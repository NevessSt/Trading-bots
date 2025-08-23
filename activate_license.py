#!/usr/bin/env python3
"""
Simple license activation script
"""

import sys
import os
sys.path.append('backend')

from license_activation import LicenseActivator

def main():
    print("Trading Bot License Activation")
    print("=" * 40)
    
    activator = LicenseActivator()
    
    # Generate a premium license code (1 year)
    print("Generating premium license code...")
    premium_code = activator.generate_license_code("premium", 365)
    print(f"\nGenerated License Code:")
    print(f"{premium_code}")
    
    print("\n" + "=" * 40)
    print("Activating license...")
    
    # Activate the license
    success, message = activator.activate_license(premium_code)
    
    if success:
        print(f"✅ SUCCESS: {message}")
        print("\nYour trading bot is now fully activated with premium features!")
        print("\nEnabled features:")
        print("- Basic Trading")
        print("- Advanced Trading Strategies")
        print("- Portfolio Management")
        print("- Risk Management")
        print("- Market Data Access")
        print("- API Access")
        print("- Multi-Exchange Support")
        print("- Custom Indicators")
    else:
        print(f"❌ FAILED: {message}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())