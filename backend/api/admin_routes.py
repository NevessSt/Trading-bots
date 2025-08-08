from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Import models
from db import db
from models import User, Trade, Bot, Subscription

# Create blueprint
admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """Get all users with pagination"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    skip = (page - 1) * limit
    
    users = User.list_all(limit=limit, skip=skip)
    
    # Remove sensitive information
    safe_users = []
    for user in users:
        safe_user = {
            'id': str(user['_id']),
            'email': user['email'],
            'username': user['username'],
            'role': user.get('role', 'user'),
            'isActive': user.get('is_active', True),
            'createdAt': user.get('created_at'),
            'lastLogin': user.get('last_login')
        }
        safe_users.append(safe_user)
    
    return jsonify({
        'users': safe_users,
        'pagination': {
            'page': page,
            'limit': limit
        }
    }), 200

@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_details(user_id):
    """Get detailed information about a specific user"""
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's trading statistics
    total_trades = Trade.count({'user_id': user_id})
    total_pnl = Trade.get_profit_loss(user_id)
    
    user_details = {
        'id': str(user['_id']),
        'email': user['email'],
        'username': user['username'],
        'firstName': user.get('firstName', ''),
        'lastName': user.get('lastName', ''),
        'role': user.get('role', 'user'),
        'isActive': user.get('is_active', True),
        'settings': user.get('settings', {}),
        'createdAt': user.get('created_at'),
        'updatedAt': user.get('updated_at'),
        'lastLogin': user.get('last_login'),
        'statistics': {
            'totalTrades': total_trades,
            'totalPnL': total_pnl
        }
    }
    
    return jsonify(user_details), 200

@admin_bp.route('/users/<user_id>/activate', methods=['POST'])
@jwt_required()
@admin_required
def activate_user(user_id):
    """Activate a user account"""
    success = User.update(user_id, {'is_active': True})
    
    if success:
        return jsonify({'message': 'User activated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to activate user'}), 500

@admin_bp.route('/users/<user_id>/deactivate', methods=['POST'])
@jwt_required()
@admin_required
def deactivate_user(user_id):
    """Deactivate a user account"""
    success = User.update(user_id, {'is_active': False})
    
    if success:
        return jsonify({'message': 'User deactivated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to deactivate user'}), 500

@admin_bp.route('/users/<user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_role(user_id):
    """Update user role"""
    data = request.get_json()
    
    if 'role' not in data:
        return jsonify({'error': 'Role is required'}), 400
    
    if data['role'] not in ['user', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400
    
    success = User.update(user_id, {'role': data['role']})
    
    if success:
        return jsonify({'message': 'User role updated successfully'}), 200
    else:
        return jsonify({'error': 'Failed to update user role'}), 500

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_system_stats():
    """Get system-wide statistics"""
    try:
        # Get user statistics
        users_collection = User.get_collection()
        total_users = users_collection.count_documents({})
        active_users = users_collection.count_documents({'is_active': True})
        
        # Get trade statistics
        trades_collection = Trade.get_collection()
        total_trades = trades_collection.count_documents({})
        
        # Get trades from last 24 hours
        yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = trades_collection.count_documents({
            'timestamp': {'$gte': yesterday}
        })
        
        # Calculate total volume (mock data for now)
        total_volume = 1000000.00  # This would be calculated from actual trades
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users
            },
            'trades': {
                'total': total_trades,
                'today': today_trades,
                'totalVolume': total_volume
            },
            'system': {
                'uptime': '99.9%',  # Mock data
                'version': '1.0.0',
                'lastUpdate': datetime.utcnow().isoformat()
            }
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/trades', methods=['GET'])
@jwt_required()
@admin_required
def get_all_trades():
    """Get all trades with pagination and filtering"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    skip = (page - 1) * limit
    
    # Build filters
    filters = {}
    
    if request.args.get('user_id'):
        filters['user_id'] = request.args.get('user_id')
    
    if request.args.get('symbol'):
        filters['symbol'] = request.args.get('symbol')
    
    if request.args.get('type'):
        filters['type'] = request.args.get('type')
    
    # Date range filtering
    if request.args.get('start_date'):
        start_date = datetime.fromisoformat(request.args.get('start_date'))
        filters['timestamp'] = {'$gte': start_date}
    
    if request.args.get('end_date'):
        end_date = datetime.fromisoformat(request.args.get('end_date'))
        if 'timestamp' in filters:
            filters['timestamp']['$lte'] = end_date
        else:
            filters['timestamp'] = {'$lte': end_date}
    
    trades = Trade.find(filters, limit=limit, skip=skip)
    total = Trade.count(filters)
    
    return jsonify({
        'trades': trades,
        'pagination': {
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }
    }), 200