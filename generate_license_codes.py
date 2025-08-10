#!/usr/bin/env python3
"""
License Code Generator for Trading Bot

This script generates license codes that can be distributed to customers.
The codes can then be activated through the web interface.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.license_activation import LicenseActivator

def main():
    print("\n" + "="*60)
    print("         TRADING BOT - LICENSE CODE GENERATOR")
    print("="*60)
    
    activator = LicenseActivator()
    
    while True:
        print("\nAvailable License Types:")
        print("1. Trial (30 days) - Basic features")
        print("2. Standard (1 year) - Basic + Advanced trading")
        print("3. Premium (1 year) - Standard + Multi-exchange + Portfolio")
        print("4. Enterprise (1 year) - All features")
        print("5. Custom duration")
        print("0. Exit")
        
        choice = input("\nSelect license type (0-5): ").strip()
        
        if choice == '0':
            print("\nGoodbye!")
            break
        elif choice == '1':
            # Trial license
            code = activator.generate_license_code('trial', 30)
            print(f"\n✅ Trial License Code Generated:")
            print(f"Code: {code}")
            print(f"Duration: 30 days")
            print(f"Features: Basic trading, Risk management, Market data, Single exchange")
            
        elif choice == '2':
            # Standard license
            code = activator.generate_license_code('standard', 365)
            print(f"\n✅ Standard License Code Generated:")
            print(f"Code: {code}")
            print(f"Duration: 1 year")
            print(f"Features: Basic + Advanced trading, Risk management, Market data, Single exchange")
            
        elif choice == '3':
            # Premium license
            code = activator.generate_license_code('premium', 365)
            print(f"\n✅ Premium License Code Generated:")
            print(f"Code: {code}")
            print(f"Duration: 1 year")
            print(f"Features: All Standard features + Multi-exchange, Portfolio management")
            
        elif choice == '4':
            # Enterprise license
            code = activator.generate_license_code('enterprise', 365)
            print(f"\n✅ Enterprise License Code Generated:")
            print(f"Code: {code}")
            print(f"Duration: 1 year")
            print(f"Features: All features including API access, White-label, Priority support")
            
        elif choice == '5':
            # Custom duration
            print("\nCustom License Configuration:")
            license_type = input("License type (trial/standard/premium/enterprise): ").strip().lower()
            
            if license_type not in ['trial', 'standard', 'premium', 'enterprise']:
                print("❌ Invalid license type!")
                continue
                
            try:
                days = int(input("Duration in days: ").strip())
                if days <= 0:
                    print("❌ Duration must be positive!")
                    continue
            except ValueError:
                print("❌ Invalid duration!")
                continue
                
            code = activator.generate_license_code(license_type, days)
            print(f"\n✅ Custom {license_type.title()} License Code Generated:")
            print(f"Code: {code}")
            print(f"Duration: {days} days")
            
        else:
            print("❌ Invalid choice! Please select 0-5.")
            continue
            
        print("\n" + "-"*60)
        print("📋 IMPORTANT INSTRUCTIONS FOR CUSTOMER:")
        print("1. Copy the license code above")
        print("2. Log into the trading bot application")
        print("3. Go to 'Activate License' in the navigation menu")
        print("4. Paste the license code and click 'Activate'")
        print("5. The license will be bound to their machine automatically")
        print("-"*60)
        
        another = input("\nGenerate another license? (y/n): ").strip().lower()
        if another != 'y':
            print("\nGoodbye!")
            break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)