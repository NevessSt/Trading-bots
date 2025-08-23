#!/usr/bin/env python3
"""
Test script to verify Enterprise license features are working correctly
"""

import requests
import json

def test_enterprise_features():
    """Test that Enterprise license features are properly recognized"""
    print("\n" + "="*60)
    print("🧪 TESTING ENTERPRISE LICENSE FEATURES")
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
        print(f"✅ License Active: {license_data.get('active', False)}")
        
        # Step 3: Check specific Enterprise features
        print("\n3️⃣ Checking Enterprise features...")
        features_to_check = [
            'bot_creation',
            'bot_control', 
            'bot_management',
            'api_key_management',
            'live_trading',
            'advanced_strategies',
            'api_access',
            'custom_indicators'
        ]
        
        features = license_data.get('features', {})
        print(f"\n📋 Available features:")
        
        all_enterprise_features_enabled = True
        for feature in features_to_check:
            enabled = features.get(feature, False)
            status_icon = "✅" if enabled else "❌"
            print(f"   {status_icon} {feature}: {enabled}")
            
            if not enabled:
                all_enterprise_features_enabled = False
        
        # Step 4: Test individual feature checks
        print("\n4️⃣ Testing individual feature access...")
        for feature in features_to_check:
            feature_response = requests.post(f"{base_url}/license/check-feature",
                headers=headers,
                json={"feature": feature},
                timeout=10
            )
            
            if feature_response.status_code == 200:
                feature_data = feature_response.json()
                has_access = feature_data.get('has_access', False)
                status_icon = "✅" if has_access else "❌"
                print(f"   {status_icon} API check for {feature}: {has_access}")
            else:
                print(f"   ⚠️  Could not check {feature} via API")
        
        # Summary
        print("\n" + "="*60)
        if all_enterprise_features_enabled:
            print("🎉 SUCCESS! All Enterprise features are properly enabled!")
            print("✅ The 'This feature is not available in your enterprise license' error should be resolved.")
            return True
        else:
            print("❌ Some Enterprise features are still disabled.")
            print("⚠️  The license feature mismatch issue may still exist.")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_enterprise_features()
    if success:
        print("\n🔥 Ready to test in the frontend!")
        print("📝 Instructions:")
        print("   1. Go to http://localhost:3000")
        print("   2. Login with danielmanji38@gmail.com / newpassword123")
        print("   3. Try creating bots, managing API keys, etc.")
        print("   4. You should no longer see the 'feature not available' error")
    else:
        print("\n❌ Enterprise features test failed. Check the logs above.")