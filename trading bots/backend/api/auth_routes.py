from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import re

# Import database and models
from models.user import User

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
    
    # Create new user
    hashed_password = generate_password_hash(data['password'])
    
    new_user = {
        'email': data['email'],
        'username': data['username'],
        'password': hashed_password,
        'role': 'user',
        'is_active': True,
        'created_at': datetime.utcnow(),
        'settings': {
            'notifications': {
                'email': True,
                'telegram': False
            },
            'risk_management': {
                'max_daily_loss': 5.0,  # Percentage
                'max_trade_size': 10.0  # Percentage of portfolio
            }
        }
    }
    
    user_id = User.create(new_user)
    
    if not user_id:
        return jsonify({'error': 'Failed to create user'}), 500
    
    # Generate access token
    access_token = create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(days=1)
    )
    
    return jsonify({
        'message': 'User registered successfully',
        'access_token': access_token,
        'user': {
            'id': str(user_id),
            'email': data['email'],
            'username': data['username'],
            'role': 'user'
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    
    # Validate required fields
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Find user by email
    user = User.find_by_email(data['email'])
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user['is_active']:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Generate access token
    access_token = create_access_token(
        identity=str(user['_id']),
        expires_delta=timedelta(days=1)
    )
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'username': user['username'],
            'role': user['role']
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user profile"""
    current_user_id = get_jwt_identity()
    
    user = User.find_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': str(user['_id']),
        'email': user['email'],
        'username': user['username'],
        'role': user['role'],
        'settings': user.get('settings', {}),
        'created_at': user.get('created_at')
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    
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