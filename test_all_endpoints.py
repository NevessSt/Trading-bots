import requests
import json

# Test all endpoints that were failing
BASE_URL = "http://localhost:5000"

def test_login():
    """Test login and get token"""
    login_data = {
        "email": "demo@example.com",
        "password": "demo123456"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_endpoints_with_auth(token):
    """Test all endpoints with authentication"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        "/api/api-keys",
        "/api/trades", 
        "/api/performance",
        "/api/bots"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"{endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"  Error: {response.text}")
        except Exception as e:
            print(f"{endpoint}: Exception - {str(e)}")
        print()

if __name__ == "__main__":
    print("Testing all endpoints...")
    token = test_login()
    if token:
        print(f"Login successful! Testing endpoints...\n")
        test_endpoints_with_auth(token)
    else:
        print("Login failed, cannot test endpoints")