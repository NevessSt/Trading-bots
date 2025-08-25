#!/usr/bin/env python3
"""
API Connection Test Routes

Provides REST endpoints for testing exchange API connections through the web interface.
These routes allow users to verify their API credentials and connection status.
"""

import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
from auth.decorators import token_required
from utils.logger import get_logger

# Initialize blueprint
connection_test_bp = Blueprint('connection_test', __name__)
logger = get_logger(__name__)

def handle_api_errors(f):
    """Decorator to handle API errors gracefully"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ImportError as e:
            logger.error(f"Missing library: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Required library not installed',
                'details': str(e),
                'solution': 'Install the required Python package'
            }), 500
        except Exception as e:
            logger.error(f"API connection test error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Connection test failed',
                'details': str(e)
            }), 500
    return decorated_function

@connection_test_bp.route('/test-binance', methods=['POST'])
@token_required
@handle_api_errors
def test_binance_connection():
    """Test Binance API connection"""
    try:
        from binance.client import Client
        from binance.exceptions import BinanceAPIException
        
        # Get credentials from request or environment
        data = request.get_json() or {}
        api_key = data.get('api_key') or os.getenv('BINANCE_API_KEY')
        secret_key = data.get('secret_key') or os.getenv('BINANCE_SECRET_KEY')
        use_testnet = data.get('testnet', os.getenv('BINANCE_TESTNET', 'true').lower() == 'true')
        
        if not api_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'Missing API credentials',
                'details': 'Please provide api_key and secret_key'
            }), 400
            
        # Initialize client
        client = Client(
            api_key=api_key,
            api_secret=secret_key,
            testnet=use_testnet
        )
        
        # Test server connection
        server_time = client.get_server_time()
        server_datetime = datetime.fromtimestamp(server_time['serverTime']/1000)
        
        # Test account access
        account_info = client.get_account()
        
        # Get non-zero balances
        balances = [
            {
                'asset': b['asset'],
                'free': float(b['free']),
                'locked': float(b['locked']),
                'total': float(b['free']) + float(b['locked'])
            }
            for b in account_info['balances']
            if float(b['free']) > 0 or float(b['locked']) > 0
        ]
        
        # Test market data
        market_data = None
        try:
            ticker = client.get_symbol_ticker(symbol="BTCUSDT")
            market_data = {
                'symbol': ticker['symbol'],
                'price': float(ticker['price'])
            }
        except Exception as e:
            logger.warning(f"Market data test failed: {str(e)}")
            
        # Test trading permissions
        trading_permissions = {'can_trade': False, 'error': None}
        try:
            client.create_test_order(
                symbol='BTCUSDT',
                side='BUY',
                type='MARKET',
                quantity=0.001
            )
            trading_permissions['can_trade'] = True
        except BinanceAPIException as e:
            if any(phrase in str(e).lower() for phrase in ['insufficient balance', 'invalid symbol']):
                trading_permissions['can_trade'] = True
                trading_permissions['note'] = 'Permissions verified (test order validation working)'
            else:
                trading_permissions['error'] = str(e)
        except Exception as e:
            trading_permissions['error'] = str(e)
            
        return jsonify({
            'success': True,
            'exchange': 'binance',
            'environment': 'testnet' if use_testnet else 'live',
            'server_time': server_datetime.isoformat(),
            'account': {
                'type': account_info['accountType'],
                'can_trade': account_info['canTrade'],
                'can_withdraw': account_info['canWithdraw'],
                'can_deposit': account_info['canDeposit']
            },
            'balances': balances[:10],  # Limit to first 10 balances
            'total_assets': len(balances),
            'market_data': market_data,
            'trading_permissions': trading_permissions,
            'timestamp': datetime.now().isoformat()
        })
        
    except BinanceAPIException as e:
        error_msg = str(e)
        suggestions = []
        
        if 'invalid api-key' in error_msg.lower():
            suggestions.extend([
                'Verify your API key is correct',
                'Check IP restrictions in Binance settings',
                'Ensure API permissions are enabled'
            ])
        elif 'timestamp' in error_msg.lower():
            suggestions.extend([
                'Synchronize your system clock',
                'Check your internet connection'
            ])
        elif 'rate limit' in error_msg.lower():
            suggestions.extend([
                'Wait a moment before retrying',
                'Reduce API request frequency'
            ])
            
        return jsonify({
            'success': False,
            'error': 'Binance API Error',
            'details': error_msg,
            'suggestions': suggestions
        }), 400

@connection_test_bp.route('/test-coinbase', methods=['POST'])
@token_required
@handle_api_errors
def test_coinbase_connection():
    """Test Coinbase Pro API connection"""
    try:
        import cbpro
        
        # Get credentials from request or environment
        data = request.get_json() or {}
        api_key = data.get('api_key') or os.getenv('COINBASE_API_KEY')
        secret_key = data.get('secret_key') or os.getenv('COINBASE_SECRET_KEY')
        passphrase = data.get('passphrase') or os.getenv('COINBASE_PASSPHRASE')
        sandbox = data.get('sandbox', os.getenv('COINBASE_SANDBOX', 'true').lower() == 'true')
        
        if not all([api_key, secret_key, passphrase]):
            return jsonify({
                'success': False,
                'error': 'Missing API credentials',
                'details': 'Please provide api_key, secret_key, and passphrase'
            }), 400
            
        # Initialize client
        client = cbpro.AuthenticatedClient(
            api_key, secret_key, passphrase,
            sandbox=sandbox
        )
        
        # Test account access
        accounts = client.get_accounts()
        
        # Process account data
        account_balances = [
            {
                'currency': acc['currency'],
                'balance': float(acc['balance']),
                'available': float(acc['available']),
                'hold': float(acc['hold'])
            }
            for acc in accounts
            if float(acc['balance']) > 0
        ]
        
        return jsonify({
            'success': True,
            'exchange': 'coinbase',
            'environment': 'sandbox' if sandbox else 'live',
            'accounts': account_balances,
            'total_accounts': len(accounts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Coinbase Pro API Error',
            'details': str(e)
        }), 400

@connection_test_bp.route('/test-kraken', methods=['POST'])
@token_required
@handle_api_errors
def test_kraken_connection():
    """Test Kraken API connection"""
    try:
        import krakenex
        
        # Get credentials from request or environment
        data = request.get_json() or {}
        api_key = data.get('api_key') or os.getenv('KRAKEN_API_KEY')
        secret_key = data.get('secret_key') or os.getenv('KRAKEN_SECRET_KEY')
        
        if not api_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'Missing API credentials',
                'details': 'Please provide api_key and secret_key'
            }), 400
            
        # Initialize client
        client = krakenex.API()
        client.key = api_key
        client.secret = secret_key
        
        # Test account access
        response = client.query_private('Balance')
        
        if response['error']:
            return jsonify({
                'success': False,
                'error': 'Kraken API Error',
                'details': response['error']
            }), 400
            
        # Process balance data
        balances = [
            {
                'currency': currency,
                'balance': float(balance)
            }
            for currency, balance in response['result'].items()
            if float(balance) > 0
        ]
        
        return jsonify({
            'success': True,
            'exchange': 'kraken',
            'balances': balances,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Kraken API Error',
            'details': str(e)
        }), 400

@connection_test_bp.route('/test-all', methods=['POST'])
@token_required
@handle_api_errors
def test_all_connections():
    """Test all configured exchange connections"""
    results = {}
    
    # Test Binance if credentials exist
    if os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_SECRET_KEY'):
        try:
            response = test_binance_connection()
            results['binance'] = response.get_json()
        except Exception as e:
            results['binance'] = {
                'success': False,
                'error': str(e)
            }
    else:
        results['binance'] = {
            'success': False,
            'error': 'No credentials configured'
        }
        
    # Test Coinbase if credentials exist
    if all([os.getenv('COINBASE_API_KEY'), os.getenv('COINBASE_SECRET_KEY'), os.getenv('COINBASE_PASSPHRASE')]):
        try:
            response = test_coinbase_connection()
            results['coinbase'] = response.get_json()
        except Exception as e:
            results['coinbase'] = {
                'success': False,
                'error': str(e)
            }
    else:
        results['coinbase'] = {
            'success': False,
            'error': 'No credentials configured'
        }
        
    # Test Kraken if credentials exist
    if os.getenv('KRAKEN_API_KEY') and os.getenv('KRAKEN_SECRET_KEY'):
        try:
            response = test_kraken_connection()
            results['kraken'] = response.get_json()
        except Exception as e:
            results['kraken'] = {
                'success': False,
                'error': str(e)
            }
    else:
        results['kraken'] = {
            'success': False,
            'error': 'No credentials configured'
        }
        
    # Calculate overall success
    successful_tests = sum(1 for result in results.values() if result.get('success', False))
    total_configured = sum(1 for result in results.values() if result.get('error') != 'No credentials configured')
    
    return jsonify({
        'success': successful_tests > 0,
        'summary': {
            'successful': successful_tests,
            'total_configured': total_configured,
            'total_possible': len(results)
        },
        'results': results,
        'timestamp': datetime.now().isoformat()
    })

@connection_test_bp.route('/supported-exchanges', methods=['GET'])
def get_supported_exchanges():
    """Get list of supported exchanges and their configuration status"""
    exchanges = {
        'binance': {
            'name': 'Binance',
            'configured': bool(os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_SECRET_KEY')),
            'testnet_available': True,
            'required_credentials': ['BINANCE_API_KEY', 'BINANCE_SECRET_KEY'],
            'optional_settings': ['BINANCE_TESTNET']
        },
        'coinbase': {
            'name': 'Coinbase Pro',
            'configured': bool(all([
                os.getenv('COINBASE_API_KEY'),
                os.getenv('COINBASE_SECRET_KEY'),
                os.getenv('COINBASE_PASSPHRASE')
            ])),
            'testnet_available': True,
            'required_credentials': ['COINBASE_API_KEY', 'COINBASE_SECRET_KEY', 'COINBASE_PASSPHRASE'],
            'optional_settings': ['COINBASE_SANDBOX']
        },
        'kraken': {
            'name': 'Kraken',
            'configured': bool(os.getenv('KRAKEN_API_KEY') and os.getenv('KRAKEN_SECRET_KEY')),
            'testnet_available': False,
            'required_credentials': ['KRAKEN_API_KEY', 'KRAKEN_SECRET_KEY'],
            'optional_settings': []
        }
    }
    
    return jsonify({
        'success': True,
        'exchanges': exchanges,
        'total_supported': len(exchanges),
        'total_configured': sum(1 for ex in exchanges.values() if ex['configured'])
    })

@connection_test_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for connection test service"""
    return jsonify({
        'success': True,
        'service': 'connection_test',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@connection_test_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/test-binance',
            '/test-coinbase',
            '/test-kraken',
            '/test-all',
            '/supported-exchanges',
            '/health'
        ]
    }), 404

@connection_test_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'details': 'Check the HTTP method for this endpoint'
    }), 405