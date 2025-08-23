#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing Bot model import and query...")
    
    # Test database connection
    from extensions import db
    print("✓ Database extension imported successfully")
    
    # Test Bot model import
    from models.bot import Bot
    print("✓ Bot model imported successfully")
    
    # Test app context
    from app import create_app
    app = create_app()
    print("✓ App created successfully")
    
    with app.app_context():
        print("✓ App context established")
        
        # Test database connection
        try:
            db.engine.execute('SELECT 1')
            print("✓ Database connection working")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
        
        # Test Bot model query
        try:
            bots = Bot.query.filter_by(user_id=1).all()
            print(f"✓ Bot query successful, found {len(bots)} bots")
        except Exception as e:
            print(f"✗ Bot query failed: {e}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()