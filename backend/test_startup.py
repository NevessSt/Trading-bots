#!/usr/bin/env python3
"""
Simple test script to debug Flask app startup
"""

import sys
import os
from datetime import datetime

print(f"=== Flask Startup Test ===")
print(f"Timestamp: {datetime.now()}")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")
print()

try:
    print("Step 1: Loading environment...")
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
    
    print("Step 2: Importing Flask components...")
    from flask import Flask
    print("✅ Flask imported")
    
    print("Step 3: Importing app module...")
    from app import app
    print("✅ App module imported")
    print(f"App name: {app.name}")
    print(f"App config keys: {list(app.config.keys())[:10]}...")
    
    print("Step 4: Testing app creation...")
    with app.app_context():
        print("✅ App context works")
    
    print("Step 5: Starting Flask development server...")
    print("🚀 Starting server on http://localhost:5000")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)