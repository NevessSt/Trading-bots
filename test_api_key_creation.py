#!/usr/bin/env python3
"""
Test script to verify API key creation is working correctly
"""

import requests
import json

def test_api_key_creation():
    """Test that API key creation works with Enterprise license"""
    print("\n" + "="*60)
    print("🔑 TESTING API KEY CREATION")
    print("="*60)
    
    base_url = "http://localhost:5000/api"
    email = "danielmanji38@gmail.com"
    password = "newpassword123"
    
    try:
        # Step 1: Login
        print("\n1️⃣ Logging in...")
        login_response = requests.post(f"{base_url}/auth/login", json={
            "email": email,
            "password": password
        }, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        token = login_response.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        print(f"✅ Login successful")
        
        # Step 2: Check license status
        print("\n2️⃣ Checking license status...")
        status_response = requests.get(f"{base_url}/license/status", headers=headers, timeout=10)
        
        if status_response.status_code != 200:
            print(f"❌ License status check failed: {status_response.text}")
            return False
        
        license_data = status_response.json().get('license', {})
        print(f"✅ License Type: {license_data.get('type', 'unknown')}")
        print(f"✅ API Key Management Feature: {license_data.get('features', {}).get('api_key_management', False)}")
        
        # Step 3: Test API key creation
        print("\n3️⃣ Testing API key creation...")
        import time
        api_key_data = {
            "key_name": f"Test Binance Key {int(time.time())}",
            "exchange": "binance",
            "api_key": "test_api_key_12345678901234567890",
            "api_secret": "test_api_secret_12345678901234567890",
            "testnet": True,
            "permissions": ["read", "trade"],
            "validate_keys": False
        }
        
        create_response = requests.post(f"{base_url}/api-keys/", 
            headers=headers,
            json=api_key_data,
            timeout=10
        )
        
        print(f"📊 Response Status: {create_response.status_code}")
        print(f"📊 Response Body: {create_response.text}")
        
        if create_response.status_code == 201:
            response_data = create_response.json()
            print(f"✅ API key created successfully!")
            print(f"   Key ID: {response_data.get('key_id')}")
            print(f"   Key Name: {response_data.get('key_name')}")
            print(f"   Exchange: {response_data.get('exchange')}")
            return True
        else:
            print(f"❌ API key creation failed")
            try:
                error_data = create_response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw error: {create_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key_creation()
    if success:
        print("\n🎉 API key creation is working!")
        print("📝 You can now add API keys through the frontend.")
    else:
        print("\n❌ API key creation test failed. Check the logs above.")