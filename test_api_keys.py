#!/usr/bin/env python3
import sys
sys.path.append('backend')

from app import create_app
from models import APIKey, User
from db import db

app = create_app()

with app.app_context():
    try:
        # Test if APIKey table exists and can be queried
        print("Testing APIKey model...")
        api_keys = APIKey.query.all()
        print(f"Found {len(api_keys)} API keys in database")
        
        # Test if we can get a specific user's API keys
        user = User.query.filter_by(email='demo@example.com').first()
        if user:
            print(f"Demo user ID: {user.id}")
            user_api_keys = APIKey.query.filter_by(user_id=user.id).all()
            print(f"Demo user has {len(user_api_keys)} API keys")
        else:
            print("Demo user not found")
            
    except Exception as e:
        print(f"Error testing APIKey model: {str(e)}")
        import traceback
        traceback.print_exc()