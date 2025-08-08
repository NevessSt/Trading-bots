import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://trading_user:trading_password123@localhost:5432/trading_bot_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour

# Enable CORS
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Import models after db initialization
from models import User, Subscription, Trade, Bot

# Import routes
try:
    from api.auth_routes import auth_bp
    from api.user_routes import user_bp
    from api.trading_routes import trading_bp
    from api.admin_routes import admin_bp
    from api.backtest_routes import backtest_bp
    from api.api_key_routes import api_key_bp
    from api.notification_routes import notification_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(trading_bp, url_prefix='/api/trading')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(backtest_bp, url_prefix='/api/backtest')
    app.register_blueprint(api_key_bp, url_prefix='/api/keys')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
except ImportError as e:
    print(f"Warning: Could not import some routes: {e}")
    print("Starting with basic routes only...")

# Create database tables
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'environment': os.environ.get('FLASK_ENV', 'development')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)