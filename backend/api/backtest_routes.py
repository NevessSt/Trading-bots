from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from bot_engine import Backtester
from utils.logger import logger
from utils.security import rate_limit, require_api_keys

backtest_bp = Blueprint('backtest', __name__, url_prefix='/api/backtest')

@backtest_bp.route('/run', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_minutes=60)  # Limit backtests to prevent abuse
def run_backtest():
    """Run a backtest for a strategy"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['strategy', 'symbol']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        strategy_name = data['strategy']
        symbol = data['symbol']
        timeframe = data.get('timeframe', '1h')
        initial_balance = float(data.get('initial_balance', 10000))
        trade_amount = float(data.get('trade_amount', 100))
        take_profit = float(data.get('take_profit', 2.0))
        stop_loss = float(data.get('stop_loss', 1.0))
        
        # Parse dates
        start_date = None
        end_date = None
        
        if 'start_date' in data:
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format.'}), 400
        
        if 'end_date' in data:
            try:
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format.'}), 400
        
        # Validate parameters
        if initial_balance <= 0:
            return jsonify({'error': 'Initial balance must be positive'}), 400
        
        if trade_amount <= 0 or trade_amount > initial_balance:
            return jsonify({'error': 'Trade amount must be positive and not exceed initial balance'}), 400
        
        if take_profit <= 0 or stop_loss <= 0:
            return jsonify({'error': 'Take profit and stop loss must be positive'}), 400
        
        # Validate timeframe
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if timeframe not in valid_timeframes:
            return jsonify({'error': f'Invalid timeframe. Must be one of: {valid_timeframes}'}), 400
        
        # Log backtest request
        logger.info(f"User {user_id} requested backtest: {strategy_name} on {symbol}")
        
        # Initialize backtester
        backtester = Backtester()
        
        # Run backtest
        results = backtester.run_backtest(
            strategy_name=strategy_name,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            trade_amount=trade_amount,
            take_profit=take_profit,
            stop_loss=stop_loss
        )
        
        if 'error' in results:
            logger.warning(f"Backtest failed for user {user_id}: {results['error']}")
            return jsonify({'error': results['error']}), 400
        
        # Log successful backtest
        logger.info(f"Backtest completed for user {user_id}: {results['total_trades']} trades, {results['total_return_pct']:.2f}% return")
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except ValueError as e:
        logger.error(f"Validation error in backtest: {str(e)}")
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@backtest_bp.route('/compare', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_minutes=60)  # More restrictive for comparisons
def compare_strategies():
    """Compare multiple strategies"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['strategies', 'symbol']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        strategies = data['strategies']
        symbol = data['symbol']
        timeframe = data.get('timeframe', '1h')
        initial_balance = float(data.get('initial_balance', 10000))
        trade_amount = float(data.get('trade_amount', 100))
        
        # Validate strategies list
        if not isinstance(strategies, list) or len(strategies) == 0:
            return jsonify({'error': 'Strategies must be a non-empty list'}), 400
        
        if len(strategies) > 5:  # Limit to prevent abuse
            return jsonify({'error': 'Maximum 5 strategies can be compared at once'}), 400
        
        # Parse dates
        start_date = None
        end_date = None
        
        if 'start_date' in data:
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format.'}), 400
        
        if 'end_date' in data:
            try:
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format.'}), 400
        
        # Log comparison request
        logger.info(f"User {user_id} requested strategy comparison: {strategies} on {symbol}")
        
        # Initialize backtester
        backtester = Backtester()
        
        # Run comparison
        results = backtester.compare_strategies(
            strategies=strategies,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            trade_amount=trade_amount
        )
        
        # Check for errors in any strategy
        errors = {strategy: result.get('error') for strategy, result in results.items() if 'error' in result}
        if errors:
            logger.warning(f"Strategy comparison had errors for user {user_id}: {errors}")
            return jsonify({'error': 'Some strategies failed', 'details': errors}), 400
        
        # Log successful comparison
        logger.info(f"Strategy comparison completed for user {user_id}: {len(strategies)} strategies")
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except ValueError as e:
        logger.error(f"Validation error in strategy comparison: {str(e)}")
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error comparing strategies: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@backtest_bp.route('/strategies', methods=['GET'])
@jwt_required()
def get_available_strategies():
    """Get list of available strategies for backtesting"""
    try:
        # Available strategies (should match StrategyFactory)
        strategies = [
            {
                'name': 'rsi',
                'display_name': 'RSI Strategy',
                'description': 'Relative Strength Index based trading strategy'
            },
            {
                'name': 'macd',
                'display_name': 'MACD Strategy',
                'description': 'Moving Average Convergence Divergence strategy'
            },
            {
                'name': 'ema_crossover',
                'display_name': 'EMA Crossover Strategy',
                'description': 'Exponential Moving Average crossover strategy'
            }
        ]
        
        return jsonify({
            'success': True,
            'strategies': strategies
        })
        
    except Exception as e:
        logger.error(f"Error getting available strategies: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@backtest_bp.route('/symbols', methods=['GET'])
@jwt_required()
def get_available_symbols():
    """Get list of available trading symbols for backtesting"""
    try:
        # Common trading pairs (in a real implementation, this would come from the exchange)
        symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT',
            'SOL/USDT', 'DOT/USDT', 'DOGE/USDT', 'AVAX/USDT', 'LUNA/USDT',
            'LINK/USDT', 'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'ALGO/USDT'
        ]
        
        return jsonify({
            'success': True,
            'symbols': symbols
        })
        
    except Exception as e:
        logger.error(f"Error getting available symbols: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@backtest_bp.route('/timeframes', methods=['GET'])
@jwt_required()
def get_available_timeframes():
    """Get list of available timeframes for backtesting"""
    try:
        timeframes = [
            {'value': '1m', 'label': '1 Minute'},
            {'value': '5m', 'label': '5 Minutes'},
            {'value': '15m', 'label': '15 Minutes'},
            {'value': '30m', 'label': '30 Minutes'},
            {'value': '1h', 'label': '1 Hour'},
            {'value': '4h', 'label': '4 Hours'},
            {'value': '1d', 'label': '1 Day'}
        ]
        
        return jsonify({
            'success': True,
            'timeframes': timeframes
        })
        
    except Exception as e:
        logger.error(f"Error getting available timeframes: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500