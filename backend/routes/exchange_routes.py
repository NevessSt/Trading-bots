from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bot_engine.exchange_manager import ExchangeManager, ExchangeConfig
from models.user import User
from models.api_key import APIKey
from utils.logger import logger
from utils.encryption import encrypt_data, decrypt_data
import os

exchange_bp = Blueprint('exchange', __name__)

# Global exchange manager instance
exchange_manager = ExchangeManager()

@exchange_bp.route('/exchanges', methods=['GET'])
@jwt_required()
def get_exchanges():
    """Get all configured exchanges and their status"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get exchange status
        exchange_status = exchange_manager.get_exchange_status()
        
        # Get available exchanges from ccxt
        supported_exchanges = [
            'binance', 'coinbase', 'kucoin', 'bybit', 'kraken', 'okx'
        ]
        
        exchanges_info = []
        for exchange_name in supported_exchanges:
            exchange_info = {
                'name': exchange_name,
                'display_name': exchange_name.title(),
                'status': 'disconnected',
                'testnet': False,
                'priority': 0,
                'is_primary': False,
                'configured': False
            }
            
            if exchange_name in exchange_status:
                exchange_info.update(exchange_status[exchange_name])
                exchange_info['configured'] = True
            
            exchanges_info.append(exchange_info)
        
        return jsonify({
            'success': True,
            'exchanges': exchanges_info,
            'primary_exchange': exchange_manager.primary_exchange
        })
        
    except Exception as e:
        logger.error(f"Error getting exchanges: {str(e)}")
        return jsonify({'error': 'Failed to get exchanges'}), 500

@exchange_bp.route('/exchanges/<exchange_name>/configure', methods=['POST'])
@jwt_required()
def configure_exchange(exchange_name):
    """Configure an exchange with API credentials"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('api_key') or not data.get('api_secret'):
            return jsonify({'error': 'API key and secret are required'}), 400
        
        # Validate exchange name
        supported_exchanges = ['binance', 'coinbase', 'kucoin', 'bybit', 'kraken', 'okx']
        if exchange_name.lower() not in supported_exchanges:
            return jsonify({'error': f'Unsupported exchange: {exchange_name}'}), 400
        
        # Create exchange configuration
        config = ExchangeConfig(
            name=exchange_name.lower(),
            api_key=data['api_key'],
            api_secret=data['api_secret'],
            passphrase=data.get('passphrase'),  # Required for Coinbase, KuCoin, OKX
            testnet=data.get('testnet', True),
            enabled=data.get('enabled', True),
            priority=data.get('priority', 10)
        )
        
        # Validate passphrase for exchanges that require it
        if exchange_name.lower() in ['coinbase', 'kucoin', 'okx'] and not config.passphrase:
            return jsonify({'error': f'{exchange_name} requires a passphrase'}), 400
        
        # Add exchange to manager
        success = exchange_manager.add_exchange(config)
        
        if not success:
            return jsonify({'error': 'Failed to configure exchange. Please check your credentials.'}), 400
        
        # Store encrypted credentials in database
        api_key_record = APIKey.query.filter_by(
            user_id=user_id,
            exchange=exchange_name.lower()
        ).first()
        
        if not api_key_record:
            api_key_record = APIKey(
                user_id=user_id,
                exchange=exchange_name.lower()
            )
        
        # Encrypt and store credentials
        api_key_record.api_key = encrypt_data(config.api_key)
        api_key_record.api_secret = encrypt_data(config.api_secret)
        if config.passphrase:
            api_key_record.passphrase = encrypt_data(config.passphrase)
        api_key_record.testnet = config.testnet
        api_key_record.is_active = True
        
        from app import db
        db.session.add(api_key_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{exchange_name} configured successfully',
            'exchange': {
                'name': exchange_name,
                'status': 'connected',
                'testnet': config.testnet,
                'is_primary': exchange_manager.primary_exchange == exchange_name.lower()
            }
        })
        
    except Exception as e:
        logger.error(f"Error configuring exchange {exchange_name}: {str(e)}")
        return jsonify({'error': 'Failed to configure exchange'}), 500

