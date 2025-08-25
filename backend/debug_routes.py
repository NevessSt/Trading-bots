#!/usr/bin/env python3
"""Debug script to check if routes are properly registered."""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def main():
    """Check if routes are registered."""
    try:
        # Create app with test config
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'JWT_SECRET_KEY': 'test-jwt-secret',
            'WTF_CSRF_ENABLED': False,
        }
        
        app = create_app(config)
        
        print("\n=== All Routes ===")
        for rule in app.url_map.iter_rules():
            print(f"{rule.methods} {rule.rule}")
        
        print("\n=== Trading Routes ===")
        trading_routes = [rule for rule in app.url_map.iter_rules() if 'trading' in str(rule.rule)]
        for rule in trading_routes:
            print(f"{rule.methods} {rule.rule}")
            
        if not trading_routes:
            print("No trading routes found!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()