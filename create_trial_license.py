#!/usr/bin/env python3
"""
Trial License Creator

This script creates a trial license for the trading bot application.
Usage: python create_trial_license.py
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tools.license_generator import LicenseGenerator
    from tools.machine_id import generate_machine_id
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure tools/license_generator.py and tools/machine_id.py exist.")
    sys.exit(1)

def create_trial_license(days=30):
    """Create a trial license for the current machine."""
    try:
        print("Creating trial license...")
        print("=" * 50)
        
        # Generate machine ID
        machine_id = generate_machine_id()
        print(f"Machine ID: {machine_id}")
        
        # Create license generator
        generator = LicenseGenerator()
        
        # Create trial license
        license_file = generator.create_trial_license(
            machine_id=machine_id,
            days=days,
            output_file="license_key.bin"
        )
        
        print("\n" + "=" * 50)
        print("TRIAL LICENSE CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"License file: {license_file}")
        print(f"Valid for: {days} days")
        print("\nYou can now start the trading bot application.")
        print("\nTo check license status, visit: http://localhost:5000/license-status")
        
        return True
        
    except Exception as e:
        print(f"Error creating trial license: {str(e)}")
        return False

def main():
    """Main function."""
    print("Trading Bot - Trial License Creator")
    print("=" * 40)
    
    # Check if license already exists
    if os.path.exists("license_key.bin"):
        print("License file already exists. Overwriting...")
    
    # Use default 30 days for trial
    days = 30
    print(f"Creating trial license for {days} days...")
    
    # Create trial license
    success = create_trial_license(days)
    
    if success:
        print("\nNext steps:")
        print("1. Start the application: python app.py")
        print("2. Open your browser to: http://localhost:5000")
        print("3. Check license status at: http://localhost:5000/license-status")
    else:
        print("\nFailed to create trial license. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()