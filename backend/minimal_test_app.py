#!/usr/bin/env python3
"""
Minimal Flask app to test basic functionality
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Creating minimal Flask app...")

# Create Flask app
app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Enable CORS
CORS(app, origins=['http://localhost:3000'])

print("Flask app configured")

# Health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Minimal Trading Bot API is running'
    })

# Root route
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'Minimal Trading Bot API',
        'version': '1.0.0',
        'status': 'running'
    })

print("Routes registered")

if __name__ == '__main__':
    print("Starting Flask development server...")
    print("Server will be available at: http://localhost:5000")
    print("Health check: http://localhost:5000/api/health")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True, use_reloader=False)