from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
import traceback

from services.license_service import LicenseService, LicenseType, Permission
from services.auth_service import AuthService
from services.admin_service import AdminService
from services.logging_service import get_logger, LogCategory
from services.error_handler import handle_errors, ErrorCategory
from middleware.security_middleware import require_permission, require_license_type
from models.user import User
from db import db

license_bp = Blueprint('license', __name__, url_prefix='/api/license')
logger = get_logger(LogCategory.API)

# Initialize services
license_service = LicenseService()
auth_service = AuthService()
admin_service = AdminService()

@license_bp.route('/activate', methods=['POST'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def activate_license():
    """Activate a license key for the current user"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        
        if not license_key:
            return jsonify({'error': 'License key is required'}), 400
        
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Activate the license
        success = license_service.activate_license(license_key, user_id)
        
        if success:
            # Refresh user data
            db.session.refresh(user)
            license_info = user.get_license_info()
            
            logger.info(f"License activated for user {user_id}: {license_key[:8]}...")
            return jsonify({
                'message': 'License activated successfully',
                'license': license_info
            }), 200
        else:
            logger.warning(f"Failed to activate license for user {user_id}: {license_key[:8]}...")
            return jsonify({'error': 'Invalid or expired license key'}), 400
            
    except Exception as e:
        logger.error(f"Error activating license: {e}")
        return jsonify({'error': 'Failed to activate license'}), 500

@license_bp.route('/info', methods=['GET'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def get_license_info():
    """Get current user's license information"""
    try:
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        license_info = user.get_license_info()
        
        # Add usage statistics
        license_info.update({
            'current_bots': len([bot for bot in user.bots if bot.is_active]),
            'current_api_keys': len([key for key in user.api_keys if key.is_active]),
            'can_create_bot': user.can_create_bot(),
            'can_create_api_key': user.can_create_api_key()
        })
        
        logger.info(f"License info retrieved for user {user_id}")
        return jsonify(license_info), 200
        
    except Exception as e:
        logger.error(f"Error getting license info: {e}")
        return jsonify({'error': 'Failed to get license information'}), 500

@license_bp.route('/validate', methods=['POST'])
@jwt_required()
@handle_errors(ErrorCategory.API_ERROR)
def validate_license():
    """Validate a license key without activating it"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        
        if not license_key:
            return jsonify({'error': 'License key is required'}), 400
        
        # Validate the license
        license_data = license_service.validate_license(license_key)
        
        if license_data:
            logger.info(f"License validated: {license_key[:8]}...")
            return jsonify({
                'valid': True,
                'license_type': license_data.license_type.value,
                'expires': license_data.expires_at.isoformat() if license_data.expires_at else None,
                'features': license_data.features.__dict__
            }), 200
        else:
            logger.warning(f"Invalid license key: {license_key[:8]}...")
            return jsonify({'valid': False}), 200
            
    except Exception as e:
        logger.error(f"Error validating license: {e}")
        return jsonify({'error': 'Failed to validate license'}), 500

@license_bp.route('/upgrade', methods=['POST'])
@jwt_required()
@require_permission(Permission.ADMIN_LICENSES)
@handle_errors(ErrorCategory.API_ERROR)
def upgrade_license():
    """Upgrade user's license"""
    try:
        data = request.get_json()
        new_license_type = data.get('license_type')
        duration_days = data.get('duration_days', 365)
        
        if not new_license_type:
            return jsonify({'error': 'License type is required'}), 400
        
        try:
            license_type = LicenseType(new_license_type)
        except ValueError:
            return jsonify({'error': 'Invalid license type'}), 400
        
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate and activate new license
        new_license = license_service.generate_license(
            license_type=license_type,
            duration_days=duration_days
        )
        
        success = license_service.activate_license(new_license.license_key, user_id)
        
        if success:
            db.session.refresh(user)
            license_info = user.get_license_info()
            
            logger.info(f"License upgraded for user {user_id} to {license_type.value}")
            return jsonify({
                'message': 'License upgraded successfully',
                'license': license_info
            }), 200
        else:
            logger.error(f"Failed to upgrade license for user {user_id}")
            return jsonify({'error': 'Failed to upgrade license'}), 500
            
    except Exception as e:
        logger.error(f"Error upgrading license: {e}")
        return jsonify({'error': 'Failed to upgrade license'}), 500

@license_bp.route('/extend', methods=['POST'])
@jwt_required()
@require_permission(Permission.ADMIN_LICENSES)
@handle_errors(ErrorCategory.API_ERROR)
def extend_license():
    """Extend user's license duration"""
    try:
        data = request.get_json()
        extension_days = data.get('extension_days', 30)
        
        if extension_days <= 0:
            return jsonify({'error': 'Extension days must be positive'}), 400
        
        user_id = int(get_jwt_identity())
        user = User.find_by_id(user_id)
        
        if not user or not user.license_key:
            return jsonify({'error': 'No active license found'}), 404
        
        # Extend the license
        success = license_service.extend_license(user.license_key, extension_days)
        
        if success:
            db.session.refresh(user)
            license_info = user.get_license_info()
            
            logger.info(f"License extended for user {user_id} by {extension_days} days")
            return jsonify({
                'message': f'License extended by {extension_days} days',
                'license': license_info
            }), 200
        else:
            logger.error(f"Failed to extend license for user {user_id}")
            return jsonify({'error': 'Failed to extend license'}), 500
            
    except Exception as e:
        logger.error(f"Error extending license: {e}")
        return jsonify({'error': 'Failed to extend license'}), 500

# Admin routes
@license_bp.route('/admin/generate', methods=['POST'])
@jwt_required()
@require_license_type(LicenseType.ENTERPRISE)
@require_permission(Permission.ADMIN_LICENSES)
@handle_errors(ErrorCategory.API_ERROR)
def admin_generate_license():
    """Generate a new license (admin only)"""
    try:
        data = request.get_json()
        license_type = data.get('license_type', 'premium')
        duration_days = data.get('duration_days', 365)
        max_activations = data.get('max_activations', 1)
        
        try:
            license_type_enum = LicenseType(license_type)
        except ValueError:
            return jsonify({'error': 'Invalid license type'}), 400
        
        # Generate license
        license_data = license_service.generate_license(
            license_type=license_type_enum,
            duration_days=duration_days,
            max_activations=max_activations
        )
        
        admin_id = int(get_jwt_identity())
        logger.info(f"License generated by admin {admin_id}: {license_data.license_key[:8]}...")
        
        return jsonify({
            'license_key': license_data.license_key,
            'license_type': license_data.license_type.value,
            'expires_at': license_data.expires_at.isoformat() if license_data.expires_at else None,
            'max_activations': license_data.max_activations,
            'features': license_data.features.__dict__
        }), 201
        
    except Exception as e:
        logger.error(f"Error generating license: {e}")
        return jsonify({'error': 'Failed to generate license'}), 500

@license_bp.route('/admin/revoke', methods=['POST'])
@jwt_required()
@require_license_type(LicenseType.ENTERPRISE)
@require_permission(Permission.ADMIN_LICENSES)
@handle_errors(ErrorCategory.API_ERROR)
def admin_revoke_license():
    """Revoke a license (admin only)"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        reason = data.get('reason', 'Admin revocation')
        
        if not license_key:
            return jsonify({'error': 'License key is required'}), 400
        
        # Revoke the license
        success = license_service.revoke_license(license_key, reason)
        
        if success:
            admin_id = int(get_jwt_identity())
            logger.info(f"License revoked by admin {admin_id}: {license_key[:8]}... - {reason}")
            return jsonify({'message': 'License revoked successfully'}), 200
        else:
            return jsonify({'error': 'License not found or already revoked'}), 404
            
    except Exception as e:
        logger.error(f"Error revoking license: {e}")
        return jsonify({'error': 'Failed to revoke license'}), 500

@license_bp.route('/admin/statistics', methods=['GET'])
@jwt_required()
@require_license_type(LicenseType.ENTERPRISE)
@require_permission(Permission.DATA_ANALYTICS)
@handle_errors(ErrorCategory.API_ERROR)
def admin_license_statistics():
    """Get license statistics (admin only)"""
    try:
        stats = admin_service.get_license_statistics()
        
        admin_id = int(get_jwt_identity())
        logger.info(f"License statistics requested by admin {admin_id}")
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting license statistics: {e}")
        return jsonify({'error': 'Failed to get license statistics'}), 500

@license_bp.route('/admin/users/<int:user_id>/upgrade', methods=['POST'])
@jwt_required()
@require_license_type(LicenseType.ENTERPRISE)
@require_permission(Permission.ADMIN_USERS)
@handle_errors(ErrorCategory.API_ERROR)
def admin_upgrade_user_license(user_id):
    """Upgrade a user's license (admin only)"""
    try:
        data = request.get_json()
        license_type = data.get('license_type')
        duration_days = data.get('duration_days', 365)
        
        if not license_type:
            return jsonify({'error': 'License type is required'}), 400
        
        try:
            license_type_enum = LicenseType(license_type)
        except ValueError:
            return jsonify({'error': 'Invalid license type'}), 400
        
        # Upgrade user license
        success = admin_service.upgrade_user_license(user_id, license_type_enum, duration_days)
        
        if success:
            admin_id = int(get_jwt_identity())
            logger.info(f"User {user_id} license upgraded by admin {admin_id} to {license_type}")
            return jsonify({'message': 'User license upgraded successfully'}), 200
        else:
            return jsonify({'error': 'Failed to upgrade user license'}), 500
            
    except Exception as e:
        logger.error(f"Error upgrading user license: {e}")
        return jsonify({'error': 'Failed to upgrade user license'}), 500

@license_bp.errorhandler(Exception)
def handle_license_error(error):
    """Handle license-related errors"""
    logger.error(f"License API error: {error}")
    logger.error(traceback.format_exc())
    return jsonify({'error': 'Internal server error'}), 500