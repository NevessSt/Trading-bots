#!/usr/bin/env python3
"""
Frontend License Debug
This script simulates the exact frontend license activation process
"""

import requests
import json

def test_frontend_license_flow():
    """Test the exact same flow as the frontend"""
    print("🔍 Frontend License Activation Debug")
    print("=" * 50)
    
    # Step 1: Test backend health
    print("\n1️⃣ Testing backend health...")
    try:
        health_response = requests.get("http://localhost:5000/api/health", timeout=5)
        print(f"✅ Backend health: {health_response.status_code}")
        if health_response.status_code != 200:
            print(f"❌ Backend not healthy: {health_response.text}")
            return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False
    
    # Step 2: Login (same as frontend)
    print("\n2️⃣ Testing login...")
    try:
        login_response = requests.post(
            "http://localhost:5000/api/auth/login",
            json={
                "email": "danielmanji38@gmail.com",
                "password": "newpassword123"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Login status: {login_response.status_code}")
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        token = login_response.json().get('access_token')
        print(f"✅ Got token: {token[:20]}...")
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 3: Test license status (what frontend does first)
    print("\n3️⃣ Testing license status...")
    try:
        status_response = requests.get(
            "http://localhost:5000/api/license/status",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"Status check: {status_response.status_code}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Current license: {status_data.get('license', {}).get('type', 'unknown')}")
        else:
            print(f"⚠️  Status check failed: {status_response.text}")
    except Exception as e:
        print(f"⚠️  Status check error: {e}")
    
    # Step 4: Test license validation (what frontend does when typing)
    license_key = '{"type":"enterprise","created":"2025-08-22T15:05:57.610385","expires":"2026-08-22T15:05:57.610402","features":{"max_bots":-1,"live_trading":true,"advanced_strategies":true,"api_access":true,"priority_support":true,"custom_indicators":true},"user_email":"danielmanji38@gmail.com"}|75a091027c610ca5'
    
    print("\n4️⃣ Testing license validation...")
    try:
        validate_response = requests.post(
            "http://localhost:5000/api/license/validate",
            json={"license_key": license_key},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"Validation status: {validate_response.status_code}")
        if validate_response.status_code == 200:
            validation_data = validate_response.json()
            print(f"✅ Validation successful: {validation_data.get('valid', False)}")
        else:
            print(f"❌ Validation failed: {validate_response.text}")
    except Exception as e:
        print(f"❌ Validation error: {e}")
    
    # Step 5: Test license activation (the main issue)
    print("\n5️⃣ Testing license activation (EXACT frontend call)...")
    try:
        # This is the EXACT same call the frontend makes
        activate_response = requests.post(
            "http://localhost:5000/api/license/activate",
            json={"license_key": license_key},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"Activation status: {activate_response.status_code}")
        print(f"Response headers: {dict(activate_response.headers)}")
        print(f"Response body: {activate_response.text}")
        
        if activate_response.status_code == 200:
            activation_data = activate_response.json()
            print(f"\n🎉 SUCCESS! License activation works!")
            print(f"Message: {activation_data.get('message', 'N/A')}")
            license_info = activation_data.get('license', {})
            print(f"License type: {license_info.get('type', 'N/A')}")
            print(f"License active: {license_info.get('active', False)}")
            return True
        else:
            print(f"\n❌ ACTIVATION FAILED")
            print(f"Status: {activate_response.status_code}")
            print(f"Error: {activate_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Activation error: {e}")
        return False
    
    # Step 6: Test what happens after activation
    print("\n6️⃣ Testing post-activation status...")
    try:
        final_status_response = requests.get(
            "http://localhost:5000/api/license/status",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        if final_status_response.status_code == 200:
            final_status = final_status_response.json()
            license_info = final_status.get('license', {})
            print(f"✅ Final license status:")
            print(f"   Type: {license_info.get('type', 'N/A')}")
            print(f"   Active: {license_info.get('active', False)}")
            print(f"   Expires: {license_info.get('expires', 'N/A')}")
        else:
            print(f"⚠️  Final status check failed: {final_status_response.text}")
    except Exception as e:
        print(f"⚠️  Final status error: {e}")

def main():
    success = test_frontend_license_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 FRONTEND LICENSE ACTIVATION SHOULD WORK!")
        print("\n📝 If it still doesn't work in the browser:")
        print("1. Open browser developer tools (F12)")
        print("2. Go to Network tab")
        print("3. Try license activation")
        print("4. Check for any failed network requests")
        print("5. Look for CORS errors in console")
    else:
        print("❌ FRONTEND LICENSE ACTIVATION HAS ISSUES")
        print("Check the error messages above for debugging.")
    print("=" * 50)

if __name__ == "__main__":
    main()