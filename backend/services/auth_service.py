"""Authentication service for user management."""

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import User, db
import secrets
import string


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def hash_password(password):
        """Hash a password using werkzeug's secure hash function."""
        return generate_password_hash(password)
    
    @staticmethod
    def register_user(username, email, password, **kwargs):
        """Register a new user."""
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered")
        
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already taken")
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password=password,
            **kwargs
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def authenticate_user(username_or_email, password):
        """Authenticate user with username/email and password."""
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise ValueError("Account is temporarily locked")
        
        # Verify password
        if not user.check_password(password):
            # Increment login attempts
            user.login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            db.session.commit()
            return None
        
        # Reset login attempts on successful login
        user.login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def create_tokens(user):
        """Create access and refresh tokens for user."""
        additional_claims = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
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
        
        return user
    
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