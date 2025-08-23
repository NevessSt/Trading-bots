#!/usr/bin/env python3
"""
Test script for license API functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_EMAIL = "danielmanji38@gmail.com"
TEST_PASSWORD = "newpassword123"
TEST_LICENSE_KEY = '{"type":"premium","created":"2025-08-22T14:00:00.679181","expires":"2026-08-22T14:00:00.679199","features":{"max_bots":10,"live_trading":true,"advanced_strategies":true,"api_access":true,"priority_support":true,"custom_indicators":true},"user_email":"danielmanji38@gmail.com"}|569736d77ad5b930'

def login():
    """Login and get access token"""
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def test_license_status(token):
    """Test license status endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/license/status", headers=headers)
    print(f"\n--- License Status Test ---")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        license_data = data.get('license', {})
        print(f"✓ License status retrieved successfully")
        print(f"License Type: {license_data.get('type', 'N/A')}")
        print(f"Is Active: {license_data.get('active', False)}")
        print(f"Features: {json.dumps(license_data.get('features', {}), indent=2)}")
        return license_data
    else:
        print(f"✗ License status failed: {response.text}")
        return None

def test_license_activation(token):
    """Test license activation endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    activation_data = {
        "license_key": TEST_LICENSE_KEY
    }
    
    response = requests.post(f"{BASE_URL}/api/license/activate", json=activation_data, headers=headers)
    print(f"\n--- License Activation Test ---")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        license_data = data.get('license', {})
        print(f"✓ License activation successful")
        print(f"Message: {data.get('message', 'N/A')}")
        print(f"License Type: {license_data.get('type', 'N/A')}")
        return True
    else:
        print(f"✗ License activation failed: {response.text}")
        return False

def test_license_deactivation(token):
    """Test license deactivation endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BASE_URL}/api/license/deactivate", headers=headers)
    print(f"\n--- License Deactivation Test ---")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ License deactivation successful")
        print(f"Message: {data.get('message', 'N/A')}")
        return True
    else:
        print(f"✗ License deactivation failed: {response.text}")
        return False

def test_feature_check(token, feature_name="live_trading"):
    """Test feature check endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    feature_data = {"feature": feature_name}
    
    response = requests.post(f"{BASE_URL}/api/license/check-feature", json=feature_data, headers=headers)
    print(f"\n--- Feature Check Test ({feature_name}) ---")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Feature check successful")
        print(f"Feature '{feature_name}' enabled: {data.get('has_access', False)}")
        print(f"Current license: {data.get('current_license', 'N/A')}")
        return data.get('has_access', False)
    else:
        print(f"✗ Feature check failed: {response.text}")
        return False

def main():
    """Main test function"""
    print("=== License API Test Suite ===")
    print(f"Testing against: {BASE_URL}")
    print(f"Test user: {TEST_EMAIL}")
    print(f"Test license key: {TEST_LICENSE_KEY}")
    
    # Step 1: Login
    token = login()
    if not token:
        print("\n✗ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Step 2: Check initial license status
    initial_status = test_license_status(token)
    
    # Step 3: Test license activation
    activation_success = test_license_activation(token)
    
    # Step 4: Check license status after activation
    if activation_success:
        post_activation_status = test_license_status(token)
    
    # Step 5: Test feature checking
    test_feature_check(token, "live_trading")
    test_feature_check(token, "api_access")
    test_feature_check(token, "custom_indicators")
    
    # Step 6: Test license deactivation
    deactivation_success = test_license_deactivation(token)
    
    # Step 7: Check final license status
    if deactivation_success:
        final_status = test_license_status(token)
    
    print("\n=== Test Summary ===")
    print(f"Login: {'✓' if token else '✗'}")
    print(f"License Activation: {'✓' if activation_success else '✗'}")
    print(f"License Deactivation: {'✓' if deactivation_success else '✗'}")
    print("\nLicense API testing completed!")

if __name__ == "__main__":
    main()