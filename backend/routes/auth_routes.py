"""Authentication and user management routes."""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from datetime import datetime
import re

from models import User, db
from services.auth_service import AuthService
from services.license_service import LicenseType, Permission
from services.admin_service import AdminService
from middleware.security_middleware import (
    authenticate, require_permission, require_license, 
    rate_limit, validate_content_type, log_request, cors_headers
)
from services.logging_service import get_logger, LogCategory
from services.error_handler import handle_errors, ErrorCategory

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize services
auth_service = AuthService()
admin_service = AdminService()
logger = get_logger(LogCategory.API)

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


@auth_bp.route('/register', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=300)  # 5 registrations per 5 minutes
@validate_content_type()
@log_request
@cors_headers
@handle_errors(ErrorCategory.AUTHENTICATION)
def register():
    """Register a new user."""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    username = data['username'].strip()
    email = data['email'].strip().lower()
    password = data['password']
    
    # Validate input
    if len(username) < 3 or len(username) > 50:
        return jsonify({'error': 'Username must be 3-50 characters'}), 400
    
    if not EMAIL_REGEX.match(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    # Check password strength
    if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
        return jsonify({
            'error': 'Password must contain uppercase, lowercase, and numeric characters'
        }), 400
    
    try:
        # Determine license type
        license_type = LicenseType.DEMO
        if data.get('license_type') == 'premium':
            license_type = LicenseType.PREMIUM
        
        # Register user
        user = auth_service.register_user(
            username=username,
            email=email,
            password=password,
            license_type=license_type,
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip()
        )
        
        # Create tokens
        access_token, refresh_token = auth_service.create_tokens(user)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'license_type': license_type.value
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=300)  # 10 login attempts per 5 minutes
@validate_content_type()
@log_request
@cors_headers
@handle_errors(ErrorCategory.AUTHENTICATION)
def login():
    """Authenticate user and return tokens."""
    data = request.get_json()
    
    username_or_email = data.get('username_or_email', '').strip()
    password = data.get('password', '')
    
    if not username_or_email or not password:
        return jsonify({'error': 'Username/email and password are required'}), 400
    
    try:
        user = auth_service.authenticate_user(username_or_email, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create tokens
        access_token, refresh_token = auth_service.create_tokens(user)
        
        # Get license info
        license_info = auth_service.license_service.get_license_info(user.license_key)
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'license_type': license_info.license_type.value if license_info else 'demo',
                'permissions': [p.value for p in license_info.features.permissions] if license_info else []
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@rate_limit(max_requests=20, window_seconds=3600)  # 20 refreshes per hour
@log_request
@cors_headers
def refresh():
    """Refresh access token."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Validate license
        if not auth_service.license_service.validate_license(user.license_key):
            return jsonify({'error': 'License expired or invalid'}), 401
        
        # Create new access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/profile', methods=['GET'])
@authenticate
@log_request
@cors_headers
def get_profile():
    """Get current user profile."""
    user = g.current_user
    license_info = auth_service.license_service.get_license_info(user.license_key)
    api_keys = auth_service.list_api_keys(user)
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        },
        'license': {
            'type': license_info.license_type.value if license_info else 'demo',
            'status': license_info.status.value if license_info else 'inactive',
            'expires_at': license_info.expires_at.isoformat() if license_info and license_info.expires_at else None,
            'permissions': [p.value for p in license_info.features.permissions] if license_info else []
        },
        'api_keys': api_keys
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@authenticate
@validate_content_type()
@log_request
@cors_headers
def update_profile():
    """Update user profile."""
    user = g.current_user
    data = request.get_json()
    
    try:
        updated_user = auth_service.update_user_profile(
            user,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone')
        )
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': updated_user.id,
                'username': updated_user.username,
                'email': updated_user.email,
                'first_name': updated_user.first_name,
                'last_name': updated_user.last_name
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'error': 'Profile update failed'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@authenticate
@validate_content_type()
@rate_limit(max_requests=5, window_seconds=3600)  # 5 password changes per hour
@log_request
@cors_headers
def change_password():
    """Change user password."""
    user = g.current_user
    data = request.get_json()
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'error': 'Old and new passwords are required'}), 400
    
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    try:
        auth_service.change_password(user, old_password, new_password)
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({'error': 'Password change failed'}), 500


@auth_bp.route('/api-keys', methods=['POST'])
@authenticate
@require_permission(Permission.API_ACCESS)
@validate_content_type()
@rate_limit(max_requests=5, window_seconds=3600)  # 5 API key generations per hour
@log_request
@cors_headers
def generate_api_key():
    """Generate new API key."""
    user = g.current_user
    data = request.get_json()
    
    name = data.get('name', 'Default').strip()
    
    try:
        api_credentials = auth_service.generate_api_key(user, name)
        
        return jsonify({
            'message': 'API key generated successfully',
            'api_key': api_credentials['api_key'],
            'api_secret': api_credentials['api_secret'],
            'warning': 'Store the API secret securely. It will not be shown again.'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        return jsonify({'error': 'API key generation failed'}), 500


@auth_bp.route('/api-keys/<api_key>', methods=['DELETE'])
@authenticate
@require_permission(Permission.API_ACCESS)
@log_request
@cors_headers
def revoke_api_key(api_key):
    """Revoke an API key."""
    user = g.current_user
    
    try:
        success = auth_service.revoke_api_key(user, api_key)
        
        if success:
            return jsonify({
                'message': 'API key revoked successfully'
            }), 200
        else:
            return jsonify({'error': 'API key not found'}), 404
            
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        return jsonify({'error': 'API key revocation failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
@authenticate
@log_request
@cors_headers
def logout():
    """Logout user (client-side token removal)."""
    # In a more sophisticated setup, you might maintain a token blacklist
    # For now, we just return success and let the client remove the token
    
    return jsonify({
        'message': 'Logged out successfully'
    }), 200


# Admin routes
@auth_bp.route('/admin/users', methods=['GET'])
@authenticate
@require_permission(Permission.ADMIN_ACCESS)
@log_request
@cors_headers
def admin_get_users():
    """Get all users (admin only)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search')
    license_type = request.args.get('license_type')
    
    try:
        result = admin_service.get_all_users(
            page=page,
            per_page=min(per_page, 100),  # Limit to 100 per page
            search=search,
            license_type=license_type
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Admin get users error: {e}")
        return jsonify({'error': 'Failed to retrieve users'}), 500


@auth_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@authenticate
@require_permission(Permission.ADMIN_ACCESS)
@log_request
@cors_headers
def admin_get_user_details(user_id):
    """Get detailed user information (admin only)."""
    try:
        user_details = admin_service.get_user_details(user_id)
        return jsonify(user_details), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Admin get user details error: {e}")
        return jsonify({'error': 'Failed to retrieve user details'}), 500


@auth_bp.route('/admin/users/<int:user_id>/upgrade', methods=['POST'])
@authenticate
@require_permission(Permission.ADMIN_ACCESS)
@validate_content_type()
@log_request
@cors_headers
def admin_upgrade_license(user_id):
    """Upgrade user license (admin only)."""
    data = request.get_json()
    
    license_type_str = data.get('license_type')
    duration_days = data.get('duration_days', 365)
    
    if not license_type_str:
        return jsonify({'error': 'license_type is required'}), 400
    
    try:
        license_type = LicenseType(license_type_str)
        success = admin_service.upgrade_user_license(user_id, license_type, duration_days)
        
        if success:
            return jsonify({
                'message': f'License upgraded to {license_type.value}'
            }), 200
        else:
            return jsonify({'error': 'License upgrade failed'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Admin license upgrade error: {e}")
        return jsonify({'error': 'License upgrade failed'}), 500


@auth_bp.route('/admin/statistics', methods=['GET'])
@authenticate
@require_permission(Permission.ADMIN_ACCESS)
@log_request
@cors_headers
def admin_get_statistics():
    """Get system statistics (admin only)."""
    try:
        license_stats = admin_service.get_license_statistics()
        system_health = admin_service.get_system_health()
        
        return jsonify({
            'license_statistics': license_stats,
            'system_health': system_health
        }), 200
        
    except Exception as e:
        logger.error(f"Admin get statistics error: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500