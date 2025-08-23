#!/usr/bin/env python3
"""
Backend Diagnostic Script

This script helps diagnose issues with the backend server startup.
"""

import os
import sys
import traceback
from datetime import datetime

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    imports_to_test = [
        ('os', 'os'),
        ('flask', 'from flask import Flask, jsonify'),
        ('flask_cors', 'from flask_cors import CORS'),
        ('flask_jwt_extended', 'from flask_jwt_extended import JWTManager'),
        ('flask_migrate', 'from flask_migrate import Migrate'),
        ('dotenv', 'from dotenv import load_dotenv'),
        ('db', 'from db import db'),
    ]
    
    failed_imports = []
    
    for name, import_statement in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {name}: OK")
        except Exception as e:
            print(f"❌ {name}: FAILED - {str(e)}")
            failed_imports.append((name, str(e)))
    
    return len(failed_imports) == 0  # Return True if no failed imports

def test_environment():
    """Test environment variables"""
    print("\nTesting environment variables...")
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded")
    except Exception as e:
        print(f"❌ Failed to load .env file: {str(e)}")
        return False
    
    # Check critical environment variables
    env_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'SMTP_SERVER',
        'SMTP_USERNAME',
        'SMTP_PASSWORD'
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            if 'PASSWORD' in var or 'SECRET' in var:
                print(f"✅ {var}: Set (hidden)")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set")
    
    return True

def test_database():
    """Test database connection"""
    print("\nTesting database...")
    
    try:
        from db import db
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trading_bot.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            # Try to create tables
            db.create_all()
            print("✅ Database connection: OK")
            print("✅ Database tables: Created/Verified")
            return True
            
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test Flask app creation"""
    print("\nTesting Flask app creation...")
    
    try:
        from app import create_app
        
        app = create_app()
        print("✅ Flask app creation: OK")
        print(f"✅ App name: {app.name}")
        print(f"✅ Debug mode: {app.debug}")
        
        # Test basic route
        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Health endpoint: OK")
            else:
                print(f"⚠️  Health endpoint returned: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app creation failed: {str(e)}")
        traceback.print_exc()
        return False

def test_port_availability():
    """Test if port 5000 is available"""
    print("\nTesting port availability...")
    
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("⚠️  Port 5000 is already in use")
            return False
        else:
            print("✅ Port 5000 is available")
            return True
            
    except Exception as e:
        print(f"❌ Port test failed: {str(e)}")
        return False

def main():
    """Run all diagnostic tests"""
    print("=== Backend Diagnostic Report ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Run all tests
    tests = [
        ('Import Test', test_imports),
        ('Environment Test', test_environment),
        ('Database Test', test_database),
        ('App Creation Test', test_app_creation),
        ('Port Availability Test', test_port_availability)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("DIAGNOSTIC SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The backend should be able to start.")
        print("Try running: python app.py")
    else:
        print("\n⚠️  Some tests failed. Please address the issues above.")
        print("\nCommon solutions:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check your .env file configuration")
        print("3. Ensure no other process is using port 5000")
        print("4. Check database permissions and file paths")

if __name__ == '__main__':
    main()