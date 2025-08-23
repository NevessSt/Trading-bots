import hashlib
import hmac
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from models.user import User
from database import db

class LicenseManager:
    """Manages license validation and feature access control"""
    
    # License types and their features
    LICENSE_FEATURES = {
        'free': {
            'max_bots': 1,
            'live_trading': False,
            'advanced_strategies': False,
            'api_access': False,
            'priority_support': False,
            'custom_indicators': False,
            'bot_creation': True,  # Allow basic bot creation for free users
            'bot_control': True,   # Allow basic bot control for free users
            'bot_management': True, # Allow basic bot management for free users
            'api_key_management': False
        },
        'premium': {
            'max_bots': 10,
            'live_trading': True,
            'advanced_strategies': True,
            'api_access': True,
            'priority_support': True,
            'custom_indicators': True,
            'bot_creation': True,
            'bot_control': True,
            'bot_management': True,
            'api_key_management': True
        },
        'enterprise': {
            'max_bots': -1,  # Unlimited
            'live_trading': True,
            'advanced_strategies': True,
            'api_access': True,
            'priority_support': True,
            'custom_indicators': True,
            'bot_creation': True,
            'bot_control': True,
            'bot_management': True,
            'api_key_management': True
        }
    }
    
    @staticmethod
    def generate_license_key(license_type='premium', duration_days=365, user_email=None):
        """Generate a new license key"""
        try:
            # Create license data
            license_data = {
                'type': license_type,
                'created': datetime.utcnow().isoformat(),
                'expires': (datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
                'features': LicenseManager.LICENSE_FEATURES.get(license_type, {}),
                'user_email': user_email
            }
            
            # Convert to JSON string
            license_json = json.dumps(license_data, separators=(',', ':'))
            
            # Create signature
            secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
            signature = hmac.new(
                secret_key.encode(),
                license_json.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            # Combine license data and signature
            license_key = f"{license_json}|{signature}"
            
            return license_key
            
        except Exception as e:
            current_app.logger.error(f"Error generating license key: {str(e)}")
            return None
    
    @staticmethod
    def validate_license_key(license_key):
        """Validate a license key and return license data"""
        try:
            if not license_key or '|' not in license_key:
                return None, "Invalid license key format"
            
            # Split license data and signature
            license_json, signature = license_key.rsplit('|', 1)
            
            # Verify signature
            secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
            expected_signature = hmac.new(
                secret_key.encode(),
                license_json.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                return None, "Invalid license signature"
            
            # Parse license data
            license_data = json.loads(license_json)
            
            # Check expiration
            expires = datetime.fromisoformat(license_data['expires'])
            if datetime.utcnow() > expires:
                return None, "License has expired"
            
            return license_data, None
            
        except json.JSONDecodeError:
            return None, "Invalid license data format"
        except Exception as e:
            current_app.logger.error(f"Error validating license: {str(e)}")
            return None, "License validation error"
    
    @staticmethod
    def activate_license(user_id, license_key):
        """Activate a license for a user"""
        try:
            # Validate license key
            license_data, error = LicenseManager.validate_license_key(license_key)
            if error:
                return False, error
            
            # Get user
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Update user license
            user.license_key = license_key
            user.license_type = license_data['type']
            user.license_expires = datetime.fromisoformat(license_data['expires'])
            user.license_activated = datetime.utcnow()
            
            db.session.commit()
            
            return True, "License activated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error activating license: {str(e)}")
            return False, "License activation failed"
    
    @staticmethod
    def deactivate_license(user_id):
        """Deactivate a user's license"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            user.license_key = None
            user.license_type = 'free'
            user.license_expires = None
            user.license_activated = None
            
            db.session.commit()
            
            return True, "License deactivated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deactivating license: {str(e)}")
            return False, "License deactivation failed"
    
    @staticmethod
    def get_user_license_info(user_id):
        """Get license information for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            # Check if user has an active license
            if not user.license_key or not user.license_expires:
                return {
                    'type': 'free',
                    'active': False,
                    'expires': None,
                    'features': LicenseManager.LICENSE_FEATURES['free']
                }, None
            
            # Check if license is still valid
            if datetime.utcnow() > user.license_expires:
                # License expired, reset to free
                user.license_key = None
                user.license_type = 'free'
                user.license_expires = None
                user.license_activated = None
                db.session.commit()
                
                return {
                    'type': 'free',
                    'active': False,
                    'expires': None,
                    'features': LicenseManager.LICENSE_FEATURES['free']
                }, None
            
            return {
                'type': user.license_type,
                'active': True,
                'expires': user.license_expires.isoformat(),
                'activated': user.license_activated.isoformat() if user.license_activated else None,
                'features': LicenseManager.LICENSE_FEATURES.get(user.license_type, LicenseManager.LICENSE_FEATURES['free'])
            }, None
            
        except Exception as e:
            current_app.logger.error(f"Error getting license info: {str(e)}")
            return None, "Error retrieving license information"
    
    @staticmethod
    def check_feature_access(user_id, feature):
        """Check if user has access to a specific feature"""
        license_info, error = LicenseManager.get_user_license_info(user_id)
        if error or not license_info:
            return False
        
        return license_info['features'].get(feature, False)

def require_license(feature=None):
    """Decorator to require a valid license for accessing endpoints"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
                
                # Get user license info
                license_info, error = LicenseManager.get_user_license_info(user_id)
                if error:
                    return jsonify({'error': error}), 500
                
                # If no specific feature is required, just check for active license
                if feature is None:
                    if not license_info['active']:
                        return jsonify({
                            'error': 'Valid license required',
                            'license_required': True
                        }), 403
                else:
                    # Check specific feature access
                    if not license_info['features'].get(feature, False):
                        return jsonify({
                            'error': f'License does not include {feature} feature',
                            'feature_required': feature,
                            'current_license': license_info['type']
                        }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"License check error: {str(e)}")
                return jsonify({'error': 'License validation failed'}), 500
        
        return decorated_function
    return decorator