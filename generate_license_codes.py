#!/usr/bin/env python3
"""
Interactive License Code Generator
This script provides a menu-driven interface to generate different types of license keys.
"""

import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from auth.license_manager import LicenseManager
from config.config import Config

def display_menu():
    """Display the main menu"""
    print("\n" + "="*60)
    print("🔑 LICENSE CODE GENERATOR")
    print("="*60)
    print("Choose the type of license you want to generate:")
    print()
    print("1. 🆓 FREE License (Basic features)")
    print("   - 1 bot maximum")
    print("   - No live trading")
    print("   - Basic features only")
    print()
    print("2. 💎 PREMIUM License (Advanced features)")
    print("   - 10 bots maximum")
    print("   - Live trading enabled")
    print("   - Advanced strategies")
    print("   - API access")
    print("   - Priority support")
    print("   - Custom indicators")
    print()
    print("3. 🚀 ENTERPRISE License (All features)")
    print("   - Unlimited bots")
    print("   - Live trading enabled")
    print("   - Advanced strategies")
    print("   - API access")
    print("   - Priority support")
    print("   - Custom indicators")
    print()
    print("4. ❌ Exit")
    print("="*60)

def get_user_input():
    """Get user email and duration"""
    print("\n📧 License Configuration:")
    user_email = input("Enter user email (default: danielmanji38@gmail.com): ").strip()
    if not user_email:
        user_email = "danielmanji38@gmail.com"
    
    duration_input = input("Enter license duration in days (default: 365): ").strip()
    try:
        duration_days = int(duration_input) if duration_input else 365
    except ValueError:
        duration_days = 365
        print("⚠️  Invalid duration, using default: 365 days")
    
    return user_email, duration_days

def generate_license(license_type, user_email, duration_days):
    """Generate a license key"""
    # Create Flask app context
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        try:
            # Generate license key
            license_key = LicenseManager.generate_license_key(
                license_type=license_type,
                duration_days=duration_days,
                user_email=user_email
            )
            
            # Validate the generated key
            license_data, error_message = LicenseManager.validate_license_key(license_key)
            
            if license_data:
                print("\n" + "="*60)
                print(f"✅ {license_type.upper()} LICENSE GENERATED SUCCESSFULLY")
                print("="*60)
                print(f"\n📋 License Key:")
                print(f"{license_key}")
                print(f"\n📊 License Details:")
                print(f"- Type: {license_data['type'].upper()}")
                print(f"- User Email: {license_data.get('user_email', 'Not specified')}")
                print(f"- Created: {license_data['created']}")
                print(f"- Expires: {license_data['expires']}")
                print(f"- Duration: {duration_days} days")
                
                print(f"\n🎯 {license_type.upper()} Features:")
                features = LicenseManager.LICENSE_FEATURES[license_type]
                for feature, value in features.items():
                    if feature == 'max_bots' and value == -1:
                        print(f"- {feature}: Unlimited")
                    else:
                        print(f"- {feature}: {value}")
                
                print(f"\n✅ Validation: VALID")
                print("="*60)
                
                # Ask if user wants to copy to clipboard or save to file
                print("\n💾 Save Options:")
                print("1. Copy license key to use in application")
                print("2. Continue generating more licenses")
                print("3. Exit")
                
                save_choice = input("\nChoose an option (1-3): ").strip()
                if save_choice == "1":
                    print(f"\n📋 Copy this license key:")
                    print(f"\n{license_key}\n")
                    input("Press Enter to continue...")
                
                return True
            else:
                print(f"❌ Error: Generated license key is invalid! {error_message}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating license key: {str(e)}")
            return False

def main():
    """Main program loop"""
    print("🚀 Welcome to the Interactive License Generator!")
    
    while True:
        display_menu()
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                # Free License
                user_email, duration_days = get_user_input()
                generate_license("free", user_email, duration_days)
                
            elif choice == "2":
                # Premium License
                user_email, duration_days = get_user_input()
                generate_license("premium", user_email, duration_days)
                
            elif choice == "3":
                # Enterprise License
                user_email, duration_days = get_user_input()
                generate_license("enterprise", user_email, duration_days)
                
            elif choice == "4":
                print("\n👋 Thank you for using the License Generator!")
                print("🔑 Your generated license keys are ready to use.")
                break
                
            else:
                print("\n⚠️  Invalid choice! Please select 1-4.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()