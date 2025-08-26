from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
import json
from db import db
from utils.encryption import get_encryption_manager, EncryptionError
import logging

logger = logging.getLogger(__name__)

class APIKey(db.Model):
    """API Key model for managing exchange API keys"""
    
    __tablename__ = 'api_keys'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exchange = db.Column(db.String(50), nullable=False)  # binance, coinbase, etc.
    key_name = db.Column(db.String(100), nullable=False)  # User-friendly name
    api_key = db.Column(db.String(255), nullable=False)  # Public API key (not encrypted)
    api_secret_encrypted = db.Column(db.Text, nullable=False)  # Encrypted secret
    passphrase_encrypted = db.Column(db.Text)  # Encrypted passphrase (for some exchanges)
    
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
    
    def __init__(self, user_id, exchange, key_name, api_key, api_secret, passphrase=None, **kwargs):
        self.user_id = user_id
        self.exchange = exchange
        self.key_name = key_name
        self.api_key = api_key
        self.set_credentials(api_secret, passphrase)
        self.is_active = True  # Set default value
        self.usage_count = 0  # Set default value
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_credentials(self, api_secret, passphrase=None):
        """Encrypt and store the API credentials"""
        try:
            encryption_manager = get_encryption_manager()
            self.api_secret_encrypted = encryption_manager.encrypt(api_secret)
            
            if passphrase:
                self.passphrase_encrypted = encryption_manager.encrypt(passphrase)
            else:
                self.passphrase_encrypted = None
                
        except EncryptionError as e:
            logger.error(f"Failed to encrypt API credentials: {str(e)}")
            raise ValueError(f"Failed to encrypt API credentials: {str(e)}")
    
    def get_credentials(self):
        """Decrypt and return the API credentials"""
        try:
            encryption_manager = get_encryption_manager()
            
            credentials = {
                'api_key': self.api_key,
                'api_secret': encryption_manager.decrypt(self.api_secret_encrypted)
            }
            
            if self.passphrase_encrypted:
                credentials['passphrase'] = encryption_manager.decrypt(self.passphrase_encrypted)
            
            return credentials
            
        except EncryptionError as e:
            logger.error(f"Failed to decrypt API credentials: {str(e)}")
            raise ValueError(f"Failed to decrypt API credentials: {str(e)}")
    
    def verify_secret(self, secret):
        """Verify the API secret by decrypting and comparing"""
        try:
            credentials = self.get_credentials()
            return credentials['api_secret'] == secret
        except Exception:
            return False
    
    def update_credentials(self, api_secret=None, passphrase=None):
        """Update encrypted credentials"""
        try:
            if api_secret is not None:
                encryption_manager = get_encryption_manager()
                self.api_secret_encrypted = encryption_manager.encrypt(api_secret)
            
            if passphrase is not None:
                encryption_manager = get_encryption_manager()
                if passphrase:
                    self.passphrase_encrypted = encryption_manager.encrypt(passphrase)
                else:
                    self.passphrase_encrypted = None
            
            self.updated_at = datetime.utcnow()
            
        except EncryptionError as e:
            logger.error(f"Failed to update API credentials: {str(e)}")
            raise ValueError(f"Failed to update API credentials: {str(e)}")
    
    def update_usage(self):
        """Update usage statistics"""
        self.last_used = datetime.utcnow()
        self.usage_count += 1
    
    def is_valid(self):
        """Check if API key is valid and active"""
        return bool(self.is_active and self.api_key and self.api_secret_encrypted)
    
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
            data['has_secret'] = bool(self.api_secret_encrypted)
            data['has_passphrase'] = bool(self.passphrase_encrypted)
        
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
    
    # Test key generation methods removed for production security
    
    def __repr__(self):
        return f'<APIKey {self.key_name} ({self.exchange})>'