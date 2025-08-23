from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

# Create test blueprint
test_bp = Blueprint('test', __name__)

@test_bp.route('/test-jwt', methods=['GET'])
@jwt_required()
def test_jwt():
    """Test JWT functionality"""
    try:
        user_id = get_jwt_identity()
        return jsonify({
            'success': True,
            'user_id': str(user_id),
            'message': 'JWT working correctly'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@test_bp.route('/test-simple', methods=['GET'])
def test_simple():
    """Simple test without JWT"""
    return jsonify({
        'success': True,
        'message': 'Simple route working'
    }), 200