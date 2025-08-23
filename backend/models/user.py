from datetime import datetime, timedelta
from typing import Dict, Optional, List
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
import secrets
from db import db

class User(db.Model):
    """User model for SQLAlchemy with subscription support"""
    
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    
    # Security
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    
    # Notification settings
    notification_settings = db.Column(db.Text)  # JSON string for notification preferences
    
    # License information
    license_key = db.Column(db.Text)  # Encrypted license key
    license_type = db.Column(db.String(20), default='free', nullable=False)  # free, premium, enterprise
    license_expires = db.Column(db.DateTime)  # License expiration date
    license_activated = db.Column(db.DateTime)  # License activation date
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    bots = db.relationship('Bot', backref='user', lazy=True, cascade='all, delete-orphan')
    trades = db.relationship('Trade', backref='user', lazy=True, cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, email, username, password, **kwargs):
        # Validate inputs
        if not username or username.strip() == '':
            raise ValueError("Username cannot be empty")
        
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            raise ValueError("Invalid email format")
        
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        self.email = email
        self.username = username
        self.set_password(password)
        
        # Set default values
        self.is_active = kwargs.get('is_active', True)
        self.is_verified = kwargs.get('is_verified', False)
        self.role = kwargs.get('role', 'user')
        self.login_attempts = kwargs.get('login_attempts', 0)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        
        # Set other provided attributes
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['is_active', 'is_verified', 'role', 'login_attempts', 'created_at', 'updated_at']:
                setattr(self, key, value)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Check if account is locked"""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.login_attempts = 0
        db.session.commit()
    
    def unlock_account(self):
        """Unlock account"""
        self.locked_until = None
        self.login_attempts = 0
        db.session.commit()
    
    def increment_login_attempts(self):
        """Increment failed login attempts"""
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.lock_account()
        db.session.commit()
    
    def reset_login_attempts(self):
        """Reset login attempts on successful login"""
        self.login_attempts = 0
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def get_current_subscription(self):
        """Get user's current active subscription"""
        from .subscription import Subscription
        return Subscription.query.filter_by(
            user_id=self.id,
            is_active=True
        ).first()
    
    def has_feature(self, feature_name):
        """Check if user has access to a specific feature"""
        subscription = self.get_current_subscription()
        if not subscription:
            return False
        return subscription.has_feature(feature_name)
    
    def can_create_bot(self):
        """Check if user can create more bots"""
        subscription = self.get_current_subscription()
        if not subscription:
            return False
        
        current_bot_count = len([bot for bot in self.bots if bot.is_active])
        max_bots = subscription.get_feature_limit('max_bots')
        return current_bot_count < max_bots
    
    def get_available_strategies(self):
        """Get list of available trading strategies for user"""
        subscription = self.get_current_subscription()
        if not subscription:
            return []
        return subscription.get_available_strategies()
    
    @property
    def is_premium(self):
        """Check if user has a premium subscription"""
        subscription = self.get_current_subscription()
        if not subscription:
            return False
        return subscription.plan_type != 'free'
    
    def generate_tokens(self):
        """Generate JWT access and refresh tokens"""
        additional_claims = {
            'user_id': self.id,
            'email': self.email,
            'role': self.role,
            'subscription_type': self.get_current_subscription().plan_type if self.get_current_subscription() else 'free'
        }
        
        access_token = create_access_token(
            identity=str(self.id),
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=str(self.id))
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_premium': self.is_premium,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                'login_attempts': self.login_attempts,
                'locked_until': self.locked_until.isoformat() if self.locked_until else None
            })
        
        # Include subscription info
        subscription = self.get_current_subscription()
        if subscription:
            data['subscription'] = subscription.to_dict()
        
        return data
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_username(cls, username):
        """Find user by username"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find user by ID"""
        return cls.query.get(user_id)
    
    @classmethod
    def create_user(cls, user_data):
        """Create a new user with validation"""
        # Check if email or username already exists
        if cls.find_by_email(user_data['email']):
            raise ValueError('Email already exists')
        
        if cls.find_by_username(user_data['username']):
            raise ValueError('Username already exists')
        
        # Create user
        user = cls(
            email=user_data['email'],
            username=user_data['username'],
            password=user_data['password'],
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            phone=user_data.get('phone')
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create free subscription
        from .subscription import Subscription
        Subscription.create_free_subscription(user.id)
        
        return user
    
    @classmethod
    def authenticate(cls, email_or_username, password):
        """Authenticate user with email/username and password"""
        # Try to find by email first, then username
        user = cls.find_by_email(email_or_username)
        if not user:
            user = cls.find_by_username(email_or_username)
        
        if not user:
            return None
        
        # Check if account is locked
        if user.is_locked():
            return None
        
        # Check if account is active
        if not user.is_active:
            return None
        
        # Verify password
        if user.check_password(password):
            user.reset_login_attempts()
            return user
        else:
            user.increment_login_attempts()
            return None
    
    def __repr__(self):
        return f'<User {self.username}>'