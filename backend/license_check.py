import hashlib
import json
import os
import platform
import requests
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from typing import Dict, Optional, Tuple
import logging

# Import the standard machine ID generator
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools.machine_id import generate_machine_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LicenseValidator:
    """License validation system for the trading bot application."""
    
    def __init__(self, license_file_path: str = None):
        self.license_file_path = license_file_path or os.path.join(
            os.path.dirname(__file__), '..', 'license_key.bin'
        )
        self.encryption_key_path = os.path.join(
            os.path.dirname(__file__), 'config', 'encryption.key'
        )
        self.revocation_cache_path = os.path.join(
            os.path.dirname(__file__), 'config', 'revocation_cache.json'
        )
        self.license_server_url = os.environ.get('LICENSE_SERVER_URL', 'https://license.tradingbot.pro')
        self.enable_remote_check = os.environ.get('ENABLE_REMOTE_LICENSE_CHECK', 'true').lower() == 'true'
        self.cache_timeout = int(os.environ.get('LICENSE_CACHE_TIMEOUT', '3600'))  # 1 hour default
    
    def get_machine_id(self) -> str:
        """Generate a unique machine identifier using the standard function."""
        return generate_machine_id()
    
    def load_encryption_key(self) -> bytes:
        """Load or generate encryption key."""
        try:
            if os.path.exists(self.encryption_key_path):
                with open(self.encryption_key_path, 'rb') as f:
                    return f.read()
            else:
                # Generate new key if not exists
                key = Fernet.generate_key()
                os.makedirs(os.path.dirname(self.encryption_key_path), exist_ok=True)
                with open(self.encryption_key_path, 'wb') as f:
                    f.write(key)
                return key
        except Exception as e:
            raise Exception(f"Failed to load encryption key: {str(e)}")
    
    def decrypt_license(self, encrypted_data: bytes) -> Dict:
        """Decrypt license data."""
        try:
            key = self.load_encryption_key()
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            raise Exception(f"Failed to decrypt license: {str(e)}")
    
    def validate_license(self) -> Tuple[bool, str, Optional[Dict]]:
        """Validate the license file with remote revocation checking.
        
        Returns:
            Tuple[bool, str, Optional[Dict]]: (is_valid, message, license_data)
        """
        try:
            # Check if license file exists
            if not os.path.exists(self.license_file_path):
                return False, "License file not found", None
            
            # Read and decrypt license
            with open(self.license_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            license_data = self.decrypt_license(encrypted_data)
            
            # Validate license structure
            required_fields = ['machine_id', 'expiry_date', 'license_type', 'features']
            for field in required_fields:
                if field not in license_data:
                    return False, f"Invalid license format: missing {field}", None
            
            # Check machine ID
            current_machine_id = self.get_machine_id()
            if license_data['machine_id'] != current_machine_id:
                return False, "License not valid for this machine", None
            
            # Check expiry date
            expiry_date = datetime.fromisoformat(license_data['expiry_date'])
            if datetime.now() > expiry_date:
                return False, "License has expired", None
            
            # Check license type
            valid_types = ['trial', 'standard', 'premium', 'enterprise']
            if license_data['license_type'] not in valid_types:
                return False, "Invalid license type", None
            
            # Check local revocation cache first
            if self._is_license_revoked_locally(license_data):
                return False, "License has been revoked", None
            
            # Perform remote validation if enabled
            if self.enable_remote_check:
                remote_valid, remote_message = self._validate_license_remote(license_data)
                if not remote_valid:
                    return False, remote_message, None
            
            return True, "License is valid", license_data
            
        except Exception as e:
            return False, f"License validation error: {str(e)}", None
    
    def get_license_info(self) -> Dict:
        """Get license information for display."""
        is_valid, message, license_data = self.validate_license()
        
        if not is_valid:
            return {
                'valid': False,
                'message': message,
                'license_type': 'None',
                'expiry_date': 'N/A',
                'features': []
            }
        
        return {
            'valid': True,
            'message': message,
            'license_type': license_data['license_type'],
            'expiry_date': license_data['expiry_date'],
            'features': license_data['features'],
            'days_remaining': (datetime.fromisoformat(license_data['expiry_date']) - datetime.now()).days
        }
    
    def check_feature_access(self, feature: str) -> bool:
        """Check if a specific feature is available in the license."""
        is_valid, _, license_data = self.validate_license()
        
        if not is_valid or not license_data:
            return False
        
        return feature in license_data.get('features', [])
    
    def get_trial_license_data(self, days: int = 30) -> Dict:
        """Generate trial license data."""
        expiry_date = datetime.now() + timedelta(days=days)
        
        return {
            'machine_id': self.get_machine_id(),
            'expiry_date': expiry_date.isoformat(),
            'license_type': 'trial',
            'features': [
                'basic_trading',
                'risk_management',
                'market_data',
                'single_exchange'
            ],
            'generated_at': datetime.now().isoformat(),
            'trial_days': days
        }
    
    def _is_license_revoked_locally(self, license_data: Dict) -> bool:
        """Check if license is revoked using local cache."""
        try:
            if not os.path.exists(self.revocation_cache_path):
                return False
            
            with open(self.revocation_cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache expiry
            cache_time = datetime.fromisoformat(cache_data.get('updated_at', '1970-01-01'))
            if (datetime.now() - cache_time).total_seconds() > self.cache_timeout:
                logger.info("Revocation cache expired, will check remotely")
                return False
            
            # Generate license hash for comparison
            license_hash = hashlib.sha256(
                json.dumps(license_data, sort_keys=True).encode()
            ).hexdigest()
            
            revoked_hashes = cache_data.get('revoked_licenses', [])
            return license_hash in revoked_hashes
            
        except Exception as e:
            logger.error(f"Error checking local revocation cache: {e}")
            return False
    
    def _validate_license_remote(self, license_data: Dict) -> Tuple[bool, str]:
        """Validate license against remote server."""
        try:
            # Generate license key from data (simplified)
            license_key = hashlib.sha256(
                json.dumps(license_data, sort_keys=True).encode()
            ).hexdigest()
            
            payload = {
                'license_key': license_key,
                'machine_id': license_data['machine_id']
            }
            
            # Make request to license server
            response = requests.post(
                f"{self.license_server_url}/validate",
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('valid'):
                    # Update local cache with revocation list
                    self._update_revocation_cache()
                    return True, "License validated remotely"
                else:
                    return False, result.get('message', 'License validation failed')
            else:
                logger.warning(f"Remote validation failed with status {response.status_code}")
                # Fall back to local validation if remote fails
                return True, "Remote validation unavailable, using local validation"
                
        except requests.exceptions.Timeout:
            logger.warning("Remote license validation timed out")
            return True, "Remote validation timed out, using local validation"
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to license server")
            return True, "Remote validation unavailable, using local validation"
        except Exception as e:
            logger.error(f"Remote validation error: {e}")
            return True, "Remote validation error, using local validation"
    
    def _update_revocation_cache(self):
        """Update local revocation cache from remote server."""
        try:
            response = requests.get(
                f"{self.license_server_url}/revocation-list",
                timeout=10
            )
            
            if response.status_code == 200:
                revocation_data = response.json()
                
                # Create cache directory if it doesn't exist
                os.makedirs(os.path.dirname(self.revocation_cache_path), exist_ok=True)
                
                # Save revocation cache
                cache_data = {
                    'updated_at': datetime.now().isoformat(),
                    'revoked_licenses': [item.get('license_key', '') for item in revocation_data.get('revoked_licenses', [])],
                    'count': revocation_data.get('count', 0)
                }
                
                with open(self.revocation_cache_path, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                logger.info(f"Updated revocation cache with {cache_data['count']} entries")
                
        except Exception as e:
            logger.error(f"Failed to update revocation cache: {e}")
    
    def force_remote_validation(self) -> Tuple[bool, str, Optional[Dict]]:
        """Force a remote license validation, bypassing cache."""
        # Clear local cache to force remote check
        if os.path.exists(self.revocation_cache_path):
            os.remove(self.revocation_cache_path)
        
        # Temporarily enable remote checking
        original_remote_check = self.enable_remote_check
        self.enable_remote_check = True
        
        try:
            result = self.validate_license()
            return result
        finally:
            self.enable_remote_check = original_remote_check
    
    def get_revocation_cache_info(self) -> Dict:
        """Get information about the local revocation cache."""
        try:
            if not os.path.exists(self.revocation_cache_path):
                return {
                    'cache_exists': False,
                    'message': 'No revocation cache found'
                }
            
            with open(self.revocation_cache_path, 'r') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data.get('updated_at', '1970-01-01'))
            age_seconds = (datetime.now() - cache_time).total_seconds()
            is_expired = age_seconds > self.cache_timeout
            
            return {
                'cache_exists': True,
                'updated_at': cache_data.get('updated_at'),
                'revoked_count': cache_data.get('count', 0),
                'age_seconds': int(age_seconds),
                'is_expired': is_expired,
                'cache_timeout': self.cache_timeout
            }
            
        except Exception as e:
            return {
                'cache_exists': False,
                'error': str(e)
            }

# Convenience functions
def verify_license() -> Tuple[bool, str]:
    """Quick license verification function."""
    validator = LicenseValidator()
    is_valid, message, _ = validator.validate_license()
    return is_valid, message

def check_feature(feature: str) -> bool:
    """Quick feature check function."""
    validator = LicenseValidator()
    return validator.check_feature_access(feature)

def get_license_status() -> Dict:
    """Get current license status."""
    validator = LicenseValidator()
    return validator.get_license_info()