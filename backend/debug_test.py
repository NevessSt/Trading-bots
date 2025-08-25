#!/usr/bin/env python3
"""Debug script to test the trading API endpoint."""

import os
import sys
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from db import db
from models.user import User

def main():
    """Test the trading API endpoint."""
    try:
        # Create app with test config
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'JWT_SECRET_KEY': 'test-jwt-secret',
            'WTF_CSRF_ENABLED': False,
        }
        
        app = create_app(config)
        
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Create test user
            user = User(
                email='test@example.com',
                username='testuser',
                password='password123',
                is_verified=True
            )
            db.session.add(user)
            db.session.commit()
            
            # Create test client
            client = app.test_client()
            
            # Login to get token
            login_response = client.post('/api/auth/login', json={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            print(f"Login response status: {login_response.status_code}")
            print(f"Login response data: {login_response.get_json()}")
            
            if login_response.status_code == 200:
                token = login_response.get_json()['access_token']
                headers = {'Authorization': f'Bearer {token}'}
                
                # Test the bots endpoint
                bots_response = client.get('/api/trading/bots', headers=headers)
                
                print(f"\nBots endpoint status: {bots_response.status_code}")
                print(f"Bots endpoint data: {bots_response.get_json()}")
                print(f"Bots endpoint response: {bots_response.get_data(as_text=True)}")
            else:
                print("Login failed!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()