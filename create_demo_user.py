#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import app, db
from backend.models.user import User
from werkzeug.security import generate_password_hash

def create_demo_user():
    with app.app_context():
        # Check if demo user already exists
        existing_user = User.query.filter_by(email='demo@example.com').first()
        if existing_user:
            print("Demo user already exists!")
            print(f"Email: demo@example.com")
            print(f"Password: demo123")
            return
        
        # Create demo user
        demo_user = User(
            email='demo@example.com',
            password_hash=generate_password_hash('demo123'),
            is_verified=True,
            notification_settings='{}'
        )
        
        db.session.add(demo_user)
        db.session.commit()
        
        print("Demo user created successfully!")
        print(f"Email: demo@example.com")
        print(f"Password: demo123")

if __name__ == '__main__':
    create_demo_user()