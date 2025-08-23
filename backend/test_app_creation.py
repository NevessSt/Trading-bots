#!/usr/bin/env python3
"""
Test the exact app creation process from app.py to identify the hang
"""

import os
from datetime import datetime, timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from db import db

print("=== App Creation Test ===")
print(f"Timestamp: {datetime.now()}")
print()

# Load environment variables
print("Step 1: Loading environment variables...")
load_dotenv()
print("✅ Environment loaded")

# Initialize extensions
print("Step 2: Initializing extensions...")
migrate = Migrate()
jwt = JWTManager()
print("✅ Extensions initialized")

def create_test_app():
    """Test version of create_app function"""
    print("Step 3: Creating Flask app...")
    app = Flask(__name__)
    print("✅ Flask app created")
    
    print("Step 4: Configuring app...")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trading_bot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    
    # SMTP Configuration for email verification
    app.config['SMTP_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', '587'))
    app.config['SMTP_USERNAME'] = os.environ.get('SMTP_USERNAME')
    app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD')
    app.config['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    print("✅ App configured")
    
    print("Step 5: Enabling CORS...")
    CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
    print("✅ CORS enabled")
    
    print("Step 6: Initializing extensions with app...")
    db.init_app(app)
    print("✅ Database initialized")
    migrate.init_app(app, db)
    print("✅ Migration initialized")
    jwt.init_app(app)
    print("✅ JWT initialized")
    
    print("Step 7: Importing models...")
    from models import User, Subscription, Trade, Bot, APIKey
    print("✅ Models imported")
    
    print("Step 8: Registering routes...")
    register_test_routes(app)
    print("✅ Routes registered")
    
    return app

def register_test_routes(app):
    """Register basic routes for testing"""
    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Trading Bot API is running'
        })
    
    # Root route
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'Trading Bot API',
            'version': '1.0.0',
            'status': 'running'
        })

def main():
    try:
        print("Creating app...")
        app = create_test_app()
        print("✅ App created successfully")
        
        print("\nStep 9: Testing app context...")
        with app.app_context():
            print("✅ App context works")
            
            print("Step 10: Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
        
        print("\nStep 11: Starting Flask server...")
        print("🚀 Server starting on http://localhost:5000")
        
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV', 'development') == 'development'
        app.run(host='127.0.0.1', port=port, debug=debug, use_reloader=False)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()