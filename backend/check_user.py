#!/usr/bin/env python3
"""
Script to check if user exists and verify account details
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import User
from db import db

def check_user():
    """Check if user exists and show details"""
    app = create_app()
    
    with app.app_context():
        try:
            # Find user by email
            user = User.find_by_email('danielmanji38@gmail.com')
            
            if user:
                print(f"✅ User found!")
                print(f"ID: {user.id}")
                print(f"Email: {user.email}")
                print(f"Username: {user.username}")
                print(f"Is Active: {user.is_active}")
                print(f"Is Verified: {user.is_verified}")
                print(f"Role: {user.role}")
                print(f"Created: {user.created_at}")
                
                # Test password check
                test_password = input("\nEnter password to test: ")
                if user.check_password(test_password):
                    print("✅ Password is correct!")
                else:
                    print("❌ Password is incorrect!")
            else:
                print("❌ User not found!")
                
                # List all users
                print("\nAll users in database:")
                all_users = User.query.all()
                for u in all_users:
                    print(f"  - ID: {u.id}, Email: {u.email}, Username: {u.username}")
                
        except Exception as e:
            print(f"Error checking user: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_user()