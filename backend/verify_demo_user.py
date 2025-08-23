#!/usr/bin/env python3
"""
Script to verify the demo user's email for testing login functionality
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import User
from db import db

def verify_demo_user():
    """Verify the demo user's email"""
    app = create_app()
    
    with app.app_context():
        # Find the demo user
        demo_user = User.find_by_email('demo@example.com')
        if not demo_user:
            print("Demo user not found! Please run create_demo_user.py first.")
            return
        
        if demo_user.is_verified:
            print("Demo user is already verified!")
            return
        
        try:
            # Verify the demo user
            demo_user.is_verified = True
            db.session.commit()
            
            print(f"Demo user verified successfully!")
            print(f"Email: {demo_user.email}")
            print(f"Username: {demo_user.username}")
            print(f"Verified: {demo_user.is_verified}")
            
        except Exception as e:
            print(f"Error verifying demo user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    verify_demo_user()