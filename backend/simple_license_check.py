#!/usr/bin/env python3
"""
Simple license status checker
"""

import os
import sys
sys.path.append('.')

try:
    from license_check import LicenseValidator
    
    print("Checking License Status...")
    print("=" * 30)
    
    # Initialize validator
    validator = LicenseValidator()
    
    # Check license file existence
    license_file = validator.license_file_path
    print(f"License file: {os.path.basename(license_file)}")
    print(f"File exists: {os.path.exists(license_file)}")
    
    if os.path.exists(license_file):
        # Validate license
        is_valid, message, license_data = validator.validate_license()
        print(f"\nValidation Result:")
        print(f"Valid: {is_valid}")
        print(f"Message: {message}")
        
        if is_valid and license_data:
            print(f"\nLicense Details:")
            print(f"Type: {license_data.get('license_type', 'Unknown')}")
            print(f"Expires: {license_data.get('expiry_date', 'Unknown')}")
            print(f"Features: {len(license_data.get('features', []))} enabled")
            
            # Show feature status
            features = license_data.get('features', [])
            if features:
                print(f"\nEnabled Features:")
                for feature in features:
                    print(f"  ✅ {feature}")
            
            print(f"\n🎉 Account Status: PREMIUM ACTIVATED")
        else:
            print(f"\n❌ License validation failed")
    else:
        print(f"\n❌ No license file found")
        
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()

# Execute the check immediately when imported
print("\n" + "="*50)
print("EXECUTING LICENSE CHECK...")
print("="*50)