from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
import csv
import io
from datetime import datetime, timedelta
import logging
from sqlalchemy import func, and_, or_

from models.user import User, db
from models.license import License
from services.admin_service import AdminService
from services.license_service import LicenseService
from services.demo_user_service import DemoUserService
from services.auth_service import AuthService
from utils.decorators import handle_errors
from utils.error_categories import ErrorCategory
from utils.permissions import Permission, require_permission

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to ensure user has admin permissions"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({
                'error': 'Admin access required',
                'message': 'You do not have permission to access this resource'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

# User Management Routes
@admin_bp.route('/users', methods=['GET'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def get_users():
    """Get all users with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', 'all')
        license_type = request.args.get('license_type', 'all')
        
        query = User.query
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f'%{search}%'),
                    User.name.ilike(f'%{search}%')
                )
            )
        
        # Apply status filter
        if status != 'all':
            if status == 'active':
                query = query.filter(User.is_active == True)
            elif status == 'inactive':
                query = query.filter(User.is_active == False)
            elif status == 'demo':
                query = query.filter(User.is_demo == True)
            elif status == 'premium':
                query = query.filter(and_(User.is_demo == False, User.is_active == True))
        
        # Apply license type filter
        if license_type != 'all':
            query = query.filter(User.license_type == license_type)
        
        # Paginate results
        users_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = []
        for user in users_pagination.items:
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'is_active': user.is_active,
                'is_demo': user.is_demo,
                'is_admin': user.is_admin,
                'license_type': user.license_type,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'demo_expires_at': user.demo_expires_at.isoformat() if user.demo_expires_at else None,
                'failed_login_attempts': user.failed_login_attempts,
                'account_locked_until': user.account_locked_until.isoformat() if user.account_locked_until else None
            }
            users_data.append(user_data)
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users_pagination.total,
                'pages': users_pagination.pages,
                'has_next': users_pagination.has_next,
                'has_prev': users_pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def get_user(user_id):
    """Get specific user details"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user's licenses
        licenses = License.query.filter_by(user_id=user_id).all()
        licenses_data = []
        for license in licenses:
            licenses_data.append({
                'id': license.id,
                'license_type': license.license_type,
                'is_active': license.is_active,
                'created_at': license.created_at.isoformat() if license.created_at else None,
                'expires_at': license.expires_at.isoformat() if license.expires_at else None
            })
        
        user_data = {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'is_active': user.is_active,
            'is_demo': user.is_demo,
            'is_admin': user.is_admin,
            'license_type': user.license_type,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'demo_expires_at': user.demo_expires_at.isoformat() if user.demo_expires_at else None,
            'failed_login_attempts': user.failed_login_attempts,
            'account_locked_until': user.account_locked_until.isoformat() if user.account_locked_until else None,
            'licenses': licenses_data
        }
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user'}), 500

@admin_bp.route('/users', methods=['POST'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Create user using AuthService
        auth_service = AuthService()
        result = auth_service.register_user(
            email=data['email'],
            password=data['password'],
            name=data.get('name'),
            is_demo=data.get('is_demo', False),
            license_type=data.get('license_type', 'basic')
        )
        
        if result['success']:
            return jsonify({
                'message': 'User created successfully',
                'user': result['user']
            }), 201
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def update_user(user_id):
    """Update user details"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        if 'license_type' in data:
            user.license_type = data['license_type']
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'license_type': user.license_type
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deleting the current admin user
        current_user_id = get_jwt_identity()
        if user_id == current_user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Delete associated licenses first
        License.query.filter_by(user_id=user_id).delete()
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500

@admin_bp.route('/users/<int:user_id>/activate', methods=['POST'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def activate_user(user_id):
    """Activate a user account"""
    try:
        admin_service = AdminService()
        result = admin_service.activate_user(user_id)
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Error activating user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to activate user'}), 500

@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def deactivate_user(user_id):
    """Deactivate a user account"""
    try:
        admin_service = AdminService()
        result = admin_service.deactivate_user(user_id)
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to deactivate user'}), 500

@admin_bp.route('/users/<int:user_id>/upgrade', methods=['POST'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def upgrade_user_license(user_id):
    """Upgrade user license"""
    try:
        data = request.get_json()
        license_type = data.get('license_type', 'professional')
        duration_days = data.get('duration_days', 30)
        
        admin_service = AdminService()
        result = admin_service.upgrade_user_license(user_id, license_type, duration_days)
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Error upgrading user {user_id} license: {str(e)}")
        return jsonify({'error': 'Failed to upgrade user license'}), 500

@admin_bp.route('/users/<int:user_id>/extend', methods=['POST'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def extend_user_license(user_id):
    """Extend user license"""
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        admin_service = AdminService()
        result = admin_service.extend_user_license(user_id, days)
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Error extending user {user_id} license: {str(e)}")
        return jsonify({'error': 'Failed to extend user license'}), 500

# License Management Routes
@admin_bp.route('/licenses', methods=['GET'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def get_licenses():
    """Get all licenses with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', 'all')
        license_type = request.args.get('license_type', 'all')
        
        query = db.session.query(License, User).join(User, License.user_id == User.id)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f'%{search}%'),
                    License.license_type.ilike(f'%{search}%')
                )
            )
        
        # Apply status filter
        if status != 'all':
            if status == 'active':
                query = query.filter(License.is_active == True)
            elif status == 'inactive':
                query = query.filter(License.is_active == False)
            elif status == 'expired':
                query = query.filter(License.expires_at < datetime.utcnow())
        
        # Apply license type filter
        if license_type != 'all':
            query = query.filter(License.license_type == license_type)
        
        # Paginate results
        licenses_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        licenses_data = []
        for license, user in licenses_pagination.items:
            license_data = {
                'id': license.id,
                'user_id': user.id,
                'user_email': user.email,
                'license_type': license.license_type,
                'is_active': license.is_active,
                'created_at': license.created_at.isoformat() if license.created_at else None,
                'expires_at': license.expires_at.isoformat() if license.expires_at else None,
                'is_expired': license.expires_at < datetime.utcnow() if license.expires_at else False
            }
            licenses_data.append(license_data)
        
        return jsonify({
            'licenses': licenses_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': licenses_pagination.total,
                'pages': licenses_pagination.pages,
                'has_next': licenses_pagination.has_next,
                'has_prev': licenses_pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting licenses: {str(e)}")
        return jsonify({'error': 'Failed to retrieve licenses'}), 500

# Statistics Routes
@admin_bp.route('/stats', methods=['GET'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def get_stats():
    """Get system statistics"""
    try:
        # User statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        demo_users = User.query.filter_by(is_demo=True).count()
        premium_users = User.query.filter(and_(User.is_demo == False, User.is_active == True)).count()
        
        # License statistics
        total_licenses = License.query.count()
        active_licenses = License.query.filter_by(is_active=True).count()
        expired_licenses = License.query.filter(License.expires_at < datetime.utcnow()).count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()
        new_licenses_30d = License.query.filter(License.created_at >= thirty_days_ago).count()
        
        # Demo user statistics
        demo_service = DemoUserService()
        demo_stats = demo_service.get_demo_user_stats()
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'demo_users': demo_users,
            'premium_users': premium_users,
            'total_licenses': total_licenses,
            'active_licenses': active_licenses,
            'expired_licenses': expired_licenses,
            'new_users_30d': new_users_30d,
            'new_licenses_30d': new_licenses_30d,
            'monthly_revenue': 0,  # TODO: Implement revenue tracking
            'demo_conversion_rate': demo_stats.get('conversion_rate', 0),
            'average_demo_duration': demo_stats.get('average_duration_days', 0)
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

# Export Routes
@admin_bp.route('/export/users', methods=['GET'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def export_users():
    """Export users data as CSV"""
    try:
        users = User.query.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Email', 'Name', 'Active', 'Demo', 'Admin', 
            'License Type', 'Created At', 'Last Login', 'Demo Expires At'
        ])
        
        # Write data
        for user in users:
            writer.writerow([
                user.id,
                user.email,
                user.name or '',
                user.is_active,
                user.is_demo,
                user.is_admin,
                user.license_type or '',
                user.created_at.isoformat() if user.created_at else '',
                user.last_login.isoformat() if user.last_login else '',
                user.demo_expires_at.isoformat() if user.demo_expires_at else ''
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting users: {str(e)}")
        return jsonify({'error': 'Failed to export users'}), 500

@admin_bp.route('/export/licenses', methods=['GET'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def export_licenses():
    """Export licenses data as CSV"""
    try:
        licenses = db.session.query(License, User).join(User, License.user_id == User.id).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'License ID', 'User Email', 'License Type', 'Active', 
            'Created At', 'Expires At', 'Is Expired'
        ])
        
        # Write data
        for license, user in licenses:
            writer.writerow([
                license.id,
                user.email,
                license.license_type,
                license.is_active,
                license.created_at.isoformat() if license.created_at else '',
                license.expires_at.isoformat() if license.expires_at else '',
                license.expires_at < datetime.utcnow() if license.expires_at else False
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'licenses_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting licenses: {str(e)}")
        return jsonify({'error': 'Failed to export licenses'}), 500

# Demo User Management Routes
@admin_bp.route('/demo-users', methods=['GET'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def get_demo_users():
    """Get all demo users"""
    try:
        demo_service = DemoUserService()
        demo_users = demo_service.get_all_demo_users()
        
        return jsonify({'demo_users': demo_users}), 200
        
    except Exception as e:
        logger.error(f"Error getting demo users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve demo users'}), 500

@admin_bp.route('/demo-users/<int:user_id>/extend', methods=['POST'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def extend_demo_user(user_id):
    """Extend demo user expiration"""
    try:
        data = request.get_json()
        days = data.get('days', 7)
        
        demo_service = DemoUserService()
        result = demo_service.extend_demo_user(user_id, days)
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Error extending demo user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to extend demo user'}), 500

@admin_bp.route('/demo-users/cleanup', methods=['POST'])
@admin_required
@handle_errors(ErrorCategory.API_ERROR)
def cleanup_expired_demo_users():
    """Manually trigger cleanup of expired demo users"""
    try:
        demo_service = DemoUserService()
        result = demo_service.cleanup_expired_demo_users()
        
        return jsonify({
            'message': f'Cleanup completed. {result["expired_count"]} demo users processed.',
            'expired_count': result['expired_count']
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up demo users: {str(e)}")
        return jsonify({'error': 'Failed to cleanup demo users'}), 500