from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Import trading engine components
from bot_engine import TradingEngine, RiskManager
from models.trade import Trade
from models.user import User
from models.bot import Bot

# Create blueprint
trading_bp = Blueprint('trading', __name__)

# Initialize trading engine
trading_engine = None

def get_trading_engine():
    """Get or initialize the trading engine"""
    global trading_engine
    if trading_engine is None:
        trading_engine = TradingEngine(
            api_key=current_app.config['BINANCE_API_KEY'],
            api_secret=current_app.config['BINANCE_API_SECRET']
        )
    return trading_engine

@trading_bp.route('/status', methods=['GET'])
@jwt_required()
def get_trading_status():
    """Get the current trading status for the user"""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's active bots
    engine = get_trading_engine()
    active_bots = engine.get_active_bots(user_id)
    
    # Get user's recent trades
    recent_trades = Trade.get_recent_trades(user_id, limit=10)
    
    # Get account balance
    balance = engine.get_account_balance(user_id)
    
    return jsonify({
        'active_bots': active_bots,
        'recent_trades': recent_trades,
        'balance': balance,
        'is_trading_enabled': user.get('settings', {}).get('is_trading_enabled', False)
    }), 200

@trading_bp.route('/start', methods=['POST'])
@jwt_required()
def start_trading():
    """Start trading for the user"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate trading parameters
    if not data:
        return jsonify({'error': 'Trading parameters are required'}), 400
    
    # Required parameters
    required_params = ['symbol', 'strategy', 'interval']
    for param in required_params:
        if param not in data:
            return jsonify({'error': f'Missing required parameter: {param}'}), 400
    
    # Optional parameters with defaults
    amount = data.get('amount', 100)  # Default $100 worth
    take_profit = data.get('take_profit', 3.0)  # Default 3%
    stop_loss = data.get('stop_loss', 2.0)  # Default 2%
    
    # Start trading bot
    try:
        engine = get_trading_engine()
        bot_id = engine.start_bot(
            user_id=user_id,
            symbol=data['symbol'],
            strategy=data['strategy'],
            interval=data['interval'],
            amount=amount,
            take_profit=take_profit,
            stop_loss=stop_loss
        )
        
        # Update user settings
        User.update(user_id, {
            'settings.is_trading_enabled': True,
            'settings.active_bots': User.find_by_id(user_id).get('settings', {}).get('active_bots', []) + [bot_id]
        })
        
        return jsonify({
            'message': 'Trading started successfully',
            'bot_id': bot_id,
            'settings': {
                'symbol': data['symbol'],
                'strategy': data['strategy'],
                'interval': data['interval'],
                'amount': amount,
                'take_profit': take_profit,
                'stop_loss': stop_loss
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_trading():
    """Stop trading for the user"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if bot_id is provided
    bot_id = data.get('bot_id')
    stop_all = data.get('stop_all', False)
    
    try:
        if stop_all:
            # Stop all bots for the user
            engine = get_trading_engine()
            stopped_bots = engine.stop_all_bots(user_id)
            
            # Update user settings
            User.update(user_id, {
                'settings.is_trading_enabled': False,
                'settings.active_bots': []
            })
            
            return jsonify({
                'message': 'All trading bots stopped successfully',
                'stopped_bots': stopped_bots
            }), 200
        elif bot_id:
            # Stop specific bot
            engine = get_trading_engine()
            success = engine.stop_bot(user_id, bot_id)
            
            if success:
                # Update user's active bots list
                user = User.find_by_id(user_id)
                active_bots = user.get('settings', {}).get('active_bots', [])
                
                if bot_id in active_bots:
                    active_bots.remove(bot_id)
                
                User.update(user_id, {
                    'settings.active_bots': active_bots,
                    'settings.is_trading_enabled': len(active_bots) > 0
                })
                
                return jsonify({
                    'message': f'Trading bot {bot_id} stopped successfully'
                }), 200
            else:
                return jsonify({'error': f'Failed to stop bot {bot_id}'}), 500
        else:
            return jsonify({'error': 'Either bot_id or stop_all parameter is required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/trades', methods=['GET'])
@jwt_required()
def get_trades():
    """Get user's trade history with pagination"""
    user_id = get_jwt_identity()
    
    # Pagination parameters
    limit = int(request.args.get('limit', 20))
    page = int(request.args.get('page', 1))
    skip = (page - 1) * limit
    
    # Filtering parameters
    symbol = request.args.get('symbol')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    trade_type = request.args.get('type')  # 'buy' or 'sell'
    
    # Build filter
    filters = {'user_id': user_id}
    
    if symbol:
        filters['symbol'] = symbol
    
    if start_date:
        filters['timestamp'] = {'$gte': datetime.fromisoformat(start_date)}
    
    if end_date:
        if 'timestamp' in filters:
            filters['timestamp']['$lte'] = datetime.fromisoformat(end_date)
        else:
            filters['timestamp'] = {'$lte': datetime.fromisoformat(end_date)}
    
    if trade_type and trade_type in ['buy', 'sell']:
        filters['type'] = trade_type
    
    # Get trades
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

@trading_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance():
    """Get trading performance statistics"""
    user_id = get_jwt_identity()
    
    # Time period (default: last 30 days)
    period = request.args.get('period', '30d')
    
    # Calculate performance metrics
    try:
        engine = get_trading_engine()
        performance = engine.calculate_performance(user_id, period)
        return jsonify(performance), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/symbols', methods=['GET'])
@jwt_required()
def get_available_symbols():
    """Get available trading symbols"""
    try:
        engine = get_trading_engine()
        symbols = engine.get_available_symbols()
        return jsonify({'symbols': symbols}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/strategies', methods=['GET'])
@jwt_required()
def get_available_strategies():
    """Get available trading strategies"""
    strategies = [
        {
            'id': 'rsi',
            'name': 'RSI Strategy',
            'description': 'Uses Relative Strength Index to identify overbought and oversold conditions',
            'parameters': [
                {'name': 'rsi_period', 'type': 'integer', 'default': 14, 'min': 2, 'max': 30},
                {'name': 'rsi_overbought', 'type': 'integer', 'default': 70, 'min': 50, 'max': 90},
                {'name': 'rsi_oversold', 'type': 'integer', 'default': 30, 'min': 10, 'max': 50}
            ]
        },
        {
            'id': 'macd',
            'name': 'MACD Strategy',
            'description': 'Uses Moving Average Convergence Divergence for trend following',
            'parameters': [
                {'name': 'fast_period', 'type': 'integer', 'default': 12, 'min': 5, 'max': 30},
                {'name': 'slow_period', 'type': 'integer', 'default': 26, 'min': 10, 'max': 50},
                {'name': 'signal_period', 'type': 'integer', 'default': 9, 'min': 5, 'max': 20}
            ]
        },
        {
            'id': 'ema_crossover',
            'name': 'EMA Crossover Strategy',
            'description': 'Uses Exponential Moving Average crossovers to identify trends',
            'parameters': [
                {'name': 'fast_ema', 'type': 'integer', 'default': 9, 'min': 3, 'max': 30},
                {'name': 'slow_ema', 'type': 'integer', 'default': 21, 'min': 10, 'max': 50}
            ]
        }
    ]
    
    return jsonify({'strategies': strategies}), 200

@trading_bp.route('/bots', methods=['GET'])
@jwt_required()
def get_user_bots():
    """Get all bots for the current user"""
    user_id = get_jwt_identity()
    
    try:
        engine = get_trading_engine()
        bots = engine.get_user_bots(user_id)
        return jsonify({'bots': bots}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/bots', methods=['POST'])
@jwt_required()
def create_bot():
    """Create a new trading bot"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'symbol', 'strategy', 'amount']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        engine = get_trading_engine()
        bot_id = engine.create_bot(
            user_id=user_id,
            name=data['name'],
            symbol=data['symbol'],
            strategy=data['strategy'],
            amount=data['amount'],
            take_profit=data.get('takeProfit', 3.0),
            stop_loss=data.get('stopLoss', 2.0),
            strategy_params=data.get('strategyParams', {})
        )
        
        return jsonify({
            'message': 'Bot created successfully',
            'bot_id': bot_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/bots/<bot_id>', methods=['GET'])
@jwt_required()
def get_bot_details(bot_id):
    """Get detailed information about a specific bot"""
    user_id = get_jwt_identity()
    
    try:
        engine = get_trading_engine()
        bot = engine.get_bot_details(user_id, bot_id)
        if not bot:
            return jsonify({'error': 'Bot not found'}), 404
        
        return jsonify(bot), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/bots/<bot_id>', methods=['PUT'])
@jwt_required()
def update_bot(bot_id):
    """Update a trading bot"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        engine = get_trading_engine()
        success = engine.update_bot(user_id, bot_id, data)
        
        if success:
            return jsonify({'message': 'Bot updated successfully'}), 200
        else:
            return jsonify({'error': 'Bot not found or update failed'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/bots/<bot_id>', methods=['DELETE'])
@jwt_required()
def delete_bot(bot_id):
    """Delete a trading bot"""
    user_id = get_jwt_identity()
    
    try:
        engine = get_trading_engine()
        success = engine.delete_bot(user_id, bot_id)
        
        if success:
            return jsonify({'message': 'Bot deleted successfully'}), 200
        else:
            return jsonify({'error': 'Bot not found or deletion failed'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/bots/<bot_id>/start', methods=['POST'])
@jwt_required()
def start_bot(bot_id):
    """Start a specific trading bot"""
    user_id = get_jwt_identity()
    
    try:
        engine = get_trading_engine()
        success = engine.start_bot_by_id(user_id, bot_id)
        
        if success:
            return jsonify({'message': 'Bot started successfully'}), 200
        else:
            return jsonify({'error': 'Bot not found or failed to start'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/bots/<bot_id>/stop', methods=['POST'])
@jwt_required()
def stop_bot(bot_id):
    """Stop a specific trading bot"""
    user_id = get_jwt_identity()
    
    try:
        engine = get_trading_engine()
        success = engine.stop_bot_by_id(user_id, bot_id)
        
        if success:
            return jsonify({'message': 'Bot stopped successfully'}), 200
        else:
            return jsonify({'error': 'Bot not found or failed to stop'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/bots/<bot_id>/trades', methods=['GET'])
@jwt_required()
def get_bot_trades(bot_id):
    """Get trades for a specific bot"""
    user_id = get_jwt_identity()
    
    # Pagination parameters
    limit = int(request.args.get('limit', 20))
    page = int(request.args.get('page', 1))
    skip = (page - 1) * limit
    
    # Build filter
    filters = {'user_id': user_id, 'bot_id': bot_id}
    
    # Get trades
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