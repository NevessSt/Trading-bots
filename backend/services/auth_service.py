"""Authentication service for user management."""

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import User, db
import secrets
import string
import hashlib
import hmac
from typing import Optional, Dict, Any, List
from functools import wraps

from .license_service import LicenseService, LicenseType, Permission
from .encryption_service import EncryptionService
from .logging_service import get_logger, LogCategory
from .error_handler import handle_errors, ErrorCategory


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.license_service = LicenseService()
        self.encryption_service = EncryptionService()
        self.logger = get_logger(LogCategory.SECURITY)
    
    @staticmethod
    def hash_password(password):
        """Hash a password using werkzeug's secure hash function."""
        return generate_password_hash(password)
    
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def register_user(self, username: str, email: str, password: str, 
                     license_type: LicenseType = LicenseType.DEMO, **kwargs) -> User:
        """Register a new user with license."""
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered")
        
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already taken")
        
        # Generate license for new user
        license_data = self.license_service.generate_license(
            user_email=email,
            license_type=license_type,
            duration_days=30 if license_type == LicenseType.DEMO else 365
        )
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password=password,
            license_key=license_data.license_key,
            **kwargs
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Activate license
        self.license_service.activate_license(license_data.license_key, str(user.id))
        
        self.logger.info(f"User registered: {username} with {license_type.value} license")
        return user
    
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password."""
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if not user:
            self.logger.warning(f"Authentication failed: user not found - {username_or_email}")
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            self.logger.warning(f"Authentication failed: account locked - {user.username}")
            raise ValueError("Account is temporarily locked")
        
        # Verify password
        if not user.check_password(password):
            # Increment login attempts
            user.login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                self.logger.warning(f"Account locked due to failed attempts: {user.username}")
            
            db.session.commit()
            self.logger.warning(f"Authentication failed: invalid password - {user.username}")
            return None
        
        # Validate license
        if not self.license_service.validate_license(user.license_key):
            self.logger.warning(f"Authentication failed: invalid license - {user.username}")
            raise ValueError("License is invalid or expired")
        
        # Reset login attempts on successful login
        user.login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        self.logger.info(f"User authenticated successfully: {user.username}")
        return user
    
    def create_tokens(self, user: User) -> tuple[str, str]:
        """Create access and refresh tokens for user."""
        # Get license info
        license_info = self.license_service.get_license_info(user.license_key)
        
        additional_claims = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'license_type': license_info.license_type.value if license_info else 'demo',
            'permissions': [p.value for p in license_info.features.permissions] if license_info else []
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        self.logger.info(f"Tokens created for user: {user.username}")
        return access_token, refresh_token
    
    @staticmethod
    def change_password(user, old_password, new_password):
        """Change user password."""
        if not user.check_password(old_password):
            raise ValueError("Current password is incorrect")
        
        user.set_password(new_password)
        db.session.commit()
        
        return True
    
    @staticmethod
    def reset_password(email):
        """Initiate password reset process."""
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists
            return True
        
        # Generate reset token (in real app, send via email)
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token (would typically be in database)
        # For now, just return the token
        return reset_token
    
    @staticmethod
    def verify_email(user, verification_code):
        """Verify user email address."""
        # In real implementation, would check verification code
        user.is_verified = True
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        return User.query.get(user_id)
    
    @staticmethod
    def update_user_profile(user, **kwargs):
        """Update user profile information."""
        allowed_fields = ['first_name', 'last_name', 'phone']
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def deactivate_user(user):
        """Deactivate user account."""
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True
    
    # API Key Management Methods
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def generate_api_key(self, user: User, name: str = "Default") -> Dict[str, str]:
        """Generate API key for user."""
        # Check if user has permission to create API keys
        license_info = self.license_service.get_license_info(user.license_key)
        if not license_info or Permission.API_ACCESS not in license_info.features.permissions:
            raise ValueError("User does not have permission to create API keys")
        
        # Generate API key and secret
        api_key = f"tb_{secrets.token_urlsafe(32)}"
        api_secret = secrets.token_urlsafe(64)
        
        # Hash the secret for storage
        secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
        
        # Store encrypted in user profile (would typically be separate table)
        api_keys = user.api_keys or {}
        api_keys[api_key] = {
            'name': name,
            'secret_hash': secret_hash,
            'created_at': datetime.utcnow().isoformat(),
            'last_used': None,
            'is_active': True
        }
        
        # Encrypt and store
        user.api_keys = self.encryption_service.encrypt_data(api_keys)
        db.session.commit()
        
        self.logger.info(f"API key generated for user: {user.username}")
        return {'api_key': api_key, 'api_secret': api_secret}
    
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def validate_api_key(self, api_key: str, api_secret: str) -> Optional[User]:
        """Validate API key and secret."""
        if not api_key.startswith('tb_'):
            return None
        
        # Find user with this API key
        users = User.query.all()
        for user in users:
            if not user.api_keys:
                continue
            
            try:
                api_keys = self.encryption_service.decrypt_data(user.api_keys)
                if api_key in api_keys:
                    key_info = api_keys[api_key]
                    if not key_info.get('is_active', False):
                        continue
                    
                    # Verify secret
                    secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
                    if hmac.compare_digest(key_info['secret_hash'], secret_hash):
                        # Update last used
                        key_info['last_used'] = datetime.utcnow().isoformat()
                        api_keys[api_key] = key_info
                        user.api_keys = self.encryption_service.encrypt_data(api_keys)
                        db.session.commit()
                        
                        self.logger.info(f"API key validated for user: {user.username}")
                        return user
            except Exception as e:
                self.logger.error(f"Error validating API key: {e}")
                continue
        
        self.logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        return None
    
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def revoke_api_key(self, user: User, api_key: str) -> bool:
        """Revoke an API key."""
        if not user.api_keys:
            return False
        
        try:
            api_keys = self.encryption_service.decrypt_data(user.api_keys)
            if api_key in api_keys:
                api_keys[api_key]['is_active'] = False
                api_keys[api_key]['revoked_at'] = datetime.utcnow().isoformat()
                user.api_keys = self.encryption_service.encrypt_data(api_keys)
                db.session.commit()
                
                self.logger.info(f"API key revoked for user: {user.username}")
                return True
        except Exception as e:
            self.logger.error(f"Error revoking API key: {e}")
        
        return False
    
    def list_api_keys(self, user: User) -> List[Dict[str, Any]]:
        """List user's API keys (without secrets)."""
        if not user.api_keys:
            return []
        
        try:
            api_keys = self.encryption_service.decrypt_data(user.api_keys)
            return [
                {
                    'api_key': key,
                    'name': info['name'],
                    'created_at': info['created_at'],
                    'last_used': info.get('last_used'),
                    'is_active': info.get('is_active', False)
                }
                for key, info in api_keys.items()
            ]
        except Exception as e:
            self.logger.error(f"Error listing API keys: {e}")
            return []
    
    # Permission and License Checking
    def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission."""
        license_info = self.license_service.get_license_info(user.license_key)
        if not license_info:
            return False
        return permission in license_info.features.permissions
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                if not user or not self.check_permission(user, permission):
                    raise ValueError(f"Permission required: {permission.value}")
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def require_license_type(self, min_license_type: LicenseType):
        """Decorator to require minimum license type."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                if not user:
                    raise ValueError("User not found")
                
                license_info = self.license_service.get_license_info(user.license_key)
                if not license_info or license_info.license_type.value < min_license_type.value:
                    raise ValueError(f"License upgrade required: {min_license_type.value}")
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def generate_test_user(username=None, email=None):
        """Generate a test user for development/testing."""
        if not username:
            username = f"testuser_{secrets.token_hex(4)}"
        
        if not email:
            email = f"test_{secrets.token_hex(4)}@example.com"
        
        return {
            'username': username,
            'email': email,
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }