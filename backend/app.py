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
from utils.logging_config import setup_logging
from utils.monitoring import MetricsCollector
from utils.sentry_config import init_sentry
from middleware.enhanced_security import EnhancedSecurityMiddleware
from celery_app import celery_app

# Load environment variables
load_dotenv()

# Initialize logging and monitoring
logger, monitoring_handler = setup_logging(enable_monitoring=True)
metrics_collector = MetricsCollector()

# Connect monitoring handler to metrics collector
if monitoring_handler:
    monitoring_handler.set_metrics_collector(metrics_collector)

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
        
        # Notification Configuration
        app.config['NOTIFICATION_EMAIL_ENABLED'] = os.environ.get('NOTIFICATION_EMAIL_ENABLED', 'True').lower() == 'true'
        app.config['NOTIFICATION_TELEGRAM_ENABLED'] = os.environ.get('NOTIFICATION_TELEGRAM_ENABLED', 'False').lower() == 'true'
        app.config['NOTIFICATION_PUSH_ENABLED'] = os.environ.get('NOTIFICATION_PUSH_ENABLED', 'False').lower() == 'true'
        
        # Telegram Configuration
        app.config['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN')
        app.config['TELEGRAM_API_URL'] = 'https://api.telegram.org/bot{}/sendMessage'
        
        # Firebase Push Notification Configuration
        app.config['FIREBASE_SERVER_KEY'] = os.environ.get('FIREBASE_SERVER_KEY')
        app.config['FCM_URL'] = 'https://fcm.googleapis.com/fcm/send'
    
    # Enable CORS
    CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
    
    # Initialize Sentry for error tracking
    init_sentry(app)
    
    # Initialize enhanced security middleware
enhanced_security = EnhancedSecurityMiddleware()
enhanced_security.init_app(app)

# Initialize enhanced integration
from utils.enhanced_integration import EnhancedTradingBotIntegration
enhanced_integration = EnhancedTradingBotIntegration()
enhanced_integration.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Initialize monitoring middleware
    from middleware.monitoring_middleware import MonitoringMiddleware
    from middleware.sentry_middleware import SentryMiddleware
    monitoring_middleware = MonitoringMiddleware(app)
    sentry_middleware = SentryMiddleware(app)
    
    # Store metrics collector in app context
    app.metrics_collector = metrics_collector
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins=['http://localhost:3000'], async_mode='threading')
    
    # Initialize WebSocket service
    from services.websocket_service import WebSocketService
    websocket_service = WebSocketService(socketio)
    
    # Initialize Real-time Data service
    from services.realtime_data_service import RealTimeDataService
    realtime_service = RealTimeDataService(websocket_service)
    
    # Connect services
    websocket_service.set_realtime_service(realtime_service)
    
    # Initialize Notification service with WebSocket integration
    notification_service = NotificationService(websocket_service)
    
    # Initialize Celery with Flask app context
    init_celery(app, celery_app)
    
    # Store services in app context for access in other modules
    app.socketio = socketio
    app.websocket_service = websocket_service
    app.realtime_service = realtime_service
    app.notification_service = notification_service
    app.celery = celery_app
    
    # Import models after db initialization
    from models import User, Subscription, Trade, Bot, APIKey
    from models.notification import NotificationPreference, NotificationLog, NotificationTemplate
    
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
        from routes.admin_routes import admin_bp  # Updated to use new admin routes
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
        from api.strategy_management_routes import strategy_management_bp
        from api.strategy_marketplace_routes import strategy_marketplace_bp
        from routes.monitoring import monitoring_bp
        from routes.async_tasks import async_tasks_bp
        from routes.websocket_routes import websocket_bp
        from routes.bot_control import bot_control_bp
        from routes.oauth_routes import oauth_bp  # Add OAuth routes
        from routes.analytics import analytics_bp  # Add analytics routes
        from routes.exchange_routes import exchange_bp  # Add exchange routes
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(user_bp, url_prefix='/api/user')
        app.register_blueprint(trading_bp, url_prefix='/api/trading')
        app.register_blueprint(admin_bp)  # Admin routes already have /api/admin prefix
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
        app.register_blueprint(strategy_management_bp)
        app.register_blueprint(strategy_marketplace_bp)
        app.register_blueprint(monitoring_bp)
        app.register_blueprint(async_tasks_bp)
        app.register_blueprint(websocket_bp, url_prefix='/api/websocket')
        app.register_blueprint(bot_control_bp)
        app.register_blueprint(oauth_bp)  # OAuth routes already have /api/oauth prefix
        app.register_blueprint(analytics_bp)  # Analytics routes already have /api/analytics prefix
        app.register_blueprint(exchange_bp, url_prefix='/api')  # Exchange routes
        
        # Import and register optimization blueprint
        from routes.optimization import optimization_bp
        app.register_blueprint(optimization_bp)
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

def init_celery(app, celery):
    """Initialize Celery with Flask app context."""
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

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
        
        # Start real-time data service
        try:
            app.realtime_service.start()
            print("Real-time data service started successfully")
        except Exception as e:
            print(f"Error starting real-time data service: {e}")

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Run with SocketIO support
    app.socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)