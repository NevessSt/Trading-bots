#!/usr/bin/env python3
"""
License Generator Tool

This tool generates encrypted license files for the trading bot application.
Usage: python license_generator.py [options]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

# Add parent directory to path to import license_check
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.license_check import LicenseValidator
except ImportError:
    print("Error: Could not import LicenseValidator. Make sure backend/license_check.py exists.")
    sys.exit(1)

class LicenseGenerator:
    """License generator for creating encrypted license files."""
    
    def __init__(self, encryption_key_path=None):
        self.encryption_key_path = encryption_key_path or os.path.join(
            os.path.dirname(__file__), '..', 'backend', 'config', 'encryption.key'
        )
        self.validator = LicenseValidator()
    
    def load_or_create_encryption_key(self):
        """Load existing encryption key or create a new one."""
        try:
            if os.path.exists(self.encryption_key_path):
                with open(self.encryption_key_path, 'rb') as f:
                    return f.read()
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.encryption_key_path), exist_ok=True)
                
                # Generate new key
                key = Fernet.generate_key()
                with open(self.encryption_key_path, 'wb') as f:
                    f.write(key)
                print(f"New encryption key created at: {self.encryption_key_path}")
                return key
        except Exception as e:
            raise Exception(f"Failed to load/create encryption key: {str(e)}")
    
    def encrypt_license_data(self, license_data):
        """Encrypt license data."""
        try:
            key = self.load_or_create_encryption_key()
            fernet = Fernet(key)
            
            # Convert to JSON and encrypt
            json_data = json.dumps(license_data, indent=2)
            encrypted_data = fernet.encrypt(json_data.encode())
            return encrypted_data
        except Exception as e:
            raise Exception(f"Failed to encrypt license data: {str(e)}")
    
    def create_license(self, machine_id, license_type, days_valid, features=None, output_file=None):
        """Create a new license file."""
        if features is None:
            features = self.get_default_features(license_type)
        
        # Calculate expiry date
        expiry_date = datetime.now() + timedelta(days=days_valid)
        
        # Create license data
        license_data = {
            'machine_id': machine_id.upper(),
            'expiry_date': expiry_date.isoformat(),
            'license_type': license_type,
            'features': features,
            'generated_at': datetime.now().isoformat(),
            'valid_days': days_valid,
            'generator_version': '1.0'
        }
        
        # Encrypt license data
        encrypted_data = self.encrypt_license_data(license_data)
        
        # Save to file
        if output_file is None:
            output_file = f"license_{machine_id[:8]}_{license_type}.bin"
        
        try:
            with open(output_file, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"License created successfully: {output_file}")
            print(f"License Type: {license_type}")
            print(f"Valid for: {days_valid} days")
            print(f"Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Features: {', '.join(features)}")
            
            return output_file
        except Exception as e:
            raise Exception(f"Failed to save license file: {str(e)}")
    
    def get_default_features(self, license_type):
        """Get default features for each license type."""
        feature_sets = {
            'trial': [
                'basic_trading',
                'risk_management',
                'market_data',
                'single_exchange'
            ],
            'standard': [
                'basic_trading',
                'advanced_trading',
                'risk_management',
                'market_data',
                'single_exchange',
                'backtesting',
                'portfolio_management'
            ],
            'premium': [
                'basic_trading',
                'advanced_trading',
                'risk_management',
                'market_data',
                'multi_exchange',
                'backtesting',
                'portfolio_management',
                'advanced_strategies',
                'api_access'
            ],
            'enterprise': [
                'basic_trading',
                'advanced_trading',
                'risk_management',
                'market_data',
                'multi_exchange',
                'backtesting',
                'portfolio_management',
                'advanced_strategies',
                'api_access',
                'white_label',
                'priority_support',
                'custom_features'
            ]
        }
        
        return feature_sets.get(license_type, feature_sets['trial'])
    
    def validate_existing_license(self, license_file):
        """Validate an existing license file."""
        try:
            validator = LicenseValidator(license_file)
            is_valid, message, license_data = validator.validate_license()
            
            print(f"License File: {license_file}")
            print(f"Valid: {is_valid}")
            print(f"Message: {message}")
            
            if license_data:
                print(f"License Type: {license_data['license_type']}")
                print(f"Expiry Date: {license_data['expiry_date']}")
                print(f"Features: {', '.join(license_data['features'])}")
                
                # Calculate days remaining
                expiry = datetime.fromisoformat(license_data['expiry_date'])
                days_remaining = (expiry - datetime.now()).days
                print(f"Days Remaining: {days_remaining}")
            
            return is_valid
        except Exception as e:
            print(f"Error validating license: {str(e)}")
            return False
    
    def create_trial_license(self, machine_id, days=30, output_file=None):
        """Create a trial license."""
        return self.create_license(machine_id, 'trial', days, output_file=output_file)

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='License Generator for Trading Bot')
    parser.add_argument('--machine-id', required=True, help='Machine ID for license binding')
    parser.add_argument('--type', choices=['trial', 'standard', 'premium', 'enterprise'], 
                       default='trial', help='License type')
    parser.add_argument('--days', type=int, default=30, help='Number of days license is valid')
    parser.add_argument('--output', help='Output license file name')
    parser.add_argument('--features', nargs='*', help='Custom features list')
    parser.add_argument('--validate', help='Validate existing license file')
    parser.add_argument('--trial', action='store_true', help='Create trial license (shortcut)')
    
    args = parser.parse_args()
    
    generator = LicenseGenerator()
    
    try:
        if args.validate:
            generator.validate_existing_license(args.validate)
        elif args.trial:
            generator.create_trial_license(args.machine_id, args.days, args.output)
        else:
            generator.create_license(
                args.machine_id, 
                args.type, 
                args.days, 
                args.features, 
                args.output
            )
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()