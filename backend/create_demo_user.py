#!/usr/bin/env python3
"""
Script to create a demo user for testing login functionality
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import User
from db import db

def create_demo_user():
    """Create a demo user for testing"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create demo user with required parameters
            demo_user = User(
                email='demo@example.com',
                username='demo',
                password='demo123456',
                first_name='Demo',
                last_name='User',
                is_active=True,
                is_verified=True,
                role='user'
            )
            
            db.session.add(demo_user)
            db.session.commit()
            
            print(f"Demo user created successfully!")
            print(f"Email: demo@example.com")
            print(f"Password: demo123456")
            print(f"User ID: {demo_user.id}")
            
        except Exception as e:
            print(f"Error creating demo user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_demo_user()