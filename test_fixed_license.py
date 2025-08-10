#!/usr/bin/env python3
"""
Test script to verify the license field name fix
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.license_activation import LicenseActivator
from backend.license_check import LicenseValidator

def test_license_fix():
    print("\n" + "="*60)
    print("         TESTING LICENSE FIELD NAME FIX")
    print("="*60)
    
    # Step 1: Generate a new license
    print("\n🔧 Step 1: Generating new license with correct field names")
    activator = LicenseActivator()
    trial_code = activator.generate_license_code('trial', 30)
    print(f"✅ Generated license code: {trial_code[:50]}...")
    
    # Step 2: Activate the license
    print("\n🔧 Step 2: Activating the license")
    success, message = activator.activate_license(trial_code)
    print(f"✅ Activation result: {success}")
    print(f"📝 Message: {message}")
    
    # Step 3: Validate with the license checker
    print("\n🔧 Step 3: Validating with license checker")
    validator = LicenseValidator()
    is_valid, validation_message, license_data = validator.validate_license()
    print(f"✅ Validation result: {is_valid}")
    print(f"📝 Message: {validation_message}")
    
    if license_data:
        print(f"📊 License data: {license_data}")
    
    print("\n" + "="*60)
    if is_valid:
        print("🎉 SUCCESS: License system is now working correctly!")
    else:
        print("❌ ISSUE: License validation still failing")
    print("="*60)

if __name__ == "__main__":
    try:
        test_license_fix()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()