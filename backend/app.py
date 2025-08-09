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


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Configure app
    if config_name:
        if isinstance(config_name, dict):
            # Handle dictionary configuration (for testing)
            app.config.update(config_name)
        else:
            # Handle object configuration
            app.config.from_object(config_name)
    else:
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
    
    # Register routes
    register_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_routes(app):
    """Register application routes."""
    # Import routes
    try:
        from api.auth_routes import auth_bp
        from api.user_routes import user_bp
        from api.trading_routes import trading_bp
        from api.admin_routes import admin_bp
        from api.backtest_routes import backtest_bp
        from api.api_key_routes import api_key_bp
        from api.notification_routes import notification_bp
        from api.license_routes import license_bp
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(user_bp, url_prefix='/api/user')
        app.register_blueprint(trading_bp, url_prefix='/api')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(backtest_bp, url_prefix='/api/backtest')
        app.register_blueprint(api_key_bp, url_prefix='/api/api-keys')
        app.register_blueprint(notification_bp, url_prefix='/api/notifications')
        app.register_blueprint(license_bp, url_prefix='/api/license')
    except ImportError as e:
        print(f"Warning: Could not import some routes: {e}")
        print("Starting with basic routes only...")
    
    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Trading Bot API is running'
        })


def register_error_handlers(app):
    """Register error handlers."""
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Internal server error'}), 500

# Create app instance for development
app = create_app()

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)