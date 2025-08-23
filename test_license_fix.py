#!/usr/bin/env python3
"""
Test License Activation Fix
This script tests if the license activation fix is working properly.
"""

import requests
import json

def test_license_workflow():
    """Test the complete license workflow"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing License Activation Fix")
    print("=" * 50)
    
    # Step 1: Login to get authentication token
    print("\n1️⃣ Logging in...")
    login_data = {
        "email": "danielmanji38@gmail.com",
        "password": "newpassword123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
            
        login_data = login_response.json()
        token = login_data.get('access_token')
        if not token:
            print("❌ No access token received")
            return False
            
        print("✅ Login successful")
        headers = {'Authorization': f'Bearer {token}'}
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 2: Generate a new license
    print("\n2️⃣ Generating license...")
    try:
        license_data = {
            "license_type": "premium",
            "duration_days": 365,
            "user_email": "danielmanji38@gmail.com"
        }
        
        gen_response = requests.post(f"{base_url}/api/license/generate", 
                                   json=license_data, headers=headers)
        
        if gen_response.status_code != 200:
            print(f"❌ License generation failed: {gen_response.text}")
            return False
            
        gen_data = gen_response.json()
        license_key = gen_data.get('license_key')
        if not license_key:
            print("❌ No license key received")
            return False
            
        print("✅ License generated successfully")
        print(f"📋 License key: {license_key[:50]}...")
        
    except Exception as e:
        print(f"❌ License generation error: {e}")
        return False
    
    # Step 3: Activate the license
    print("\n3️⃣ Activating license...")
    try:
        activate_data = {"license_key": license_key}
        
        activate_response = requests.post(f"{base_url}/api/license/activate", 
                                        json=activate_data, headers=headers)
        
        print(f"Status Code: {activate_response.status_code}")
        print(f"Response: {activate_response.text}")
        
        if activate_response.status_code == 200:
            activation_data = activate_response.json()
            license_info = activation_data.get('license', {})
            print("✅ License activated successfully!")
            print(f"📊 License Type: {license_info.get('type', 'unknown')}")
            print(f"🔄 Active: {license_info.get('active', False)}")
            print(f"📅 Expires: {license_info.get('expires', 'unknown')}")
            return True
        else:
            print(f"❌ License activation failed: {activate_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ License activation error: {e}")
        return False

if __name__ == "__main__":
    success = test_license_workflow()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! License activation is working properly.")
        print("\n📝 Next steps:")
        print("1. Go to http://localhost:3000")
        print("2. Login with danielmanji38@gmail.com / newpassword123")
        print("3. Navigate to License page")
        print("4. Generate and activate a license")
    else:
        print("\n" + "=" * 50)
        print("❌ FAILED! There are still issues with license activation.")
        print("Check the error messages above for details.")