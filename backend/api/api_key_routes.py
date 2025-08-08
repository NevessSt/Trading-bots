from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from db import db
from models import User, APIKey
from utils.logger import logger
from utils.security import security_manager, rate_limit
from bot_engine import TradingEngine
import re

api_key_bp = Blueprint('api_keys', __name__, url_prefix='/api/keys')

@api_key_bp.route('/add', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_minutes=60)
def add_api_key():
    """Add or update user's exchange API keys"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['exchange', 'api_key', 'api_secret']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        exchange = data['exchange'].lower()
        api_key = data['api_key'].strip()
        api_secret = data['api_secret'].strip()
        testnet = data.get('testnet', True)  # Default to testnet for safety
        
        # Validate exchange
        supported_exchanges = ['binance', 'coinbase', 'kraken', 'bitfinex']
        if exchange not in supported_exchanges:
            return jsonify({'error': f'Unsupported exchange. Supported: {supported_exchanges}'}), 400
        
        # Validate API key format (basic validation)
        if not security_manager.validate_api_key_format(api_key, exchange):
            return jsonify({'error': 'Invalid API key format'}), 400
        
        if len(api_secret) < 10:
            return jsonify({'error': 'API secret too short'}), 400
        
        # Test API key validity
        try:
            trading_engine = TradingEngine(api_key=api_key, api_secret=api_secret, testnet=testnet)
            
            # Try to fetch account info to validate keys
            balance = trading_engine.get_account_balance(user_id)
            if not balance:
                return jsonify({'error': 'Invalid API credentials or insufficient permissions'}), 400
            
        except Exception as e:
            logger.warning(f"API key validation failed for user {user_id}: {str(e)}")
            return jsonify({'error': 'Invalid API credentials or connection failed'}), 400
        
        # Encrypt API credentials
        encrypted_key = security_manager.encrypt_api_key(api_key)
        encrypted_secret = security_manager.encrypt_api_key(api_secret)
        
        # Update user's API keys
        api_keys_data = {
            f'api_keys.{exchange}': {
                'api_key': encrypted_key,
                'api_secret': encrypted_secret,
                'testnet': testnet,
                'created_at': datetime.utcnow(),
                'last_used': None,
                'is_active': True
            }
        }
        
        success = User.update(user_id, api_keys_data)
        
        if success:
            logger.info(f"User {user_id} added API keys for {exchange} (testnet: {testnet})")
            logger.log_security_event('api_key_added', user_id, {'exchange': exchange, 'testnet': testnet})
            
            return jsonify({
                'success': True,
                'message': f'API keys for {exchange} added successfully',
                'testnet': testnet
            })
        else:
            return jsonify({'error': 'Failed to save API keys'}), 500
            
    except Exception as e:
        logger.error(f"Error adding API keys for user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_key_bp.route('/list', methods=['GET'])
@jwt_required()
def list_api_keys():
    """List user's configured API keys (without revealing the actual keys)"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        api_keys = user.get('api_keys', {})
        
        # Return safe information about API keys
        safe_keys = {}
        for exchange, key_data in api_keys.items():
            if isinstance(key_data, dict):
                safe_keys[exchange] = {
                    'exchange': exchange,
                    'testnet': key_data.get('testnet', True),
                    'created_at': key_data.get('created_at'),
                    'last_used': key_data.get('last_used'),
                    'is_active': key_data.get('is_active', True),
                    'api_key_preview': key_data.get('api_key', '')[:8] + '...' if key_data.get('api_key') else 'Not set'
                }
        
        return jsonify({
            'success': True,
            'api_keys': safe_keys
        })
        
    except Exception as e:
        logger.error(f"Error listing API keys for user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_key_bp.route('/remove/<exchange>', methods=['DELETE'])
@jwt_required()
@rate_limit(max_requests=10, window_minutes=60)
def remove_api_key(exchange):
    """Remove API keys for a specific exchange"""
    try:
        user_id = get_jwt_identity()
        exchange = exchange.lower()
        
        # Check if user has API keys for this exchange
        user = User.find_by_id(user_id)
        if not user or not user.get('api_keys', {}).get(exchange):
            return jsonify({'error': f'No API keys found for {exchange}'}), 404
        
        # Remove API keys
        success = User.update(user_id, {f'api_keys.{exchange}': None})
        
        if success:
            logger.info(f"User {user_id} removed API keys for {exchange}")
            logger.log_security_event('api_key_removed', user_id, {'exchange': exchange})
            
            return jsonify({
                'success': True,
                'message': f'API keys for {exchange} removed successfully'
            })
        else:
            return jsonify({'error': 'Failed to remove API keys'}), 500
            
    except Exception as e:
        logger.error(f"Error removing API keys for user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_key_bp.route('/test/<exchange>', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_minutes=60)
def test_api_key(exchange):
    """Test API key connection for a specific exchange"""
    try:
        user_id = get_jwt_identity()
        exchange = exchange.lower()
        
        # Get user's API keys
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        api_keys = user.get('api_keys', {}).get(exchange)
        if not api_keys:
            return jsonify({'error': f'No API keys configured for {exchange}'}), 404
        
        # Decrypt API keys
        try:
            api_key = security_manager.decrypt_api_key(api_keys['api_key'])
            api_secret = security_manager.decrypt_api_key(api_keys['api_secret'])
            testnet = api_keys.get('testnet', True)
        except Exception as e:
            logger.error(f"Failed to decrypt API keys for user {user_id}: {str(e)}")
            return jsonify({'error': 'Failed to decrypt API keys'}), 500
        
        # Test connection
        try:
            trading_engine = TradingEngine(api_key=api_key, api_secret=api_secret, testnet=testnet)
            
            # Test basic functionality
            balance = trading_engine.get_account_balance(user_id)
            symbols = trading_engine.get_available_symbols()[:5]  # Get first 5 symbols
            
            # Update last used timestamp
            User.update(user_id, {f'api_keys.{exchange}.last_used': datetime.utcnow()})
            
            logger.info(f"API key test successful for user {user_id} on {exchange}")
            
            return jsonify({
                'success': True,
                'message': 'API connection successful',
                'test_results': {
                    'balance_check': 'OK' if balance else 'Failed',
                    'symbols_check': 'OK' if symbols else 'Failed',
                    'testnet': testnet,
                    'available_symbols_count': len(symbols) if symbols else 0
                }
            })
            
        except Exception as e:
            logger.warning(f"API key test failed for user {user_id} on {exchange}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'API connection failed',
                'details': str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing API keys for user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_key_bp.route('/toggle/<exchange>', methods=['POST'])
@jwt_required()
def toggle_api_key(exchange):
    """Enable/disable API keys for a specific exchange"""
    try:
        user_id = get_jwt_identity()
        exchange = exchange.lower()
        data = request.get_json()
        
        is_active = data.get('is_active', True)
        
        # Check if user has API keys for this exchange
        user = User.find_by_id(user_id)
        if not user or not user.get('api_keys', {}).get(exchange):
            return jsonify({'error': f'No API keys found for {exchange}'}), 404
        
        # Update active status
        success = User.update(user_id, {f'api_keys.{exchange}.is_active': is_active})
        
        if success:
            status = 'enabled' if is_active else 'disabled'
            logger.info(f"User {user_id} {status} API keys for {exchange}")
            logger.log_security_event('api_key_toggled', user_id, {'exchange': exchange, 'is_active': is_active})
            
            return jsonify({
                'success': True,
                'message': f'API keys for {exchange} {status} successfully'
            })
        else:
            return jsonify({'error': 'Failed to update API key status'}), 500
            
    except Exception as e:
        logger.error(f"Error toggling API keys for user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_key_bp.route('/supported-exchanges', methods=['GET'])
def get_supported_exchanges():
    """Get list of supported exchanges"""
    try:
        exchanges = [
            {
                'id': 'binance',
                'name': 'Binance',
                'description': 'World\'s largest cryptocurrency exchange',
                'testnet_available': True,
                'features': ['spot_trading', 'futures_trading', 'margin_trading']
            },
            {
                'id': 'coinbase',
                'name': 'Coinbase Pro',
                'description': 'Professional trading platform by Coinbase',
                'testnet_available': True,
                'features': ['spot_trading']
            },
            {
                'id': 'kraken',
                'name': 'Kraken',
                'description': 'Secure and reliable cryptocurrency exchange',
                'testnet_available': False,
                'features': ['spot_trading', 'margin_trading']
            },
            {
                'id': 'bitfinex',
                'name': 'Bitfinex',
                'description': 'Advanced cryptocurrency trading platform',
                'testnet_available': True,
                'features': ['spot_trading', 'margin_trading', 'lending']
            }
        ]
        
        return jsonify({
            'success': True,
            'exchanges': exchanges
        })
        
    except Exception as e:
        logger.error(f"Error getting supported exchanges: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500