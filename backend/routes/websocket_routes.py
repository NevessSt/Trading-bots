"""WebSocket management API routes."""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.logger import get_logger
from models import User
from db import db

logger = get_logger(__name__)

websocket_bp = Blueprint('websocket', __name__)

@websocket_bp.route('/info', methods=['GET'])
@jwt_required()
def get_websocket_info():
    """Get WebSocket connection information."""
    try:
        user_id = get_jwt_identity()
        
        # Get WebSocket service
        websocket_service = current_app.websocket_service
        realtime_service = current_app.realtime_service
        
        # Get connection status
        is_connected = websocket_service.is_user_connected(user_id)
        user_subscriptions = list(websocket_service.get_user_subscriptions(user_id))
        
        # Get active subscriptions stats
        active_subscriptions = realtime_service.get_active_subscriptions() if realtime_service else {}
        
        return jsonify({
            'status': 'success',
            'data': {
                'websocket_url': '/socket.io',
                'is_connected': is_connected,
                'user_subscriptions': user_subscriptions,
                'active_subscriptions': active_subscriptions,
                'connected_users': websocket_service.get_connected_users_count(),
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting WebSocket info: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@websocket_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def subscribe_to_symbol():
    """Subscribe to real-time price updates for a symbol."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        symbol = data.get('symbol', '').upper().strip()
        if not symbol:
            return jsonify({
                'status': 'error',
                'message': 'Symbol is required'
            }), 400
        
        # Get services
        realtime_service = current_app.realtime_service
        
        if not realtime_service:
            return jsonify({
                'status': 'error',
                'message': 'Real-time service not available'
            }), 503
        
        # Subscribe user to symbol
        success = realtime_service.subscribe_user_to_symbol(user_id, symbol)
        
        if success:
            # Get current price if available
            current_price = realtime_service.get_current_price(symbol)
            
            return jsonify({
                'status': 'success',
                'message': f'Successfully subscribed to {symbol}',
                'data': {
                    'symbol': symbol,
                    'current_price': current_price,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to subscribe to {symbol}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error subscribing to symbol: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@websocket_bp.route('/unsubscribe', methods=['POST'])
@jwt_required()
def unsubscribe_from_symbol():
    """Unsubscribe from real-time price updates for a symbol."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        symbol = data.get('symbol', '').upper().strip()
        if not symbol:
            return jsonify({
                'status': 'error',
                'message': 'Symbol is required'
            }), 400
        
        # Get services
        realtime_service = current_app.realtime_service
        
        if not realtime_service:
            return jsonify({
                'status': 'error',
                'message': 'Real-time service not available'
            }), 503
        
        # Unsubscribe user from symbol
        success = realtime_service.unsubscribe_user_from_symbol(user_id, symbol)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Successfully unsubscribed from {symbol}',
                'data': {
                    'symbol': symbol,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to unsubscribe from {symbol}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error unsubscribing from symbol: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@websocket_bp.route('/price/<symbol>', methods=['GET'])
@jwt_required()
def get_current_price(symbol):
    """Get current price for a symbol."""
    try:
        symbol = symbol.upper().strip()
        
        # Get services
        realtime_service = current_app.realtime_service
        
        if not realtime_service:
            return jsonify({
                'status': 'error',
                'message': 'Real-time service not available'
            }), 503
        
        # Get current price
        price_data = realtime_service.get_current_price(symbol)
        
        if price_data:
            return jsonify({
                'status': 'success',
                'data': price_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Price data not available for {symbol}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting current price for {symbol}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@websocket_bp.route('/price-history/<symbol>', methods=['GET'])
@jwt_required()
def get_price_history(symbol):
    """Get price history for a symbol."""
    try:
        symbol = symbol.upper().strip()
        limit = request.args.get('limit', 100, type=int)
        
        # Validate limit
        if limit < 1 or limit > 1000:
            return jsonify({
                'status': 'error',
                'message': 'Limit must be between 1 and 1000'
            }), 400
        
        # Get services
        realtime_service = current_app.realtime_service
        
        if not realtime_service:
            return jsonify({
                'status': 'error',
                'message': 'Real-time service not available'
            }), 503
        
        # Get price history
        history = realtime_service.get_price_history(symbol, limit)
        
        return jsonify({
            'status': 'success',
            'data': {
                'symbol': symbol,
                'history': history,
                'count': len(history),
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting price history for {symbol}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@websocket_bp.route('/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio_data():
    """Get real-time portfolio data for the current user."""
    try:
        user_id = get_jwt_identity()
        
        # Get services
        realtime_service = current_app.realtime_service
        
        if not realtime_service:
            return jsonify({
                'status': 'error',
                'message': 'Real-time service not available'
            }), 503
        
        # Force portfolio update and get data
        realtime_service.force_portfolio_update(user_id)
        portfolio_data = realtime_service.get_portfolio_data(user_id)
        
        if portfolio_data:
            return jsonify({
                'status': 'success',
                'data': portfolio_data
            })
        else:
            return jsonify({
                'status': 'success',
                'data': {
                    'user_id': user_id,
                    'total_pnl': 0,
                    'total_value': 0,
                    'positions': {},
                    'active_bots': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting portfolio data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@websocket_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_websocket_stats():
    """Get WebSocket connection statistics."""
    try:
        # Get services
        websocket_service = current_app.websocket_service
        realtime_service = current_app.realtime_service
        
        # Get statistics
        stats = {
            'connected_users': websocket_service.get_connected_users_count(),
            'total_connections': len(websocket_service.connected_users),
            'active_subscriptions': realtime_service.get_active_subscriptions() if realtime_service else {},
            'subscribed_symbols': list(realtime_service.subscribed_symbols) if realtime_service else [],
            'active_streams': len(realtime_service.active_streams) if realtime_service else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@websocket_bp.route('/broadcast-test', methods=['POST'])
@jwt_required()
def broadcast_test_message():
    """Broadcast a test message (admin only)."""
    try:
        user_id = get_jwt_identity()
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        data = request.get_json()
        message = data.get('message', 'Test message from admin')
        
        # Get WebSocket service
        websocket_service = current_app.websocket_service
        
        # Broadcast test message
        websocket_service.socketio.emit('test_message', {
            'message': message,
            'from': 'admin',
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)
        
        return jsonify({
            'status': 'success',
            'message': 'Test message broadcasted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error broadcasting test message: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500