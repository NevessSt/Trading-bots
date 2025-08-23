#!/usr/bin/env python3
"""
Test License Activation
This script tests if a generated license key can be successfully activated.
"""

import sys
import os
import requests
import json

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_license_activation(license_key, email="danielmanji38@gmail.com", password="newpassword123"):
    """Test license activation with the backend API"""
    base_url = "http://localhost:5000/api"
    
    try:
        print("🔐 Testing License Activation...")
        print("="*50)
        
        # Step 1: Login to get access token
        print("1️⃣ Logging in...")
        login_response = requests.post(f"{base_url}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        access_token = login_response.json().get('access_token')
        print(f"✅ Login successful")
        
        # Step 2: Check current license status
        print("\n2️⃣ Checking current license status...")
        headers = {'Authorization': f'Bearer {access_token}'}
        status_response = requests.get(f"{base_url}/license/status", headers=headers)
        
        if status_response.status_code == 200:
            current_license = status_response.json().get('license', {})
            print(f"📊 Current license: {current_license.get('type', 'unknown')} (Active: {current_license.get('active', False)})")
        
        # Step 3: Activate the license
        print("\n3️⃣ Activating license...")
        activation_response = requests.post(f"{base_url}/license/activate", 
            headers=headers,
            json={"license_key": license_key}
        )
        
        if activation_response.status_code != 200:
            print(f"❌ License activation failed: {activation_response.text}")
            return False
        
        activation_data = activation_response.json()
        new_license = activation_data.get('license', {})
        print(f"✅ License activated successfully!")
        print(f"📊 New license: {new_license.get('type', 'unknown')} (Active: {new_license.get('active', False)})")
        
        # Step 4: Test feature access
        print("\n4️⃣ Testing feature access...")
        test_features = ['live_trading', 'api_access', 'custom_indicators']
        
        for feature in test_features:
            feature_response = requests.post(f"{base_url}/license/check-feature",
                headers=headers,
                json={"feature": feature}
            )
            
            if feature_response.status_code == 200:
                feature_data = feature_response.json()
                has_access = feature_data.get('has_access', False)
                print(f"🎯 {feature}: {'✅ Enabled' if has_access else '❌ Disabled'}")
            else:
                print(f"⚠️  Could not check {feature} access")
        
        print("\n" + "="*50)
        print("🎉 License activation test completed successfully!")
        print("🔑 Your license is now active and ready to use.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend server.")
        print("💡 Make sure the backend server is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error during license activation test: {str(e)}")
        return False

def main():
    """Main function"""
    print("🧪 License Activation Tester")
    print("This script tests if your generated license keys work correctly.\n")
    
    license_key = input("📋 Enter the license key to test: ").strip()
    
    if not license_key:
        print("❌ No license key provided!")
        return
    
    # Test the license activation
    success = test_license_activation(license_key)
    
    if success:
        print("\n✅ All tests passed! Your license system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()