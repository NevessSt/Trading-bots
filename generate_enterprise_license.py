#!/usr/bin/env python3
"""
Generate Enterprise License Key
This script generates the highest tier license (Enterprise) with all features enabled.
"""

import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from auth.license_manager import LicenseManager
from config.config import Config

def generate_enterprise_license(user_email, duration_days=365):
    """Generate an Enterprise license key"""
    
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        try:
            # Generate Enterprise license key
            license_key = LicenseManager.generate_license_key(
                license_type='enterprise',
                duration_days=duration_days,
                user_email=user_email
            )
            
            # Validate the generated key
            license_data, error_message = LicenseManager.validate_license_key(license_key)
            
            if license_data:
                print("\n" + "="*60)
                print("ENTERPRISE LICENSE KEY GENERATED SUCCESSFULLY")
                print("="*60)
                print(f"\nLicense Key:")
                print(f"{license_key}")
                print(f"\nLicense Details:")
                print(f"- Type: {license_data['type'].upper()}")
                print(f"- User Email: {license_data.get('user_email', 'Not specified')}")
                print(f"- Created: {license_data['created']}")
                print(f"- Expires: {license_data['expires']}")
                print(f"- Duration: {duration_days} days")
                
                print(f"\nEnterprise Features:")
                features = LicenseManager.LICENSE_FEATURES['enterprise']
                for feature, value in features.items():
                    if feature == 'max_bots' and value == -1:
                        print(f"- {feature}: Unlimited")
                    else:
                        print(f"- {feature}: {value}")
                
                print(f"\nValidation: {'✓ VALID' if license_data else '✗ INVALID'}")
                print("="*60)
                
                return license_key
            else:
                print(f"Error: Generated license key is invalid!")
                return None
                
        except Exception as e:
            print(f"Error generating license key: {str(e)}")
            return None

if __name__ == "__main__":
    print("Enterprise License Generator")
    print("This generates the highest tier license with all features enabled.")
    
    # Get user email
    user_email = input("\nEnter user email (or press Enter for default): ").strip()
    if not user_email:
        user_email = "danielmanji38@gmail.com"  # Default email
    
    # Get duration
    duration_input = input("Enter license duration in days (default: 365): ").strip()
    try:
        duration_days = int(duration_input) if duration_input else 365
    except ValueError:
        duration_days = 365
        print("Invalid duration, using default: 365 days")
    
    # Generate the license
    license_key = generate_enterprise_license(user_email, duration_days)
    
    if license_key:
        print(f"\n🎉 Enterprise license key generated successfully!")
        print(f"\n📋 Copy this license key to activate:")
        print(f"{license_key}")
    else:
        print("\n❌ Failed to generate license key.")