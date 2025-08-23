#!/usr/bin/env python3
"""
Test Specific License Key
"""

import requests
import json

def main():
    print("=== Testing Specific License Key ===")
    
    # The license key from the previous generation
    license_key = '{"type":"enterprise","created":"2025-08-22T15:05:57.610385","expires":"2026-08-22T15:05:57.610402","features":{"max_bots":-1,"live_trading":true,"advanced_strategies":true,"api_access":true,"priority_support":true,"custom_indicators":true},"user_email":"danielmanji38@gmail.com"}|75a091027c610ca5'
    
    # Test backend health
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        print(f"✅ Backend health: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return
    
    # Test login
    try:
        response = requests.post("http://localhost:5000/api/auth/login", 
            json={
                "email": "danielmanji38@gmail.com",
                "password": "newpassword123"
            },
            timeout=10
        )
        print(f"✅ Login status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Login failed: {response.text}")
            return
        
        token = response.json().get('access_token')
        print(f"✅ Got token: {token[:20]}...")
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test license activation
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post("http://localhost:5000/api/license/activate",
            json={"license_key": license_key},
            headers=headers,
            timeout=10
        )
        print(f"\n📋 License activation:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 SUCCESS! License activation works in backend.")
            print("\n📝 Now test in frontend:")
            print("1. Go to http://localhost:3000")
            print("2. Login with danielmanji38@gmail.com / newpassword123")
            print("3. Go to License page")
            print("4. Paste this license key:")
            print("-" * 60)
            print(license_key)
            print("-" * 60)
        else:
            print(f"\n❌ License activation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Activation error: {e}")

if __name__ == "__main__":
    main()