#!/usr/bin/env python3
"""
Debug License Generation and Activation

This script tests the license generation and activation process
to identify the checksum mismatch issue.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.license_activation import LicenseActivator

def test_license_flow():
    print("\n" + "="*60)
    print("         DEBUG: LICENSE GENERATION & ACTIVATION")
    print("="*60)
    
    try:
        activator = LicenseActivator()
        
        # Generate a trial license code
        print("\n1. Generating trial license code...")
        trial_code = activator.generate_license_code("trial", 30)
        print(f"Generated code: {trial_code}")
        
        # Split and analyze the code
        if '-' in trial_code:
            encoded_data, checksum = trial_code.rsplit('-', 1)
            print(f"Encoded data: {encoded_data[:50]}...")
            print(f"Checksum: {checksum}")
            
            # Manually verify checksum
            import hashlib
            expected_checksum = hashlib.sha256(encoded_data.encode()).hexdigest()[:8]
            print(f"Expected checksum: {expected_checksum}")
            print(f"Checksums match: {checksum == expected_checksum}")
        
        # Test activation
        print("\n2. Testing license activation...")
        success, message = activator.activate_license(trial_code)
        print(f"Activation result: {success}")
        print(f"Message: {message}")
        
        if success:
            print("\n✅ License generation and activation working correctly!")
        else:
            print("\n❌ License activation failed!")
            
            # Try to debug the issue
            print("\n3. Debugging the issue...")
            
            # Check if it's a machine ID issue
            from tools.machine_id import generate_machine_id
            machine_id = generate_machine_id()
            print(f"Current machine ID: {machine_id}")
            
            # Check if license file exists
            if os.path.exists("license_key.bin"):
                print("License file exists - checking contents...")
                # Try to read existing license
                try:
                    from backend.license_check import verify_license
                    is_valid, license_info = verify_license()
                    print(f"Existing license valid: {is_valid}")
                    if license_info:
                        print(f"License info: {license_info}")
                except Exception as e:
                    print(f"Error reading existing license: {e}")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_license_flow()