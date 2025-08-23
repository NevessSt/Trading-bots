#!/usr/bin/env python3
"""
Test Frontend License Activation
This script generates a license key and provides instructions for testing in the frontend.
"""

import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from auth.license_manager import LicenseManager
from config.config import Config

def main():
    print("\n" + "="*60)
    print("🧪 FRONTEND LICENSE ACTIVATION TEST")
    print("="*60)
    
    # Initialize Flask app for license manager
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        # Generate a test enterprise license
        email = "danielmanji38@gmail.com"
        duration_days = 365
        
        print(f"\n🔑 Generating Enterprise License for: {email}")
        print(f"📅 Duration: {duration_days} days")
        
        license_key = LicenseManager.generate_license_key(
            license_type="enterprise",
            duration_days=duration_days,
            user_email=email
        )
        
        if license_key:
            print(f"\n✅ License Key Generated Successfully!")
            print("\n" + "-"*60)
            print("📋 COPY THIS LICENSE KEY:")
            print("-"*60)
            print(license_key)
            print("-"*60)
            
            # Validate the key
            license_data, error = LicenseManager.validate_license_key(license_key)
            if license_data:
                print(f"\n✅ License Validation: VALID")
                print(f"📊 Type: {license_data['type']}")
                print(f"📅 Expires: {license_data['expires']}")
                print(f"🎯 Features:")
                for feature, enabled in license_data['features'].items():
                    status = "✅" if enabled else "❌"
                    print(f"   {status} {feature}: {enabled}")
            else:
                print(f"❌ License Validation Failed: {error}")
                return
            
            print("\n" + "="*60)
            print("🌐 FRONTEND TESTING INSTRUCTIONS")
            print("="*60)
            print("1. Open your browser and go to: http://localhost:3000")
            print("2. Login with your credentials:")
            print(f"   📧 Email: {email}")
            print("   🔒 Password: newpassword123")
            print("3. Navigate to the License page")
            print("4. Copy and paste the license key above")
            print("5. Click 'Activate License'")
            print("6. Verify that the license type changes to 'Enterprise'")
            print("7. Check that all features are enabled")
            
            print("\n💡 TROUBLESHOOTING:")
            print("- If activation fails, check browser console for errors")
            print("- Ensure backend server is running on http://localhost:5000")
            print("- Verify you're logged in with the correct user account")
            
            print("\n" + "="*60)
            
        else:
            print("❌ Failed to generate license key")

if __name__ == "__main__":
    main()