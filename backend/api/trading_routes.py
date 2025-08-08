from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import asyncio

# Import trading engine components
from bot_engine import TradingEngine, RiskManager
from db import db
from models import Trade, User, Bot

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
    })







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

@trading_bp.route('/realtime/<symbol>', methods=['GET'])
@jwt_required()
def get_realtime_data(symbol):
    """Get real-time price data for a symbol"""
    try:
        engine = get_trading_engine()
        data = engine.get_real_time_data(symbol.upper())
        
        if data:
            return jsonify({
                'symbol': data['symbol'],
                'price': data['price'],
                'change': data['change'],
                'volume': data['volume'],
                'high': data['high'],
                'low': data['low'],
                'timestamp': data['timestamp'].isoformat()
            }), 200
        else:
            return jsonify({'error': 'No real-time data available for this symbol'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/realtime', methods=['GET'])
@jwt_required()
def get_all_realtime_data():
    """Get all real-time price data"""
    try:
        engine = get_trading_engine()
        all_data = engine.get_all_real_time_data()
        
        # Format data for response
        formatted_data = {}
        for symbol, data in all_data.items():
            formatted_data[symbol] = {
                'symbol': data['symbol'],
                'price': data['price'],
                'change': data['change'],
                'volume': data['volume'],
                'high': data['high'],
                'low': data['low'],
                'timestamp': data['timestamp'].isoformat()
            }
        
        return jsonify({'data': formatted_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/market-data/<symbol>', methods=['GET'])
@jwt_required()
def get_market_data(symbol):
    """Get historical market data for a symbol"""
    try:
        engine = get_trading_engine()
        
        # Get parameters
        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 100))
        
        # Fetch market data
        df = engine.get_market_data(symbol.upper(), interval, limit)
        
        if df.empty:
            return jsonify({'error': 'No market data available'}), 404
        
        # Convert DataFrame to list of dictionaries
        data = []
        for index, row in df.iterrows():
            data.append({
                'timestamp': index.isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })
        
        return jsonify({
            'symbol': symbol.upper(),
            'interval': interval,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/account/balance', methods=['GET'])
@jwt_required()
def get_account_balance():
    """Get account balance information"""
    try:
        engine = get_trading_engine()
        balance = engine.get_account_balance()
        return jsonify(balance), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/websocket/start/<symbol>', methods=['POST'])
@jwt_required()
def start_websocket_stream(symbol):
    """Start WebSocket stream for a symbol"""
    try:
        engine = get_trading_engine()
        
        # Start WebSocket stream in background
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(engine.start_websocket_stream(symbol.upper()))
        
        return jsonify({'message': f'WebSocket stream started for {symbol.upper()}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_bp.route('/websocket/stop/<symbol>', methods=['POST'])
@jwt_required()
def stop_websocket_stream(symbol):
    """Stop WebSocket stream for a symbol"""
    try:
        engine = get_trading_engine()
        engine.stop_websocket_stream(symbol.upper())
        return jsonify({'message': f'WebSocket stream stopped for {symbol.upper()}'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['name', 'strategy']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Extract required parameters from config
        config = data.get('config', {})
        
        # Create bot directly using Bot model
        bot = Bot(
            user_id=user_id,
            name=data['name'],
            strategy=data['strategy'],
            symbol=data.get('trading_pair', 'BTCUSDT'),  # Map trading_pair to symbol
            base_amount=config.get('base_amount', 100.0),  # Default base amount
            timeframe=config.get('timeframe', '1h'),
            stop_loss_percentage=config.get('stop_loss_percentage'),
            take_profit_percentage=config.get('take_profit_percentage'),
            max_daily_trades=config.get('max_daily_trades', 10),
            risk_per_trade=config.get('risk_per_trade', 2.0),
            is_paper_trading=config.get('is_paper_trading', True)
        )
        
        db.session.add(bot)
        db.session.commit()
        
        return jsonify({
            'message': 'Bot created successfully',
            'bot': bot.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
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