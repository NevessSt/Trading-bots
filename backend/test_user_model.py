#!/usr/bin/env python3
"""
Test script to check User model functionality
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import User
from db import db

def test_user_model():
    """Test User model operations"""
    app = create_app()
    
    with app.app_context():
        try:
            # Test creating a user
            print("Testing User model creation...")
            test_user = User(
                email='test@example.com',
                username='testuser',
                password='testpass123',
                first_name='Test',
                last_name='User'
            )
            print("User model created successfully")
            
            # Test querying (this is where the error occurs)
            print("Testing User.find_by_email...")
            existing_user = User.find_by_email('demo@example.com')
            if existing_user:
                print(f"Found user: {existing_user.email}")
            else:
                print("No user found with email demo@example.com")
                
        except Exception as e:
            print(f"Error testing User model: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_user_model()