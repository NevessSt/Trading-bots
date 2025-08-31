from datetime import datetime, timedelta
from typing import Dict, Optional, List
from db import db
import json

class License(db.Model):
    """License model for SQLAlchemy"""
    
    __tablename__ = 'licenses'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    license_type = db.Column(db.String(50), default='free', nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    activated_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    last_used = db.Column(db.DateTime)
    
    # Activation tracking
    machine_id = db.Column(db.String(255))
    activation_count = db.Column(db.Integer, default=0)
    max_activations = db.Column(db.Integer, default=1)
    
    # Features and metadata
    features = db.Column(db.JSON)  # JSON object for license features
    metadata = db.Column(db.JSON)  # Additional metadata
    usage_stats = db.Column(db.JSON)  # Usage statistics
    
    # Relationships
    user = db.relationship('User', backref='licenses')
    
    def __init__(self, license_key, user_id, license_type='free', **kwargs):
        self.license_key = license_key
        self.user_id = user_id
        self.license_type = license_type
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.max_activations = kwargs.get('max_activations', 1)
        self.features = kwargs.get('features', self._get_default_features())
        self.metadata = kwargs.get('metadata', {})
        self.usage_stats = kwargs.get('usage_stats', {})
    
    def _get_default_features(self):
        """Get default features based on license type"""
        features_map = {
            'free': {
                'max_bots': 1,
                'live_trading': False,
                'advanced_strategies': False,
                'api_access': False,
                'priority_support': False,
                'custom_indicators': False
            },
            'premium': {
                'max_bots': 10,
                'live_trading': True,
                'advanced_strategies': True,
                'api_access': True,
                'priority_support': True,
                'custom_indicators': True
            },
            'enterprise': {
                'max_bots': -1,  # Unlimited
                'live_trading': True,
                'advanced_strategies': True,
                'api_access': True,
                'priority_support': True,
                'custom_indicators': True
            }
        }
        return features_map.get(self.license_type, features_map['free'])
    
    def is_valid(self):
        """Check if license is valid"""
        if self.status != 'active':
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def is_expired(self):
        """Check if license is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def activate(self, machine_id=None):
        """Activate the license"""
        if self.activation_count >= self.max_activations:
            raise ValueError("Maximum activations reached")
        
        self.activated_at = datetime.utcnow()
        self.last_used = datetime.utcnow()
        self.activation_count += 1
        
        if machine_id:
            self.machine_id = machine_id
    
    def deactivate(self):
        """Deactivate the license"""
        self.status = 'inactive'
    
    def update_usage(self, stats):
        """Update usage statistics"""
        if not self.usage_stats:
            self.usage_stats = {}
        
        self.usage_stats.update(stats)
        self.last_used = datetime.utcnow()
    
    def to_dict(self):
        """Convert license to dictionary"""
        return {
            'id': self.id,
            'license_key': self.license_key,
            'user_id': self.user_id,
            'license_type': self.license_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'machine_id': self.machine_id,
            'activation_count': self.activation_count,
            'max_activations': self.max_activations,
            'features': self.features,
            'metadata': self.metadata,
            'usage_stats': self.usage_stats,
            'is_valid': self.is_valid(),
            'is_expired': self.is_expired()
        }
    
    def __repr__(self):
        return f'<License {self.license_key} - {self.license_type} - {self.status}>'