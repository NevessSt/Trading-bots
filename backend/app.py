import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from dotenv import load_dotenv
from db import db
from services.notification_service import NotificationService

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
        
        # Binance API Configuration
        app.config['BINANCE_API_KEY'] = os.environ.get('BINANCE_API_KEY')
        app.config['BINANCE_API_SECRET'] = os.environ.get('BINANCE_API_SECRET')
        app.config['BINANCE_TESTNET'] = os.environ.get('BINANCE_TESTNET', 'True').lower() == 'true'
        
        # SMTP Configuration for email verification
        app.config['SMTP_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', '587'))
        app.config['SMTP_USERNAME'] = os.environ.get('SMTP_USERNAME')
        app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD')
        app.config['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # Enable CORS
    CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins=['http://localhost:3000'], async_mode='threading')
    
    # Initialize WebSocket service
    from services.websocket_service import WebSocketService
    websocket_service = WebSocketService(socketio)
    
    # Initialize Notification service
    notification_service = NotificationService()
    # Initialize SMTP settings from app config
    notification_service.initialize_smtp(
        smtp_server=app.config.get('SMTP_SERVER'),
        smtp_port=app.config.get('SMTP_PORT'),
        username=app.config.get('SMTP_USERNAME'),
        password=app.config.get('SMTP_PASSWORD'),
        from_email=app.config.get('SMTP_USERNAME')
    )
    
    # Store services in app context for access in other modules
    app.socketio = socketio
    app.websocket_service = websocket_service
    app.notification_service = notification_service
    
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

        from api.billing_routes import billing_bp
        from api.support_routes import support_bp
        from api.test_routes import test_bp
        from api.dashboard_routes import dashboard_bp
        from api.pro_dashboard_routes import pro_dashboard_bp
        from api.license_routes import license_bp
        from api.connection_test_routes import connection_test_bp
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(user_bp, url_prefix='/api/user')
        app.register_blueprint(trading_bp, url_prefix='/api/trading')
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        app.register_blueprint(backtest_bp, url_prefix='/api/backtest')
        app.register_blueprint(api_key_bp, url_prefix='/api/api-keys')
        app.register_blueprint(notification_bp, url_prefix='/api/notifications')

        app.register_blueprint(billing_bp, url_prefix='/api/billing')
        app.register_blueprint(support_bp, url_prefix='/api/support')
        app.register_blueprint(test_bp, url_prefix='/api/test')
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        app.register_blueprint(pro_dashboard_bp, url_prefix='/')
        app.register_blueprint(license_bp, url_prefix='/api/license')
        app.register_blueprint(connection_test_bp, url_prefix='/api/connection')
    except ImportError as e:
        print(f"Warning: Could not import some routes: {e}")
        print("Starting with basic routes only...")
    
    # Root route
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'Trading Bot API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'user': '/api/user',
                'trading': '/api',
                'admin': '/api/admin'
            }
        })
    
    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Trading Bot API is running'
        })


def register_error_handlers(app):
    """Register error handlers."""
    from flask_jwt_extended.exceptions import JWTExtendedException
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        print(f"500 Error: {error}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exceptions(error):
        print(f"JWT Error: {error}")
        return jsonify({'error': str(error)}), 401

# Create app instance for development
app = create_app()

if __name__ == '__main__':
    # Initialize trading engine
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Run with SocketIO support
    app.socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)