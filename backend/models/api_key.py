from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
from db import db

class APIKey(db.Model):
    """API Key model for managing exchange API keys"""
    
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exchange = db.Column(db.String(50), nullable=False)  # binance, coinbase, etc.
    key_name = db.Column(db.String(100), nullable=False)  # User-friendly name
    api_key = db.Column(db.String(255), nullable=False)  # Public API key
    api_secret_hash = db.Column(db.String(255), nullable=False)  # Hashed secret
    
    # Status and permissions
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_testnet = db.Column(db.Boolean, default=False, nullable=False)
    permissions = db.Column(db.JSON, default=lambda: ['read', 'trade'])  # read, trade, withdraw
    
    # Usage tracking
    last_used = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships are defined via backref in User model
    
    def __init__(self, user_id, exchange, key_name, api_key, api_secret, **kwargs):
        self.user_id = user_id
        self.exchange = exchange
        self.key_name = key_name
        self.api_key = api_key
        self.set_secret(api_secret)
        self.is_active = True  # Set default value
        self.usage_count = 0  # Set default value
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_secret(self, secret):
        """Hash and store the API secret"""
        self.api_secret_hash = generate_password_hash(secret)
    
    def check_secret(self, secret):
        """Verify the API secret"""
        return check_password_hash(self.api_secret_hash, secret)
    
    def update_usage(self):
        """Update usage statistics"""
        self.last_used = datetime.utcnow()
        self.usage_count += 1
    
    def is_valid(self):
        """Check if API key is valid and active"""
        return self.is_active and self.api_key and self.api_secret_hash
    
    def to_dict(self, include_secret=False):
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'exchange': self.exchange,
            'key_name': self.key_name,
            'is_active': self.is_active,
            'is_testnet': self.is_testnet,
            'permissions': self.permissions,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Never include the actual secret in serialization
        if include_secret:
            data['has_secret'] = bool(self.api_secret_hash)
        
        return data
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """Find all API keys for a user"""
        return cls.query.filter_by(user_id=user_id, is_active=True).all()
    
    @classmethod
    def find_by_id_and_user(cls, api_key_id, user_id):
        """Find API key by ID and user ID"""
        return cls.query.filter_by(id=api_key_id, user_id=user_id).first()
    
    @classmethod
    def find_by_exchange_and_user(cls, exchange, user_id):
        """Find API keys by exchange and user"""
        return cls.query.filter_by(exchange=exchange, user_id=user_id, is_active=True).all()
    
    @staticmethod
    def generate_test_key():
        """Generate a test API key for development"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    @staticmethod
    def generate_test_secret():
        """Generate a test API secret for development"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    def __repr__(self):
        return f'<APIKey {self.key_name} ({self.exchange})>'