#!/usr/bin/env python3
"""
Quick test to generate and activate a license code
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.license_activation import LicenseActivator
    
    print("Creating LicenseActivator...")
    activator = LicenseActivator()
    
    print("Generating trial license code...")
    code = activator.generate_license_code('trial', 30)
    print(f"Generated code: {code}")
    print(f"Code length: {len(code)}")
    
    print("\nTesting activation immediately...")
    success, message = activator.activate_license(code)
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    if not success:
        print("\nDebugging the issue...")
        
        # Check for whitespace or special characters
        print(f"Code repr: {repr(code)}")
        
        # Test with stripped code
        stripped_code = code.strip()
        print(f"\nTrying with stripped code: {repr(stripped_code)}")
        success2, message2 = activator.activate_license(stripped_code)
        print(f"Success: {success2}")
        print(f"Message: {message2}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()