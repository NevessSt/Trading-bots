#!/usr/bin/env python3
"""
Generate a test license key for testing purposes
"""

import os
import sys
from flask import Flask
from auth.license_manager import LicenseManager
from config import Config

def create_app():
    """Create Flask app for license generation"""
    app = Flask(__name__)
    app.config.from_object(Config)
    return app

def generate_test_license():
    """Generate a test license key"""
    app = create_app()
    
    with app.app_context():
        # Generate premium license key valid for 365 days
        license_key = LicenseManager.generate_license_key(
            license_type='premium',
            duration_days=365,
            user_email='danielmanji38@gmail.com'
        )
        
        if license_key:
            print("Generated test license key:")
            print(f"License Key: {license_key}")
            print("\nLicense Details:")
            print("- Type: Premium")
            print("- Duration: 365 days")
            print("- User: danielmanji38@gmail.com")
            print("\nFeatures included:")
            features = LicenseManager.LICENSE_FEATURES.get('premium', {})
            for feature, enabled in features.items():
                print(f"- {feature}: {enabled}")
            
            # Validate the generated key
            license_data, error = LicenseManager.validate_license_key(license_key)
            if error:
                print(f"\n❌ Validation failed: {error}")
            else:
                print(f"\n✅ License key is valid!")
                print(f"Expires: {license_data['expires']}")
            
            return license_key
        else:
            print("❌ Failed to generate license key")
            return None

if __name__ == "__main__":
    license_key = generate_test_license()
    if license_key:
        print(f"\n=== Copy this license key for testing ===")
        print(license_key)
        print("=" * 50)