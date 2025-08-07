import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from dotenv import load_dotenv
from config.config import get_config

# Import routes
from api.auth_routes import auth_bp
from api.user_routes import user_bp
from api.trading_routes import trading_bp
from api.admin_routes import admin_bp
from api.backtest_routes import backtest_bp
from api.api_key_routes import api_key_bp
from api.notification_routes import notification_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure app
config_name = os.environ.get('FLASK_ENV', 'development')
config = get_config(config_name)
app.config.from_object(config)

# Enable CORS
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Initialize MongoDB
mongo_client = MongoClient(app.config['MONGO_URI'])
db = mongo_client.get_database()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(trading_bp, url_prefix='/api/trading')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(backtest_bp, url_prefix='/api/backtest')
app.register_blueprint(api_key_bp, url_prefix='/api/keys')
app.register_blueprint(notification_bp, url_prefix='/api/notifications')

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