@exchange_bp.route('/exchanges/<exchange_name>/test', methods=['POST'])
@jwt_required()
def test_exchange_connection(exchange_name):
    """Test connection to an exchange"""
    try:
        user_id = get_jwt_identity()
        
        exchange = exchange_manager.get_exchange(exchange_name.lower())
        if not exchange:
            return jsonify({'error': f'Exchange {exchange_name} not configured'}), 404
        
        # Test connection by fetching balance
        balance = exchange.fetch_balance()
        
        return jsonify({
            'success': True,
            'message': f'Connection to {exchange_name} successful',
            'balance_currencies': list(balance.keys()) if balance else []
        })
        
    except Exception as e:
        logger.error(f"Error testing exchange {exchange_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Connection test failed: {str(e)}'
        }), 400

@exchange_bp.route('/exchanges/<exchange_name>/remove', methods=['DELETE'])
@jwt_required()
def remove_exchange(exchange_name):
    """Remove an exchange configuration"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Remove from exchange manager
        success = exchange_manager.remove_exchange(exchange_name.lower())
        
        if success:
            # Remove from database
            api_key_record = APIKey.query.filter_by(
                user_id=user_id,
                exchange=exchange_name.lower()
            ).first()
            
            if api_key_record:
                from app import db
                db.session.delete(api_key_record)
                db.session.commit()
        
        return jsonify({
            'success': success,
            'message': f'{exchange_name} removed successfully' if success else f'{exchange_name} not found'
        })
        
    except Exception as e:
        logger.error(f"Error removing exchange {exchange_name}: {str(e)}")
        return jsonify({'error': 'Failed to remove exchange'}), 500

@exchange_bp.route('/exchanges/<exchange_name>/set-primary', methods=['POST'])
@jwt_required()
def set_primary_exchange(exchange_name):
    """Set an exchange as the primary exchange"""
    try:
        user_id = get_jwt_identity()
        
        exchange = exchange_manager.get_exchange(exchange_name.lower())
        if not exchange:
            return jsonify({'error': f'Exchange {exchange_name} not configured'}), 404
        
        # Update priority to make it primary
        if exchange_name.lower() in exchange_manager.configs:
            exchange_manager.configs[exchange_name.lower()].priority = 0
            exchange_manager.primary_exchange = exchange_name.lower()
        
        return jsonify({
            'success': True,
            'message': f'{exchange_name} set as primary exchange',
            'primary_exchange': exchange_manager.primary_exchange
        })
        
    except Exception as e:
        logger.error(f"Error setting primary exchange {exchange_name}: {str(e)}")
        return jsonify({'error': 'Failed to set primary exchange'}), 500

@exchange_bp.route('/exchanges/markets/<exchange_name>', methods=['GET'])
@jwt_required()
def get_exchange_markets(exchange_name):
    """Get available trading pairs for an exchange"""
    try:
        user_id = get_jwt_identity()
        
        exchange = exchange_manager.get_exchange(exchange_name.lower())
        if not exchange:
            return jsonify({'error': f'Exchange {exchange_name} not configured'}), 404
        
        markets = exchange.fetch_markets()
        
        # Format markets for frontend
        formatted_markets = []
        for market_id, market in markets.items():
            if market.get('active', True):  # Only active markets
                formatted_markets.append({
                    'symbol': market.get('symbol', market_id),
                    'base': market.get('base'),
                    'quote': market.get('quote'),
                    'active': market.get('active', True),
                    'type': market.get('type', 'spot')
                })
        
        return jsonify({
            'success': True,
            'exchange': exchange_name,
            'markets': formatted_markets[:100]  # Limit to first 100 for performance
        })
        
    except Exception as e:
        logger.error(f"Error getting markets for {exchange_name}: {str(e)}")
        return jsonify({'error': 'Failed to get markets'}), 500

@exchange_bp.route('/exchanges/best-price/<symbol>', methods=['GET'])
@jwt_required()
def get_best_price(symbol):
    """Get best price across all configured exchanges"""
    try:
        user_id = get_jwt_identity()
        side = request.args.get('side', 'buy')  # buy or sell
        
        if side not in ['buy', 'sell']:
            return jsonify({'error': 'Side must be buy or sell'}), 400
        
        best_price_info = exchange_manager.get_best_price(symbol, side)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'side': side,
            'best_price': best_price_info
        })
        
    except Exception as e:
        logger.error(f"Error getting best price for {symbol}: {str(e)}")
        return jsonify({'error': 'Failed to get best price'}), 500