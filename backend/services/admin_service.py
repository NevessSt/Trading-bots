"""Admin service for license and user management."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_, or_

from models import User, db
from .license_service import LicenseService, LicenseType, LicenseStatus, Permission
from .auth_service import AuthService
from .logging_service import get_logger, LogCategory
from .error_handler import handle_errors, ErrorCategory
from .notification_service import NotificationService


class AdminService:
    """Service for administrative operations."""
    
    def __init__(self):
        self.license_service = LicenseService()
        self.auth_service = AuthService()
        self.notification_service = NotificationService()
        self.logger = get_logger(LogCategory.SECURITY)
    
    # User Management
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def get_all_users(self, page: int = 1, per_page: int = 50, 
                     search: str = None, license_type: str = None) -> Dict[str, Any]:
        """Get paginated list of all users."""
        query = User.query
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%')
                )
            )
        
        # Apply license type filter
        if license_type:
            # This would require joining with license data
            # For now, we'll filter by role as a proxy
            if license_type == 'premium':
                query = query.filter(User.role == 'premium')
            elif license_type == 'demo':
                query = query.filter(User.role == 'user')
        
        # Get paginated results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users_data = []
        for user in pagination.items:
            license_info = self.license_service.get_license_info(user.license_key)
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'license_type': license_info.license_type.value if license_info else 'none',
                'license_status': license_info.status.value if license_info else 'inactive',
                'license_expires': license_info.expires_at.isoformat() if license_info and license_info.expires_at else None
            })
        
        return {
            'users': users_data,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def get_user_details(self, user_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        license_info = self.license_service.get_license_info(user.license_key)
        api_keys = self.auth_service.list_api_keys(user)
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'login_attempts': user.login_attempts,
            'locked_until': user.locked_until.isoformat() if user.locked_until else None,
            'license': {
                'key': user.license_key,
                'type': license_info.license_type.value if license_info else 'none',
                'status': license_info.status.value if license_info else 'inactive',
                'created_at': license_info.created_at.isoformat() if license_info else None,
                'activated_at': license_info.activated_at.isoformat() if license_info and license_info.activated_at else None,
                'expires_at': license_info.expires_at.isoformat() if license_info and license_info.expires_at else None,
                'permissions': [p.value for p in license_info.features.permissions] if license_info else []
            },
            'api_keys': api_keys,
            'statistics': self._get_user_statistics(user)
        }
    
    def _get_user_statistics(self, user: User) -> Dict[str, Any]:
        """Get user statistics (trades, performance, etc.)."""
        # This would typically query trade history, performance metrics, etc.
        # For now, return placeholder data
        return {
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'last_trade_date': None
        }
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def update_user(self, user_id: int, **kwargs) -> User:
        """Update user information."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        allowed_fields = [
            'username', 'email', 'first_name', 'last_name', 
            'role', 'is_active', 'is_verified'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        self.logger.info(f"User updated by admin: {user.username}")
        return user
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def deactivate_user(self, user_id: int, reason: str = None) -> bool:
        """Deactivate a user account."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Revoke license
        if user.license_key:
            self.license_service.revoke_license(user.license_key, reason or "Account deactivated by admin")
        
        # Send notification
        try:
            self.notification_service.send_immediate_alert(
                f"Account Deactivated",
                f"User {user.username} ({user.email}) has been deactivated. Reason: {reason or 'Admin action'}"
            )
        except Exception as e:
            self.logger.error(f"Failed to send deactivation notification: {e}")
        
        self.logger.info(f"User deactivated by admin: {user.username} - Reason: {reason}")
        return True
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def unlock_user(self, user_id: int) -> bool:
        """Unlock a locked user account."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.login_attempts = 0
        user.locked_until = None
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        self.logger.info(f"User unlocked by admin: {user.username}")
        return True
    
    # License Management
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def upgrade_user_license(self, user_id: int, new_license_type: LicenseType, 
                           duration_days: int = 365) -> bool:
        """Upgrade user's license."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Revoke old license
        if user.license_key:
            self.license_service.revoke_license(user.license_key, "Upgraded by admin")
        
        # Generate new license
        license_data = self.license_service.generate_license(
            user_email=user.email,
            license_type=new_license_type,
            duration_days=duration_days
        )
        
        # Update user
        user.license_key = license_data.license_key
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Activate new license
        self.license_service.activate_license(license_data.license_key, str(user.id))
        
        # Send notification
        try:
            self.notification_service.send_immediate_alert(
                f"License Upgraded",
                f"User {user.username} ({user.email}) license upgraded to {new_license_type.value}"
            )
        except Exception as e:
            self.logger.error(f"Failed to send upgrade notification: {e}")
        
        self.logger.info(f"License upgraded by admin: {user.username} to {new_license_type.value}")
        return True
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def extend_user_license(self, user_id: int, additional_days: int) -> bool:
        """Extend user's license duration."""
        user = User.query.get(user_id)
        if not user or not user.license_key:
            raise ValueError("User or license not found")
        
        success = self.license_service.extend_license(user.license_key, additional_days)
        
        if success:
            self.logger.info(f"License extended by admin: {user.username} by {additional_days} days")
        
        return success
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def get_license_statistics(self) -> Dict[str, Any]:
        """Get license usage statistics."""
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # Count by license type (this would need proper license tracking)
        demo_users = User.query.filter_by(role='user').count()
        premium_users = User.query.filter_by(role='premium').count()
        
        # Recent registrations
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_registrations = User.query.filter(User.created_at >= week_ago).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'demo_users': demo_users,
            'premium_users': premium_users,
            'recent_registrations': recent_registrations,
            'license_distribution': {
                'demo': demo_users,
                'basic': 0,  # Would need proper tracking
                'premium': premium_users,
                'enterprise': 0  # Would need proper tracking
            }
        }
    
    # System Management
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        return {
            'database': {
                'status': 'healthy',  # Would check actual DB connection
                'total_users': User.query.count(),
                'active_sessions': 0  # Would track active JWT tokens
            },
            'licenses': {
                'total_issued': 0,  # Would count from license storage
                'active_licenses': 0,
                'expired_licenses': 0
            },
            'security': {
                'failed_login_attempts': 0,  # Would track from logs
                'blocked_ips': 0,
                'api_key_usage': 0
            },
            'performance': {
                'avg_response_time': 0.0,
                'error_rate': 0.0,
                'uptime': '99.9%'
            }
        }
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data (tokens, sessions, etc.)."""
        cleaned_count = {
            'expired_licenses': 0,
            'old_logs': 0,
            'inactive_sessions': 0
        }
        
        # Clean up expired licenses
        # This would typically involve checking license expiration dates
        # and updating their status
        
        # Clean up old log entries (if stored in database)
        # Clean up inactive user sessions
        
        self.logger.info(f"Data cleanup completed: {cleaned_count}")
        return cleaned_count
    
    @handle_errors(ErrorCategory.SYSTEM_ERROR)
    def send_system_announcement(self, title: str, message: str, 
                               target_users: str = 'all') -> bool:
        """Send system announcement to users."""
        try:
            # This would send notifications to specified user groups
            self.notification_service.send_immediate_alert(
                f"System Announcement: {title}",
                message
            )
            
            self.logger.info(f"System announcement sent: {title} to {target_users}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send system announcement: {e}")
            return False