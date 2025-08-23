import requests
import json

def test_bots_route():
    try:
        # Login first
        login_data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        login_response = requests.post(
            'http://localhost:5000/api/auth/login',
            json=login_data
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test bots route
        bots_response = requests.get(
            'http://localhost:5000/api/bots',
            headers=headers
        )
        
        print(f"Bots route status: {bots_response.status_code}")
        print(f"Response: {bots_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

def test_debug_route():
    try:
        response = requests.get('http://localhost:5000/api/debug-bot')
        print(f"Debug route status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    print("Testing debug route...")
    test_debug_route()
    print("\nTesting bots route...")
    test_bots_route()