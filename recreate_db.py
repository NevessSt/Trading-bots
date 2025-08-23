#!/usr/bin/env python3
import sys
sys.path.append('backend')

from app import create_app
from db import db
from models import User, APIKey, Trade, Bot, Subscription

app = create_app()

with app.app_context():
    try:
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        print("Database recreated successfully!")
        
        # Test if APIKey table was created properly
        api_keys = APIKey.query.all()
        print(f"APIKey table working - found {len(api_keys)} records")
        
    except Exception as e:
        print(f"Error recreating database: {str(e)}")
        import traceback
        traceback.print_exc()