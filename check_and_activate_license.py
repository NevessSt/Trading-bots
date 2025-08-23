#!/usr/bin/env python3
"""
Check current license status and activate if needed
"""

import sys
import os
sys.path.append('backend')

from license_check import LicenseValidator, get_license_status
from license_activation import LicenseActivator

def main():
    print("Trading Bot License Status Check")
    print("=" * 50)
    
    # Check current license status
    validator = LicenseValidator()
    license_info = get_license_status()
    
    print(f"License Valid: {license_info['valid']}")
    print(f"License Type: {license_info['license_type']}")
    print(f"Expiry Date: {license_info['expiry_date']}")
    print(f"Message: {license_info['message']}")
    
    if license_info['valid']:
        print(f"Days Remaining: {license_info['days_remaining']}")
        print(f"Available Features: {', '.join(license_info['features'])}")
        print("\n✅ Your license is already active and valid!")
        return 0
    
    print("\n" + "=" * 50)
    print("License not found or invalid. Activating premium license...")
    
    # Generate and activate a premium license
    activator = LicenseActivator()
    
    # Generate a premium license code (1 year)
    premium_code = activator.generate_license_code("premium", 365)
    print(f"\nGenerated License Code: {premium_code}")
    
    # Activate the license
    success, message = activator.activate_license(premium_code)
    
    if success:
        print(f"\n✅ SUCCESS: {message}")
        
        # Check status again
        updated_info = get_license_status()
        print("\n" + "=" * 50)
        print("Updated License Status:")
        print(f"License Type: {updated_info['license_type']}")
        print(f"Valid Until: {updated_info['expiry_date']}")
        print(f"Days Remaining: {updated_info['days_remaining']}")
        print("\nEnabled Features:")
        for feature in updated_info['features']:
            print(f"  - {feature.replace('_', ' ').title()}")
        
        print("\n🎉 Your trading bot is now fully activated with premium features!")
    else:
        print(f"\n❌ ACTIVATION FAILED: {message}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())