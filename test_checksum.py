#!/usr/bin/env python3
"""
Simple test for license checksum validation
"""

import json
import hashlib
import base64
from datetime import datetime, timedelta

def test_checksum():
    print("Testing license code checksum validation...")
    
    # Create sample license data
    license_data = {
        'type': 'trial',
        'created_at': datetime.utcnow().isoformat(),
        'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
        'features': ['basic_trading', 'risk_management', 'market_data', 'single_exchange'],
        'days': 30
    }
    
    # Convert to JSON and encode
    json_data = json.dumps(license_data, separators=(',', ':'))
    print(f"JSON data: {json_data}")
    
    encoded_data = base64.b64encode(json_data.encode()).decode()
    print(f"Encoded data: {encoded_data[:50]}...")
    
    # Create checksum
    checksum = hashlib.sha256(encoded_data.encode()).hexdigest()[:8]
    print(f"Generated checksum: {checksum}")
    
    # Create license code
    license_code = f"{encoded_data}-{checksum}"
    print(f"License code: {license_code[:50]}...")
    
    # Test validation
    print("\nTesting validation...")
    
    # Split the code
    if '-' not in license_code:
        print("ERROR: Invalid license code format")
        return
    
    test_encoded_data, test_checksum = license_code.rsplit('-', 1)
    print(f"Extracted encoded data: {test_encoded_data[:50]}...")
    print(f"Extracted checksum: {test_checksum}")
    
    # Verify checksum
    expected_checksum = hashlib.sha256(test_encoded_data.encode()).hexdigest()[:8]
    print(f"Expected checksum: {expected_checksum}")
    
    if test_checksum == expected_checksum:
        print("✅ Checksum validation PASSED")
        
        # Test decoding
        try:
            decoded_json = base64.b64decode(test_encoded_data.encode()).decode()
            decoded_data = json.loads(decoded_json)
            print("✅ Data decoding PASSED")
            print(f"Decoded license type: {decoded_data.get('type')}")
            print(f"Decoded features: {decoded_data.get('features')}")
        except Exception as e:
            print(f"❌ Data decoding FAILED: {e}")
    else:
        print("❌ Checksum validation FAILED")
        print(f"Expected: {expected_checksum}")
        print(f"Got: {test_checksum}")

if __name__ == "__main__":
    test_checksum()