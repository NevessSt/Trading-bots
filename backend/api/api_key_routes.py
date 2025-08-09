from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from db import db
from models import User, APIKey
from utils.logger import logger
from utils.security import security_manager, rate_limit
from utils.encryption import get_encryption_manager, EncryptionError
from auth.license_manager import require_license
from bot_engine import TradingEngine
import re

api_key_bp = Blueprint('api_keys', __name__, url_prefix='/api/keys')

@api_key_bp.route('/add', methods=['POST'])
@jwt_required()
@require_license('live_trading')
@rate_limit(max_requests=5, window_minutes=60)
def add_api_key():
    """Add or update user's exchange API keys with encrypted storage"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['exchange', 'key_name', 'api_key', 'api_secret']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        exchange = data['exchange'].lower()
        key_name = data['key_name'].strip()
        api_key = data['api_key'].strip()
        api_secret = data['api_secret'].strip()
        passphrase = data.get('passphrase', '').strip() or None
        testnet = data.get('testnet', True)  # Default to testnet for safety
        permissions = data.get('permissions', ['read', 'trade'])
        
        # Validate exchange
        supported_exchanges = ['binance', 'coinbase', 'kraken', 'bitfinex', 'okx', 'kucoin']
        if exchange not in supported_exchanges:
            return jsonify({'error': f'Unsupported exchange. Supported: {supported_exchanges}'}), 400
        
        # Validate key name
        if len(key_name) < 3 or len(key_name) > 50:
            return jsonify({'error': 'Key name must be between 3 and 50 characters'}), 400
        
        # Check if key name already exists for this user
        existing_key = APIKey.query.filter_by(
            user_id=user_id, 
            key_name=key_name, 
            is_active=True
        ).first()
        
        if existing_key:
            return jsonify({'error': 'Key name already exists'}), 400
        
        # Validate API key format (basic validation)
        if len(api_key) < 10:
            return jsonify({'error': 'API key too short'}), 400
        
        if len(api_secret) < 10:
            return jsonify({'error': 'API secret too short'}), 400
        
        # Validate permissions
        valid_permissions = ['read', 'trade', 'withdraw']
        if not all(perm in valid_permissions for perm in permissions):
            return jsonify({'error': f'Invalid permissions. Valid: {valid_permissions}'}), 400
        
        # Test API key validity (optional, can be skipped for faster setup)
        if data.get('validate_keys', True):
            try:
                # Basic validation - try to create trading engine instance
                trading_engine = TradingEngine(
                    api_key=api_key, 
                    api_secret=api_secret, 
                    passphrase=passphrase,
                    testnet=testnet
                )
                
                # Try to fetch account info to validate keys
                balance = trading_engine.get_account_balance(user_id)
                if not balance:
                    return jsonify({'error': 'Invalid API credentials or insufficient permissions'}), 400
                
                logger.info(f"API key validation successful for user {user_id} on {exchange}")
                
            except Exception as e:
                logger.error(f"API key validation failed for user {user_id}: {str(e)}")
                return jsonify({'error': 'Invalid API credentials or exchange connection failed'}), 400
        
        # Create new API key record with encryption
        try:
            api_key_record = APIKey(
                user_id=user_id,
                exchange=exchange,
                key_name=key_name,
                permissions=permissions,
                testnet=testnet
            )
            
            # Set encrypted credentials
            api_key_record.set_credentials(api_key, api_secret, passphrase)
            
            db.session.add(api_key_record)
            db.session.commit()
            
            logger.info(f"API key '{key_name}' added successfully for user {user_id} on {exchange}")
            logger.log_security_event('api_key_added', user_id, {'exchange': exchange, 'testnet': testnet})
            
            return jsonify({
                'success': True,
                'message': f'API key added successfully',
                'key_id': api_key_record.id,
                'key_name': key_name,
                'exchange': exchange,
                'testnet': testnet,
                'permissions': permissions,
                'created_at': api_key_record.created_at.isoformat()
            }), 201
            
        except EncryptionError as e:
            logger.error(f"Encryption error for user {user_id}: {str(e)}")
            return jsonify({'error': 'Failed to encrypt API credentials'}), 500
            
    except Exception as e:
        logger.error(f"Error adding API keys for user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_key_bp.route('/list', methods=['GET'])
@jwt_required()
def list_api_keys():
    """List user's configured API keys (safe info only)"""
    try:
        user_id = get_jwt_identity()
        
        # Get all active API keys for the user
        api_keys = APIKey.find_by_user_id(user_id)
        
        api_keys_info = []
        for api_key in api_keys:
            if api_key.is_active:
                # Only return safe information
                safe_info = {
                    'id': api_key.id,
                    'key_name': api_key.key_name,
                    'exchange': api_key.exchange,
                    'testnet': api_key.testnet,
                    'permissions': api_key.permissions,
                    'created_at': api_key.created_at.isoformat(),
                    'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
                    'usage_count': api_key.usage_count,
                    'api_key_preview': api_key.api_key[:8] + '...' if api_key.api_key else None
                }
                api_keys_info.append(safe_info)
        
        return jsonify({
            'api_keys': api_keys_info,
            'total': len(api_keys_info)
        })
        
    except Exception as e:
        logger.error(f"Error listing API keys for user {user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_key_bp.route('/remove/<int:key_id>', methods=['DELETE'])
@jwt_required()
@rate_limit(max_requests=10, window_minutes=60)
def remove_api_key(key_id):
    """Remove API key by ID"""
    try:
        user_id = get_jwt_identity()
        
        # Find the API key
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Mark as inactive instead of deleting
        api_key.is_active = False
        api_key.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"API key '{api_key.key_name}' removed for user {user_id} on {api_key.exchange}")
        logger.log_security_event('api_key_removed', user_id, {'exchange': api_key.exchange, 'key_name': api_key.key_name})
        
        return jsonify({
            'success': True,
            'message': f'API key "{api_key.key_name}" removed successfully'
        })
            
    except Exception as e:
         logger.error(f"Error removing API key for user {user_id}: {str(e)}")
         return jsonify({'error': 'Internal server error'}), 500


