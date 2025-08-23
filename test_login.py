import requests
import json

# Test the backend login endpoint
url = "http://localhost:5000/api/auth/login"
data = {
    "email": "demo@example.com",
    "password": "demo123456"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        token = result.get('access_token')
        print(f"Login successful! Token: {token[:20]}...")
        
        # Test the performance endpoint with the token
        headers = {'Authorization': f'Bearer {token}'}
        perf_response = requests.get("http://localhost:5000/api/performance", headers=headers)
        print(f"Performance endpoint status: {perf_response.status_code}")
        print(f"Performance response: {perf_response.text}")
    else:
        print("Login failed!")
        
except Exception as e:
    print(f"Error: {e}")