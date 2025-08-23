#!/usr/bin/env python3

import sys
sys.path.append('backend')

from license_activation import LicenseActivator

def main():
    print("\n" + "="*60)
    print("TRADING BOT LICENSE KEY GENERATOR")
    print("="*60)
    
    activator = LicenseActivator()
    
    # Generate premium license key
    license_key = activator.generate_license_code("premium", 365)
    
    print("\nYour Premium License Key:")
    print("-" * 40)
    print(license_key)
    print("-" * 40)
    
    print("\nInstructions:")
    print("1. Copy the ENTIRE key above (including the part after the dash)")
    print("2. Go to your trading bot web interface")
    print("3. Navigate to License page")
    print("4. Paste the key in the 'License Key' field")
    print("5. Click 'Activate License'")
    
    print("\nLicense Details:")
    print(f"- Type: Premium")
    print(f"- Valid for: 365 days (1 year)")
    print(f"- Features: All premium features enabled")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()