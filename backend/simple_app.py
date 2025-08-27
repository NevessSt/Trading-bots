#!/usr/bin/env python3

import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from db import db

# Load environment variables
load_dotenv()

# Initialize extensions
migrate = Migrate()
jwt = JWTManager()

def create_app():
    """Lightweight application factory."""
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trading_bot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    
    # Enable CORS
    CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Import models after db initialization
    from models import User, Subscription, Trade, Bot, APIKey
    
    # Register basic routes
    register_basic_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_basic_routes(app):
    """Register essential routes only."""
    try:
        # Import and register auth routes
        from api.auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        
        # Import and register user routes
        from api.user_routes import user_bp
        app.register_blueprint(user_bp, url_prefix='/api/user')
        
        print("Auth and user routes registered successfully")
    except ImportError as e:
        print(f"Warning: Could not import routes: {e}")
    
    # Root route
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'Trading Bot API (Simple Mode)',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'user': '/api/user'
            }
        })
    
    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'message': 'Trading Bot API is running (Simple Mode)',
            'version': '1.0.0'
        })

def register_error_handlers(app):
    """Register error handlers."""
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting simple Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)