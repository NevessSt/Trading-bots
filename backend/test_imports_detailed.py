#!/usr/bin/env python3
"""
Test imports from app.py one by one to identify the problematic import
"""

import sys
import traceback
from datetime import datetime

def test_import(description, import_statement):
    """Test a single import statement"""
    print(f"Testing: {description}")
    try:
        exec(import_statement)
        print(f"✅ {description}: OK")
        return True
    except Exception as e:
        print(f"❌ {description}: FAILED - {str(e)}")
        traceback.print_exc()
        return False

def main():
    print("=== Detailed Import Test ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test basic imports first
    imports_to_test = [
        ("os", "import os"),
        ("datetime.timedelta", "from datetime import timedelta"),
        ("flask", "from flask import Flask, jsonify"),
        ("flask_cors", "from flask_cors import CORS"),
        ("flask_jwt_extended", "from flask_jwt_extended import JWTManager"),
        ("flask_migrate", "from flask_migrate import Migrate"),
        ("dotenv", "from dotenv import load_dotenv"),
        ("db module", "from db import db"),
    ]
    
    print("=== Testing Basic Imports ===")
    for desc, stmt in imports_to_test:
        if not test_import(desc, stmt):
            print(f"\n❌ Failed at basic import: {desc}")
            return
        print()
    
    print("\n=== Testing Model Imports ===")
    model_imports = [
        ("User model", "from models.user import User"),
        ("Subscription model", "from models.subscription import Subscription"),
        ("Trade model", "from models.trade import Trade"),
        ("Bot model", "from models.bot import Bot"),
        ("APIKey model", "from models.api_key import APIKey"),
        ("All models at once", "from models import User, Subscription, Trade, Bot, APIKey"),
    ]
    
    for desc, stmt in model_imports:
        if not test_import(desc, stmt):
            print(f"\n❌ Failed at model import: {desc}")
            return
        print()
    
    print("\n=== Testing Route Imports ===")
    route_imports = [
        ("auth_routes", "from api.auth_routes import auth_bp"),
        ("user_routes", "from api.user_routes import user_bp"),
        ("trading_routes", "from api.trading_routes import trading_bp"),
        ("admin_routes", "from api.admin_routes import admin_bp"),
        ("backtest_routes", "from api.backtest_routes import backtest_bp"),
        ("api_key_routes", "from api.api_key_routes import api_key_bp"),
        ("notification_routes", "from api.notification_routes import notification_bp"),
        ("license_routes", "from api.license_routes import license_bp"),
        ("billing_routes", "from api.billing_routes import billing_bp"),
    ]
    
    for desc, stmt in route_imports:
        if not test_import(desc, stmt):
            print(f"\n❌ Failed at route import: {desc}")
            return
        print()
    
    print("\n🎉 All imports successful!")
    print("The issue might be in the app creation or execution logic.")

if __name__ == '__main__':
    main()