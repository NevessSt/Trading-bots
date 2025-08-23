#!/usr/bin/env python3
"""
Debug License Activation
This script helps debug license activation issues by testing the API directly.
"""

import sys
import os
import requests
import json

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from auth.license_manager import LicenseManager
from config.config import Config

def test_backend_license_generation():
    """Test license generation in backend"""
    print("\n🔧 Testing Backend License Generation...")
    print("="*50)
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        try:
            # Generate a test license
            license_key = LicenseManager.generate_license_key(
                license_type="enterprise",
                duration_days=365,
                user_email="danielmanji38@gmail.com"
            )
            
            if license_key:
                print(f"✅ License generated: {license_key[:50]}...")
                
                # Validate the license
                license_data, error = LicenseManager.validate_license_key(license_key)
                if license_data:
                    print(f"✅ License validation: SUCCESS")
                    print(f"📊 Type: {license_data['type']}")
                    return license_key
                else:
                    print(f"❌ License validation failed: {error}")
                    return None
            else:
                print("❌ Failed to generate license")
                return None
                
        except Exception as e:
            print(f"❌ Backend error: {str(e)}")
            return None

def test_api_endpoints(license_key):
    """Test API endpoints directly"""
    print("\n🌐 Testing API Endpoints...")
    print("="*50)
    
    base_url = "http://localhost:5000/api"
    email = "danielmanji38@gmail.com"
    password = "newpassword123"
    
    try:
        # Test login
        print("1️⃣ Testing login...")
        login_response = requests.post(f"{base_url}/auth/login", json={
            "email": email,
            "password": password
        }, timeout=10)
        
        print(f"Login status: {login_response.status_code}")
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        token = login_response.json().get('access_token')
        print(f"✅ Login successful, token: {token[:20]}...")
        
        # Test license status
        print("\n2️⃣ Testing license status...")
        headers = {'Authorization': f'Bearer {token}'}
        status_response = requests.get(f"{base_url}/license/status", headers=headers, timeout=10)
        
        print(f"Status check: {status_response.status_code}")
        if status_response.status_code == 200:
            current_license = status_response.json().get('license', {})
            print(f"✅ Current license: {current_license.get('type', 'unknown')}")
        else:
            print(f"⚠️ Status check failed: {status_response.text}")
        
        # Test license validation
        print("\n3️⃣ Testing license validation...")
        validate_response = requests.post(f"{base_url}/license/validate", 
            headers=headers,
            json={"license_key": license_key},
            timeout=10
        )
        
        print(f"Validation status: {validate_response.status_code}")
        if validate_response.status_code == 200:
            validation_data = validate_response.json()
            print(f"✅ Validation successful: {validation_data.get('valid', False)}")
        else:
            print(f"❌ Validation failed: {validate_response.text}")
        
        # Test license activation
        print("\n4️⃣ Testing license activation...")
        activate_response = requests.post(f"{base_url}/license/activate", 
            headers=headers,
            json={"license_key": license_key},
            timeout=10
        )
        
        print(f"Activation status: {activate_response.status_code}")
        print(f"Response headers: {dict(activate_response.headers)}")
        print(f"Response body: {activate_response.text}")
        
        if activate_response.status_code == 200:
            activation_data = activate_response.json()
            print(f"✅ Activation successful!")
            print(f"📊 New license: {activation_data.get('license', {}).get('type', 'unknown')}")
            return True
        else:
            print(f"❌ Activation failed: {activate_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Backend server not reachable")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout error: Request took too long")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def check_backend_server():
    """Check if backend server is running"""
    print("\n🔍 Checking Backend Server...")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        print(f"✅ Backend server is running (status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is not reachable")
        return False
    except Exception as e:
        print(f"⚠️ Backend server check failed: {str(e)}")
        return False

def main():
    """Main debugging function"""
    print("\n" + "="*60)
    print("🐛 LICENSE ACTIVATION DEBUGGER")
    print("="*60)
    
    # Check backend server
    if not check_backend_server():
        print("\n💡 Make sure the backend server is running with: python backend/app.py")
        return
    
    # Test backend license generation
    license_key = test_backend_license_generation()
    if not license_key:
        print("\n❌ Cannot proceed without a valid license key")
        return
    
    # Test API endpoints
    success = test_api_endpoints(license_key)
    
    if success:
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("The license activation should work in the frontend.")
        print("\n📋 Use this license key in the frontend:")
        print("-" * 60)
        print(license_key)
        print("-" * 60)
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED")
        print("Check the error messages above for debugging.")
        print("="*60)

if __name__ == "__main__":
    main()