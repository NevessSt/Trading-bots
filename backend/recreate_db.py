#!/usr/bin/env python3
"""
Recreate database with updated schema including license fields
"""

import os
import sys
from sqlalchemy import create_engine, text
from database import db
from app import create_app
from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.api_key import APIKey
from models.subscription import Subscription

def recreate_database():
    """Recreate the database with updated schema"""
    try:
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            # Drop all tables
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables with new schema
            print("Creating tables with updated schema...")
            db.create_all()
            
            print("Database recreated successfully!")
            
            # Create a demo user for testing
            print("Creating demo user...")
            demo_user = User(
                email='demo@example.com',
                username='demo',
                first_name='Demo',
                last_name='User',
                is_active=True,
                is_verified=True,
                role='user'
            )
            demo_user.set_password('demo123')
            
            db.session.add(demo_user)
            db.session.commit()
            
            print("Demo user created successfully!")
            print("Email: demo@example.com")
            print("Password: demo123")
            
    except Exception as e:
        print(f"Error recreating database: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    success = recreate_database()
    sys.exit(0 if success else 1)