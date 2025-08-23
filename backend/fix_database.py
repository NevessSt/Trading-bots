#!/usr/bin/env python3
"""
Script to fix database schema by recreating all tables
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from db import db

# Import all models to ensure they're registered
from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.subscription import Subscription
from models.api_key import APIKey

def fix_database():
    """Fix database by dropping and recreating all tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Dropping all existing tables...")
            db.drop_all()
            print("Creating all tables with correct schema...")
            db.create_all()
            print("Database schema fixed successfully!")
            
            # Verify the User table has all required columns
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('users')
            print("\nUser table columns:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
                
        except Exception as e:
            print(f"Error fixing database: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    fix_database()