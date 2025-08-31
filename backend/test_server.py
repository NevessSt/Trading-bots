#!/usr/bin/env python3
"""
Simple test server to check if Flask can start without complex services
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from db import db

# Create simple Flask app
app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trading_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')

# Initialize extensions
CORS(app)
db.init_app(app)
jwt = JWTManager(app)

# Simple health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Simple test server is running'
    })

# Simple test login endpoint
@app.route('/api/auth/login', methods=['POST'])
def test_login():
    """Simple test login endpoint"""
    data = request.get_json()
    print(f"DEBUG: Received login data: {data}")
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    print(f"DEBUG: username={username}, email={email}, password={password}")
    
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    if not username and not email:
        return jsonify({'error': 'Username or email is required'}), 400
    
    # Simple test credentials - accept both username and email
    if (username == 'test' or email == 'test@example.com') and password == 'test':
        return jsonify({
            'message': 'Login successful',
            'token': 'test-token-123',
            'user': {'id': 1, 'username': username or email}
        }), 200
    
    # Accept user's actual credentials
    if email == 'danielmanji38@gmail.com' and password == 'newpassword123':
        return jsonify({
            'message': 'Login successful',
            'user': {'username': username, 'id': 1},
            'token': 'test-token-123'
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Simple login test route
@app.route('/api/auth/test', methods=['GET'])
def auth_test():
    return jsonify({
        'status': 'success',
        'message': 'Auth routes are accessible'
    })

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Database error: {e}")
    
    print("Starting simple test server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)