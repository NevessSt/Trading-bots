#!/usr/bin/env python3
"""
Direct license file creation - bypasses command execution issues
"""

import os
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

# Simple machine ID generation
def simple_machine_id():
    import platform
    import hashlib
    import uuid
    
    info = f"{platform.system()}|{platform.machine()}|{uuid.getnode()}"
    return hashlib.sha256(info.encode()).hexdigest()[:32]

# Create license directly
def create_license():
    print("Creating Premium License...")
    
    # Get machine ID
    machine_id = simple_machine_id()
    print(f"Machine ID: {machine_id}")
    
    # Create license data
    expiry_date = datetime.utcnow() + timedelta(days=365)
    license_data = {
        'machine_id': machine_id,
        'license_type': 'premium',
        'created_at': datetime.utcnow().isoformat(),
        'expiry_date': expiry_date.isoformat(),
        'features': [
            'basic_trading',
            'advanced_trading', 
            'portfolio_management',
            'risk_management',
            'market_data',
            'api_access',
            'multi_exchange',
            'custom_indicators'
        ],
        'activated_at': datetime.utcnow().isoformat()
    }
    
    # Create encryption key
    encryption_key_file = "config/encryption.key"
    os.makedirs(os.path.dirname(encryption_key_file), exist_ok=True)
    
    if os.path.exists(encryption_key_file):
        with open(encryption_key_file, 'rb') as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(encryption_key_file, 'wb') as f:
            f.write(key)
    
    # Encrypt license data
    cipher = Fernet(key)
    json_str = json.dumps(license_data, separators=(',', ':'))
    encrypted_data = cipher.encrypt(json_str.encode())
    
    # Save license file
    license_file = "../license_key.bin"
    with open(license_file, 'wb') as f:
        f.write(encrypted_data)
    
    print(f"✅ Premium license created successfully!")
    print(f"License Type: {license_data['license_type']}")
    print(f"Valid Until: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Features: {', '.join(license_data['features'])}")
    print(f"License file saved to: {os.path.abspath(license_file)}")
    
    return True

# Execute directly
if __name__ == "__main__":
    try:
        create_license()
        print("\n🎉 License activation completed successfully!")
        print("Your trading bot now has full premium features enabled.")
    except Exception as e:
        print(f"❌ Error creating license: {str(e)}")
        import traceback
        traceback.print_exc()

# Also execute immediately for direct import
try:
    create_license()
    print("\n🎉 License activation completed successfully!")
    print("Your trading bot now has full premium features enabled.")
except Exception as e:
    print(f"❌ Error creating license: {str(e)}")
    import traceback
    traceback.print_exc()