#!/usr/bin/env python3
"""
License Activation System

This module handles user-friendly license activation through license codes.
Users can enter a license code in the web interface to activate their license.
"""

import os
import json
import hashlib
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from tools.machine_id import generate_machine_id

class LicenseActivator:
    """Handles license activation from license codes."""
    
    def __init__(self):
        self.encryption_key_file = "backend/config/encryption.key"
        self.license_file = "license_key.bin"
        self.load_encryption_key()
    
    def load_encryption_key(self):
        """Load or create encryption key."""
        try:
            if os.path.exists(self.encryption_key_file):
                with open(self.encryption_key_file, 'rb') as f:
                    self.key = f.read()
            else:
                # Create new key if it doesn't exist
                self.key = Fernet.generate_key()
                os.makedirs(os.path.dirname(self.encryption_key_file), exist_ok=True)
                with open(self.encryption_key_file, 'wb') as f:
                    f.write(self.key)
            
            self.cipher = Fernet(self.key)
        except Exception as e:
            raise Exception(f"Failed to load encryption key: {str(e)}")
    
    def generate_license_code(self, license_type="standard", days=365, features=None):
        """Generate a license code that can be given to users.
        
        Args:
            license_type (str): Type of license (trial, standard, premium, enterprise)
            days (int): Number of days the license is valid
            features (list): List of features to enable
            
        Returns:
            str: License code that users can enter
        """
        if features is None:
            features = self._get_default_features(license_type)
        
        # Create license data
        license_data = {
            'type': license_type,
            'created_at': datetime.utcnow().isoformat(),
            'expiry_date': (datetime.utcnow() + timedelta(days=days)).isoformat(),
            'features': features,
            'days': days
        }
        
        # Convert to JSON and encode
        json_data = json.dumps(license_data, separators=(',', ':'))
        encoded_data = base64.b64encode(json_data.encode()).decode()
        
        # Create checksum for validation
        checksum = hashlib.sha256(encoded_data.encode()).hexdigest()[:8]
        
        # Format as user-friendly license code
        license_code = f"{encoded_data}-{checksum}"
        
        return license_code
    
    def activate_license(self, license_code):
        """Activate a license using a license code.
        
        Args:
            license_code (str): License code provided by the user
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Clean the license code (remove whitespace, newlines, etc.)
            license_code = license_code.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            
            # Validate license code format
            if '-' not in license_code:
                return False, "Invalid license code format"
            
            encoded_data, provided_checksum = license_code.rsplit('-', 1)
            
            # Verify checksum
            expected_checksum = hashlib.sha256(encoded_data.encode()).hexdigest()[:8]
            if provided_checksum != expected_checksum:
                return False, "Invalid license code - checksum mismatch"
            
            # Decode license data
            try:
                json_data = base64.b64decode(encoded_data.encode()).decode()
                license_data = json.loads(json_data)
            except Exception:
                return False, "Invalid license code - corrupted data"
            
            # Validate required fields
            required_fields = ['type', 'created_at', 'expiry_date', 'features']
            for field in required_fields:
                if field not in license_data:
                    return False, f"Invalid license code - missing {field}"
            
            # Check if license is expired
            expiry_date = datetime.fromisoformat(license_data['expiry_date'])
            if datetime.utcnow() > expiry_date:
                return False, "License code has expired"
            
            # Get current machine ID
            machine_id = generate_machine_id()
            
            # Create final license data with machine binding
            final_license_data = {
                'machine_id': machine_id,
                'license_type': license_data['type'],
                'created_at': license_data['created_at'],
                'expiry_date': license_data['expiry_date'],
                'features': license_data['features'],
                'activated_at': datetime.utcnow().isoformat()
            }
            
            # Encrypt and save license
            json_str = json.dumps(final_license_data, separators=(',', ':'))
            encrypted_data = self.cipher.encrypt(json_str.encode())
            
            with open(self.license_file, 'wb') as f:
                f.write(encrypted_data)
            
            return True, f"License activated successfully! Type: {license_data['type']}, Valid until: {expiry_date.strftime('%Y-%m-%d')}"
            
        except Exception as e:
            return False, f"License activation failed: {str(e)}"
    
    def _get_default_features(self, license_type):
        """Get default features for license type."""
        feature_sets = {
            'trial': ['basic_trading', 'risk_management', 'market_data', 'single_exchange'],
            'standard': ['basic_trading', 'risk_management', 'market_data', 'single_exchange', 'api_access'],
            'premium': ['basic_trading', 'advanced_trading', 'portfolio_management', 'risk_management', 
                       'market_data', 'api_access', 'multi_exchange', 'custom_indicators'],
            'enterprise': ['basic_trading', 'advanced_trading', 'portfolio_management', 'risk_management',
                          'market_data', 'api_access', 'multi_exchange', 'custom_indicators', 'white_label']
        }
        return feature_sets.get(license_type, feature_sets['trial'])

# Example usage and testing
if __name__ == "__main__":
    activator = LicenseActivator()
    
    # Generate a sample license code
    print("Generating sample license codes:")
    print("=" * 50)
    
    # Trial license
    trial_code = activator.generate_license_code("trial", 30)
    print(f"Trial License (30 days): {trial_code}")
    
    # Standard license
    standard_code = activator.generate_license_code("standard", 365)
    print(f"Standard License (1 year): {standard_code}")
    
    # Premium license
    premium_code = activator.generate_license_code("premium", 365)
    print(f"Premium License (1 year): {premium_code}")
    
    print("\n" + "=" * 50)
    print("Test activation with trial code:")
    success, message = activator.activate_license(trial_code)
    print(f"Result: {success}")
    print(f"Message: {message}")