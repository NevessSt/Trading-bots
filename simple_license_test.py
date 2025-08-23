#!/usr/bin/env python3
"""
Simple License Test
Quick test to check license activation without complex debugging.
"""

import requests
import json

def test_backend_health():
    """Test if backend is responding"""
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        print(f"Backend health: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        return False
    except Exception as e:
        print(f"Backend health check failed: {e}")
        return False

def test_login():
    """Test login"""
    try:
        response = requests.post("http://localhost:5000/api/auth/login", 
            json={
                "email": "danielmanji38@gmail.com",
                "password": "newpassword123"
            },
            timeout=10
        )
        print(f"Login status: {response.status_code}")
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"Got token: {token[:20] if token else 'None'}...")
            return token
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_license_activation(token, license_key):
    """Test license activation"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post("http://localhost:5000/api/license/activate",
            json={"license_key": license_key},
            headers=headers,
            timeout=10
        )
        print(f"Activation status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Activation error: {e}")
        return False

def main():
    print("=== Simple License Test ===")
    
    # Test backend health
    if not test_backend_health():
        print("Backend is not responding")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("Login failed")
        return
    
    # Use the license key from previous generation
    license_key = input("Enter license key to test: ").strip()
    if not license_key:
        print("No license key provided")
        return
    
    # Test activation
    success = test_license_activation(token, license_key)
    if success:
        print("✅ License activation successful!")
    else:
        print("❌ License activation failed")

if __name__ == "__main__":
    main()