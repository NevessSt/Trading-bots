import os
import json
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LicenseError(Exception):
    """Custom exception for license-related errors"""
    pass

class LicenseManager:
    """
    Handles license activation, validation, and management for the trading bot system.
    Uses HMAC-SHA256 for license signature verification and local storage.
    """
    
    def __init__(self, license_file_path: str = None):
        self.license_file_path = license_file_path or os.path.join(
            os.path.dirname(__file__), '..', 'config', 'license.json'
        )
        self.secret_key = self._get_secret_key()
        
    def _get_secret_key(self) -> bytes:
        """
        Get the secret key for license signature verification.
        In production, this should be securely stored and not hardcoded.
        """
        # Use the existing encryption key or generate a new one
        key_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'encryption.key')
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Encryption key not found, using default key for license validation")
            # Fallback key - in production, this should be properly managed
            return b'trading_bot_license_key_2024'
    
    def generate_license_signature(self, license_data: Dict[str, Any]) -> str:
        """
        Generate HMAC-SHA256 signature for license data.
        This method is typically used by the license server/generator.
        """
        # Create a canonical string from license data
        canonical_data = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key,
            canonical_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_license_signature(self, license_data: Dict[str, Any], signature: str) -> bool:
        """
        Verify the HMAC-SHA256 signature of license data.
        """
        expected_signature = self.generate_license_signature(license_data)
        return hmac.compare_digest(expected_signature, signature)
    
    def activate_license(self, license_key: str, user_email: str) -> Dict[str, Any]:
        """
        Activate a license with the provided license key and user email.
        
        Args:
            license_key: The license key provided by the user
            user_email: User's email address
            
        Returns:
            Dict containing activation status and details
        """
        try:
            # Decode the license key (base64 encoded JSON)
            try:
                license_data_json = base64.b64decode(license_key).decode('utf-8')
                license_data = json.loads(license_data_json)
            except Exception as e:
                return {
                    'success': False,
                    'error': 'Invalid license key format',
                    'details': str(e)
                }
            
            # Verify required fields
            required_fields = ['license_id', 'user_email', 'expiry_date', 'features', 'signature']
            if not all(field in license_data for field in required_fields):
                return {
                    'success': False,
                    'error': 'License key missing required fields'
                }
            
            # Verify signature
            signature = license_data.pop('signature')
            if not self.verify_license_signature(license_data, signature):
                return {
                    'success': False,
                    'error': 'Invalid license signature'
                }
            
            # Verify user email matches
            if license_data['user_email'].lower() != user_email.lower():
                return {
                    'success': False,
                    'error': 'License key does not match user email'
                }
            
            # Check expiry date
            expiry_date = datetime.fromisoformat(license_data['expiry_date'])
            if datetime.now() > expiry_date:
                return {
                    'success': False,
                    'error': 'License has expired'
                }
            
            # Store license locally
            local_license = {
                'license_id': license_data['license_id'],
                'user_email': license_data['user_email'],
                'expiry_date': license_data['expiry_date'],
                'features': license_data['features'],
                'activated_at': datetime.now().isoformat(),
                'signature': signature
            }
            
            self._save_license(local_license)
            
            return {
                'success': True,
                'license_id': license_data['license_id'],
                'expiry_date': license_data['expiry_date'],
                'features': license_data['features']
            }
            
        except Exception as e:
            logger.error(f"License activation error: {str(e)}")
            return {
                'success': False,
                'error': 'License activation failed',
                'details': str(e)
            }
    
    def validate_license(self) -> Dict[str, Any]:
        """
        Validate the current license stored locally.
        
        Returns:
            Dict containing validation status and license details
        """
        try:
            license_data = self._load_license()
            if not license_data:
                return {
                    'valid': False,
                    'error': 'No license found'
                }
            
            # Verify signature
            signature = license_data.pop('signature', '')
            activated_at = license_data.pop('activated_at', '')
            
            if not self.verify_license_signature(license_data, signature):
                return {
                    'valid': False,
                    'error': 'Invalid license signature'
                }
            
            # Check expiry
            expiry_date = datetime.fromisoformat(license_data['expiry_date'])
            if datetime.now() > expiry_date:
                return {
                    'valid': False,
                    'error': 'License has expired',
                    'expiry_date': license_data['expiry_date']
                }
            
            return {
                'valid': True,
                'license_id': license_data['license_id'],
                'user_email': license_data['user_email'],
                'expiry_date': license_data['expiry_date'],
                'features': license_data['features'],
                'activated_at': activated_at,
                'days_remaining': (expiry_date - datetime.now()).days
            }
            
        except Exception as e:
            logger.error(f"License validation error: {str(e)}")
            return {
                'valid': False,
                'error': 'License validation failed',
                'details': str(e)
            }
    
    def has_feature(self, feature_name: str) -> bool:
        """
        Check if the current license includes a specific feature.
        
        Args:
            feature_name: Name of the feature to check
            
        Returns:
            True if feature is available, False otherwise
        """
        license_status = self.validate_license()
        if not license_status.get('valid', False):
            return False
        
        features = license_status.get('features', [])
        return feature_name in features
    
    def get_license_info(self) -> Dict[str, Any]:
        """
        Get current license information for display purposes.
        """
        return self.validate_license()
    
    def deactivate_license(self) -> bool:
        """
        Deactivate the current license by removing the local license file.
        
        Returns:
            True if successfully deactivated, False otherwise
        """
        try:
            if os.path.exists(self.license_file_path):
                os.remove(self.license_file_path)
            return True
        except Exception as e:
            logger.error(f"License deactivation error: {str(e)}")
            return False
    
    def _save_license(self, license_data: Dict[str, Any]) -> None:
        """
        Save license data to local file.
        """
        os.makedirs(os.path.dirname(self.license_file_path), exist_ok=True)
        with open(self.license_file_path, 'w') as f:
            json.dump(license_data, f, indent=2)
    
    def _load_license(self) -> Optional[Dict[str, Any]]:
        """
        Load license data from local file.
        """
        try:
            if not os.path.exists(self.license_file_path):
                return None
            
            with open(self.license_file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading license: {str(e)}")
            return None


# License decorator for protecting endpoints
def require_license(feature: str = None):
    """
    Decorator to require valid license for accessing endpoints.
    
    Args:
        feature: Specific feature name to check (optional)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            license_manager = LicenseManager()
            license_status = license_manager.validate_license()
            
            if not license_status.get('valid', False):
                from flask import jsonify
                return jsonify({
                    'error': 'Valid license required',
                    'details': license_status.get('error', 'Unknown error')
                }), 403
            
            if feature and not license_manager.has_feature(feature):
                from flask import jsonify
                return jsonify({
                    'error': f'Feature "{feature}" not available in current license'
                }), 403
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


# Example license generator (for testing purposes)
def generate_test_license(user_email: str, days_valid: int = 30) -> str:
    """
    Generate a test license key for development/testing purposes.
    In production, this would be handled by a secure license server.
    """
    license_manager = LicenseManager()
    
    license_data = {
        'license_id': f"TEST-{hashlib.md5(user_email.encode()).hexdigest()[:8].upper()}",
        'user_email': user_email,
        'expiry_date': (datetime.now() + timedelta(days=days_valid)).isoformat(),
        'features': ['live_trading', 'backtesting', 'real_time_data', 'advanced_strategies']
    }
    
    signature = license_manager.generate_license_signature(license_data)
    license_data['signature'] = signature
    
    # Encode as base64
    license_json = json.dumps(license_data)
    license_key = base64.b64encode(license_json.encode('utf-8')).decode('utf-8')
    
    return license_key