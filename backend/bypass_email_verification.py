#!/usr/bin/env python3
"""
Development Email Verification Bypass

This script provides a temporary bypass for email verification during development.
It can automatically verify users or provide manual verification tokens.
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import db
from models.user import User

# Load environment variables
load_dotenv()

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trading_bot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def list_unverified_users():
    """List all unverified users"""
    users = User.query.filter_by(is_verified=False).all()
    if not users:
        print("No unverified users found.")
        return []
    
    print("\nUnverified users:")
    print("-" * 50)
    for i, user in enumerate(users, 1):
        print(f"{i}. Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Created: {user.created_at}")
        if hasattr(user, 'verification_token') and user.verification_token:
            print(f"   Token: {user.verification_token[:20]}...")
        print()
    
    return users

def verify_user_by_email(email):
    """Manually verify a user by email"""
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"❌ User with email {email} not found.")
        return False
    
    if user.is_verified:
        print(f"✅ User {email} is already verified.")
        return True
    
    try:
        user.is_verified = True
        if hasattr(user, 'verification_token'):
            user.verification_token = None
        if hasattr(user, 'verification_token_expires'):
            user.verification_token_expires = None
        
        db.session.commit()
        print(f"✅ User {email} has been manually verified.")
        return True
    except Exception as e:
        print(f"❌ Failed to verify user {email}: {str(e)}")
        db.session.rollback()
        return False

def verify_all_users():
    """Verify all unverified users"""
    users = User.query.filter_by(is_verified=False).all()
    if not users:
        print("No unverified users found.")
        return
    
    verified_count = 0
    for user in users:
        try:
            user.is_verified = True
            if hasattr(user, 'verification_token'):
                user.verification_token = None
            if hasattr(user, 'verification_token_expires'):
                user.verification_token_expires = None
            verified_count += 1
        except Exception as e:
            print(f"❌ Failed to verify {user.email}: {str(e)}")
    
    try:
        db.session.commit()
        print(f"✅ Successfully verified {verified_count} users.")
    except Exception as e:
        print(f"❌ Failed to save changes: {str(e)}")
        db.session.rollback()

def get_verification_token(email):
    """Get verification token for a user"""
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"❌ User with email {email} not found.")
        return None
    
    if user.is_verified:
        print(f"✅ User {email} is already verified.")
        return None
    
    if hasattr(user, 'verification_token') and user.verification_token:
        print(f"Verification token for {email}:")
        print(f"Token: {user.verification_token}")
        print(f"Verification URL: http://localhost:3000/verify-email?token={user.verification_token}")
        return user.verification_token
    else:
        print(f"❌ No verification token found for {email}.")
        return None

def main():
    """Main interactive menu"""
    app = create_app()
    
    with app.app_context():
        print("=== Email Verification Bypass Tool ===")
        print("This tool helps with email verification during development.")
        print()
        
        while True:
            print("\nOptions:")
            print("1. List unverified users")
            print("2. Verify user by email")
            print("3. Verify all users")
            print("4. Get verification token for user")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                list_unverified_users()
            
            elif choice == '2':
                email = input("Enter user email to verify: ").strip()
                if email:
                    verify_user_by_email(email)
            
            elif choice == '3':
                confirm = input("Are you sure you want to verify ALL unverified users? (y/N): ").strip().lower()
                if confirm == 'y':
                    verify_all_users()
            
            elif choice == '4':
                email = input("Enter user email to get token: ").strip()
                if email:
                    get_verification_token(email)
            
            elif choice == '5':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()