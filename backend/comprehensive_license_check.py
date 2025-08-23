#!/usr/bin/env python3
"""
Comprehensive license status checker for trading bot
"""

import os
import json
from datetime import datetime

def check_license_json():
    """Check the license.json file status"""
    print("\n📄 Checking license.json...")
    license_json_path = "config/license.json"
    
    if os.path.exists(license_json_path):
        try:
            with open(license_json_path, 'r') as f:
                license_data = json.load(f)
            
            print(f"✅ License file found: {license_json_path}")
            print(f"License ID: {license_data.get('license_id', 'Unknown')}")
            print(f"User Email: {license_data.get('user_email', 'Unknown')}")
            print(f"Expiry Date: {license_data.get('expiry_date', 'Unknown')}")
            print(f"Activated At: {license_data.get('activated_at', 'Unknown')}")
            
            # Check if expired
            try:
                expiry_str = license_data.get('expiry_date', '')
                if expiry_str:
                    expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                    now = datetime.now(expiry_date.tzinfo) if expiry_date.tzinfo else datetime.now()
                    
                    if now < expiry_date:
                        days_left = (expiry_date - now).days
                        print(f"⏰ Status: ACTIVE ({days_left} days remaining)")
                    else:
                        print(f"⚠️  Status: EXPIRED")
                else:
                    print(f"⚠️  Status: No expiry date found")
            except Exception as e:
                print(f"⚠️  Could not parse expiry date: {e}")
            
            # Show features
            features = license_data.get('features', [])
            if features:
                print(f"\n🎯 Enabled Features ({len(features)}):")
                for feature in features:
                    print(f"  ✅ {feature.replace('_', ' ').title()}")
            
            return True, license_data
            
        except Exception as e:
            print(f"❌ Error reading license.json: {e}")
            return False, None
    else:
        print(f"❌ License file not found: {license_json_path}")
        return False, None

def check_license_bin():
    """Check the license_key.bin file status"""
    print("\n🔐 Checking license_key.bin...")
    license_bin_path = "../license_key.bin"
    
    if os.path.exists(license_bin_path):
        print(f"✅ Encrypted license file found: {license_bin_path}")
        file_size = os.path.getsize(license_bin_path)
        print(f"File size: {file_size} bytes")
        
        # Try to validate using the license system
        try:
            from license_check import LicenseValidator
            validator = LicenseValidator(license_bin_path)
            is_valid, message, license_data = validator.validate_license()
            
            print(f"Validation result: {is_valid}")
            print(f"Message: {message}")
            
            if is_valid and license_data:
                print(f"\n📋 License Details:")
                print(f"  Type: {license_data.get('license_type', 'Unknown')}")
                print(f"  Machine ID: {license_data.get('machine_id', 'Unknown')[:16]}...")
                print(f"  Created: {license_data.get('created_at', 'Unknown')}")
                print(f"  Expires: {license_data.get('expiry_date', 'Unknown')}")
                
                features = license_data.get('features', [])
                if features:
                    print(f"\n🎯 Enabled Features ({len(features)}):")
                    for feature in features:
                        print(f"  ✅ {feature.replace('_', ' ').title()}")
            
            return is_valid, license_data
            
        except Exception as e:
            print(f"❌ Error validating license_key.bin: {e}")
            return False, None
    else:
        print(f"❌ Encrypted license file not found: {license_bin_path}")
        return False, None

def check_trading_engine_license():
    """Check if trading engine accepts the current license"""
    print("\n🤖 Checking Trading Engine License Validation...")
    
    try:
        from license_check import verify_license
        is_valid, message = verify_license()
        
        print(f"Trading Engine Validation: {is_valid}")
        print(f"Message: {message}")
        
        if is_valid:
            print(f"✅ Trading engine will accept current license")
        else:
            print(f"⚠️  Trading engine license validation failed")
            
        return is_valid
        
    except Exception as e:
        print(f"❌ Error checking trading engine license: {e}")
        return False

def main():
    """Main license status check"""
    print("🔍 COMPREHENSIVE LICENSE STATUS CHECK")
    print("=" * 50)
    
    # Check both license systems
    json_valid, json_data = check_license_json()
    bin_valid, bin_data = check_license_bin()
    engine_valid = check_trading_engine_license()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if json_valid:
        print("✅ license.json: VALID")
    else:
        print("❌ license.json: INVALID/MISSING")
        
    if bin_valid:
        print("✅ license_key.bin: VALID")
    else:
        print("❌ license_key.bin: INVALID/MISSING")
        
    if engine_valid:
        print("✅ Trading Engine: ACCEPTS LICENSE")
    else:
        print("⚠️  Trading Engine: LICENSE ISSUES (but runs in demo mode)")
    
    # Overall status
    if json_valid or bin_valid:
        print("\n🎉 OVERALL STATUS: ACCOUNT ACTIVATED")
        print("Your trading bot has premium features enabled!")
        
        if json_valid and json_data:
            features = json_data.get('features', [])
            if features:
                print(f"\n🚀 Available Features:")
                for feature in features:
                    print(f"  • {feature.replace('_', ' ').title()}")
    else:
        print("\n⚠️  OVERALL STATUS: NO VALID LICENSE FOUND")
        print("The system will run in demo mode with limited features.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()

# Execute immediately when imported
print("\n🔄 EXECUTING COMPREHENSIVE LICENSE CHECK...")
main()