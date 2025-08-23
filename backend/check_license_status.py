#!/usr/bin/env python3
"""
Check current license status
"""

import os
import sys
sys.path.append('.')
from license_check import LicenseValidator

def check_current_license():
    """Check the current license status"""
    print("Checking Current License Status...")
    print("=" * 40)
    
    try:
        # Initialize license validator
        validator = LicenseValidator()
        
        # Check if license file exists
        license_file = validator.license_file_path
        print(f"License file path: {license_file}")
        print(f"License file exists: {os.path.exists(license_file)}")
        
        if os.path.exists(license_file):
            # Validate license
            is_valid, message = validator.validate_license()
            print(f"License valid: {is_valid}")
            print(f"Validation message: {message}")
            
            if is_valid:
                # Get license info
                license_info = validator.get_license_info()
                if license_info:
                    print("\nLicense Details:")
                    print(f"  Type: {license_info.get('license_type', 'Unknown')}")
                    print(f"  Created: {license_info.get('created_at', 'Unknown')}")
                    print(f"  Expires: {license_info.get('expiry_date', 'Unknown')}")
                    print(f"  Features: {', '.join(license_info.get('features', []))}")
                    
                    # Check feature access
                    print("\nFeature Access:")
                    features_to_check = [
                        'basic_trading', 'advanced_trading', 'portfolio_management',
                        'risk_management', 'market_data', 'api_access'
                    ]
                    for feature in features_to_check:
                        has_access = validator.check_feature_access(feature)
                        print(f"  {feature}: {'✅ Enabled' if has_access else '❌ Disabled'}")
                else:
                    print("Could not retrieve license information")
            else:
                print(f"\n❌ License validation failed: {message}")
        else:
            print("\n❌ No license file found")
            
        # Show machine ID
        machine_id = validator.get_machine_id()
        print(f"\nMachine ID: {machine_id}")
        
    except Exception as e:
        print(f"❌ Error checking license: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_current_license()

# Execute immediately
check_current_license()