import hashlib
import json
import os
import platform
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from typing import Dict, Optional, Tuple

# Import the standard machine ID generator
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools.machine_id import generate_machine_id

class LicenseValidator:
    """License validation system for the trading bot application."""
    
    def __init__(self, license_file_path: str = None):
        self.license_file_path = license_file_path or os.path.join(
            os.path.dirname(__file__), '..', 'license_key.bin'
        )
        self.encryption_key_path = os.path.join(
            os.path.dirname(__file__), 'config', 'encryption.key'
        )
    
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
        """Validate the license file.
        
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