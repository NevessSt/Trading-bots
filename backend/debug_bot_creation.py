#!/usr/bin/env python3

import json
from app import create_app
from tests.conftest import test_user
from db import db
from models.user import User

# Create app and test client
app = create_app()
client = app.test_client()

with app.app_context():
    # Create tables
    db.create_all()
    
    # Create test user if it doesn't exist
    user = User.query.filter_by(username='testuser').first()
    if not user:
        user = User(
            email='test@example.com',
            username='testuser',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
    
    # Login to get token
    login_response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    print(f"Login status: {login_response.status_code}")
    print(f"Login response: {login_response.get_json()}")
    
    if login_response.status_code == 200:
        token = login_response.json['access_token']
        auth_headers = {'Authorization': f'Bearer {token}'}
        
        # Test bot creation
        bot_data = {
            'name': 'Test Grid Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'config': {
                'grid_size': 10,
                'price_range': [45000, 55000],
                'investment_amount': 1000,
                'grid_spacing': 0.5
            }
        }
        
        bot_response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=auth_headers)
        
        print(f"Bot creation status: {bot_response.status_code}")
        print(f"Bot creation response: {bot_response.get_json()}")
    else:
        print("Login failed, cannot test bot creation")