@api_key_bp.route('/test/<int:key_id>', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=3, window_minutes=60)
def test_api_key(key_id):
    """Test API key connection and permissions"""
    try:
        user_id = get_jwt_identity()
        
        # Find the API key
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Get decrypted credentials
        try:
            credentials = api_key.get_credentials()
            if not credentials:
                return jsonify({'error': 'Failed to decrypt API credentials'}), 500
        except EncryptionError as e:
            logger.error(f"Decryption error for API key {key_id}: {str(e)}")
            return jsonify({'error': 'Failed to decrypt API credentials'}), 500
        
        # Test the API key
        try:
            trading_engine = TradingEngine(
                api_key=credentials['api_key'],
                api_secret=credentials['api_secret'],
                passphrase=credentials.get('passphrase'),
                testnet=api_key.testnet
            )
            
            # Try to fetch account info
            balance = trading_engine.get_account_balance(user_id)
            
            if balance:
                # Update last used timestamp
                api_key.update_usage()
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'API key test successful',
                    'exchange': api_key.exchange,
                    'testnet': api_key.testnet,
                    'balance_available': True
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'API key test failed - no balance data',
                    'error': 'Invalid credentials or insufficient permissions'
                }), 400
                
        except Exception as e:
            logger.error(f"API key test failed for key {key_id}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'API key test failed',
                'error': str(e)
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing API key {key_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_key_bp.route('/update/<int:key_id>', methods=['PUT'])
@jwt_required()
@rate_limit(max_requests=5, window_minutes=60)
def update_api_key(key_id):
    """Update API key credentials or settings"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Find the API key
        api_key = APIKey.query.filter_by(
            id=key_id,
            user_id=user_id,
            is_active=True
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # Update key name if provided
        if 'key_name' in data:
            new_key_name = data['key_name'].strip()
            if len(new_key_name) < 3 or len(new_key_name) > 50:
                return jsonify({'error': 'Key name must be between 3 and 50 characters'}), 400
            
            # Check if new name already exists for this user (excluding current key)
            existing_key = APIKey.query.filter_by(
                user_id=user_id,
                key_name=new_key_name,
                is_active=True
            ).filter(APIKey.id != key_id).first()
            
            if existing_key:
                return jsonify({'error': 'Key name already exists'}), 400
            
            api_key.key_name = new_key_name
        
        # Update permissions if provided
        if 'permissions' in data:
            permissions = data['permissions']
            valid_permissions = ['read', 'trade', 'withdraw']
            if not all(perm in valid_permissions for perm in permissions):
                return jsonify({'error': f'Invalid permissions. Valid: {valid_permissions}'}), 400
            api_key.permissions = permissions
        
        # Update credentials if provided
        if any(field in data for field in ['api_key', 'api_secret', 'passphrase']):
            api_key_val = data.get('api_key', '').strip()
            api_secret = data.get('api_secret', '').strip()
            passphrase = data.get('passphrase', '').strip() or None
            
            if api_key_val and len(api_key_val) < 10:
                return jsonify({'error': 'API key too short'}), 400
            
            if api_secret and len(api_secret) < 10:
                return jsonify({'error': 'API secret too short'}), 400
            
            # If updating credentials, get current ones first
            try:
                current_creds = api_key.get_credentials()
                
                # Use new values or keep current ones
                final_api_key = api_key_val if api_key_val else current_creds['api_key']
                final_api_secret = api_secret if api_secret else current_creds['api_secret']
                final_passphrase = passphrase if 'passphrase' in data else current_creds.get('passphrase')
                
                # Test new credentials if validation is requested
                if data.get('validate_keys', True):
                    try:
                        trading_engine = TradingEngine(
                            api_key=final_api_key,
                            api_secret=final_api_secret,
                            passphrase=final_passphrase,
                            testnet=api_key.testnet
                        )
                        
                        balance = trading_engine.get_account_balance(user_id)
                        if not balance:
                            return jsonify({'error': 'Invalid API credentials or insufficient permissions'}), 400
                            
                    except Exception as e:
                        logger.error(f"API key validation failed during update: {str(e)}")
                        return jsonify({'error': 'Invalid API credentials or exchange connection failed'}), 400
                
                # Update credentials
                api_key.update_credentials(final_api_key, final_api_secret, final_passphrase)
                
            except EncryptionError as e:
                logger.error(f"Encryption error during update for key {key_id}: {str(e)}")
                return jsonify({'error': 'Failed to encrypt API credentials'}), 500
        
        api_key.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"API key '{api_key.key_name}' updated for user {user_id}")
        
        return jsonify({
            'message': 'API key updated successfully',
            'key_id': api_key.id,
            'key_name': api_key.key_name,
            'exchange': api_key.exchange,
            'permissions': api_key.permissions,
            'updated_at': api_key.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating API key {key_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Removed duplicate test_api_key function - using the new one with key_id parameter

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