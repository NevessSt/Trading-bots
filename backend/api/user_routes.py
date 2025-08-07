from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

# Import models
from models.user import User

# Create blueprint
user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Remove sensitive information
    user_data = {
        'id': str(user['_id']),
        'email': user['email'],
        'username': user['username'],
        'firstName': user.get('firstName', ''),
        'lastName': user.get('lastName', ''),
        'role': user.get('role', 'user'),
        'settings': user.get('settings', {}),
        'createdAt': user.get('created_at'),
        'updatedAt': user.get('updated_at')
    }
    
    return jsonify(user_data), 200

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Allowed fields to update
    allowed_fields = ['firstName', 'lastName', 'username']
    update_data = {}
    
    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]
    
    # Validate username if provided
    if 'username' in update_data:
        existing_user = User.find_by_username(update_data['username'])
        if existing_user and str(existing_user['_id']) != user_id:
            return jsonify({'error': 'Username already taken'}), 409
    
    if not update_data:
        return jsonify({'error': 'No valid fields to update'}), 400
    
    # Update user
    success = User.update(user_id, update_data)
    
    if success:
        return jsonify({'message': 'Profile updated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to update profile'}), 500

@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['currentPassword', 'newPassword']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Get current user
    user = User.find_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify current password
    if not check_password_hash(user['password'], data['currentPassword']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password
    if len(data['newPassword']) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long'}), 400
    
    # Hash new password
    hashed_password = generate_password_hash(data['newPassword'])
    
    # Update password
    success = User.update(user_id, {'password': hashed_password})
    
    if success:
        return jsonify({'message': 'Password changed successfully'}), 200
    else:
        return jsonify({'error': 'Failed to change password'}), 500

@user_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get user settings"""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    settings = user.get('settings', {
        'notifications': {
            'email': True,
            'telegram': False,
            'telegramChatId': ''
        },
        'trading': {
            'maxDailyLoss': 5.0,
            'maxTradeSize': 10.0,
            'autoTrade': False
        },
        'apiKeys': {
            'binanceApiKey': '',
            'binanceApiSecret': ''
        }
    })
    
    return jsonify(settings), 200

@user_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update user settings"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get current user
    user = User.find_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get current settings or initialize with defaults
    current_settings = user.get('settings', {})
    
    # Update settings
    if 'notifications' in data:
        if 'notifications' not in current_settings:
            current_settings['notifications'] = {}
        current_settings['notifications'].update(data['notifications'])
    
    if 'trading' in data:
        if 'trading' not in current_settings:
            current_settings['trading'] = {}
        current_settings['trading'].update(data['trading'])
    
    if 'apiKeys' in data:
        if 'apiKeys' not in current_settings:
            current_settings['apiKeys'] = {}
        current_settings['apiKeys'].update(data['apiKeys'])
    
    # Update user settings
    success = User.update(user_id, {'settings': current_settings})
    
    if success:
        return jsonify({'message': 'Settings updated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to update settings'}), 500

@user_bp.route('/account-summary', methods=['GET'])
@jwt_required()
def get_account_summary():
    """Get account summary including balance and performance"""
    user_id = get_jwt_identity()
    
    try:
        # This would typically integrate with the trading engine
        # For now, return mock data that matches frontend expectations
        summary = {
            'totalBalance': 10000.00,
            'availableBalance': 8500.00,
            'totalEquity': 10250.00,
            'dailyPnL': 125.50,
            'totalPnL': 250.00,
            'assets': [
                {'symbol': 'BTC', 'amount': 0.5, 'value': 25000.00},
                {'symbol': 'ETH', 'amount': 2.0, 'value': 4000.00},
                {'symbol': 'USDT', 'amount': 1000.00, 'value': 1000.00}
            ]
        }
        
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500