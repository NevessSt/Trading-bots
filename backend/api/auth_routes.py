from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
import re

# Import database and models
from db import db
from models import User

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'username']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate email format
    email_regex = r'^[\w\.-]+@([\w\-]+\.)+[A-Z]{2,}$'
    if not re.match(email_regex, data['email'], re.IGNORECASE):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if user already exists
    if User.find_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 409
    
    if User.find_by_username(data['username']):
        return jsonify({'error': 'Username already taken'}), 409
    
    try:
        # Create new user using the model's create_user method
        user_data = {
            'email': data['email'],
            'username': data['username'],
            'password': data['password'],
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name')
        }
        
        new_user = User.create_user(user_data)
        
        # Generate access token
        tokens = new_user.generate_tokens()
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': tokens['access_token'],
            'user': new_user.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    
    # Validate required fields
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Authenticate user
    user = User.authenticate(data['username'], data['password'])
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate access token
    tokens = user.generate_tokens()
    
    return jsonify({
        'message': 'Login successful',
        'access_token': tokens['access_token'],
        'refresh_token': tokens.get('refresh_token', tokens['access_token']),
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user profile"""
    current_user_id = get_jwt_identity()
    
    user = User.find_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(current_user_id))
    
    return jsonify({
        'access_token': access_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout a user (client-side implementation)"""
    # JWT tokens are stateless, so we don't need to do anything server-side
    # The client should remove the token from storage
    
    return jsonify({
        'message': 'Logout successful'
    }), 200