from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from bot_engine.trading_engine import TradingEngine, TradingBotConfig
from models.bot import Bot
from models.user import User
from models.trade import Trade
from db import db
from utils.logger import get_logger
from functools import wraps
import json

bot_control_bp = Blueprint('bot_control', __name__, url_prefix='/api/bot')
logger = get_logger('bot_control_api')

# Global trading engine instance
trading_engine = None

def get_trading_engine():
    """Get or create trading engine instance"""
    global trading_engine
    if trading_engine is None:
        trading_engine = TradingEngine(testnet=True)
    return trading_engine

def user_required(f):
    """Decorator to require user authentication"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        return f(user, *args, **kwargs)
    return decorated_function

@bot_control_bp.route('/status', methods=['GET'])
@user_required
def get_bot_status(user):
    """Get status of all user's bots"""
    try:
        engine = get_trading_engine()
        active_bots = engine.get_active_bots(user.id)
        
        bot_statuses = []
        for bot_data in active_bots:
            bot = Bot.query.get(bot_data['bot_id'])
            if bot:
                status = {
                    'bot_id': bot.id,
                    'name': bot.name,
                    'strategy': bot.strategy,
                    'symbol': bot.symbol,
                    'is_active': bot.is_active,
                    'created_at': bot.created_at.isoformat(),
                    'last_trade': bot.last_trade_at.isoformat() if bot.last_trade_at else None,
                    'total_trades': bot.total_trades,
                    'profit_loss': float(bot.total_profit_loss),
                    'win_rate': float(bot.win_rate) if bot.win_rate else 0.0
                }
                bot_statuses.append(status)
        
        return jsonify({
            'success': True,
            'data': {
                'bots': bot_statuses,
                'total_active': len([b for b in bot_statuses if b['is_active']]),
                'total_bots': len(bot_statuses)
            }
        })
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get bot status'
        }), 500

@bot_control_bp.route('/start', methods=['POST'])
@user_required
def start_bot(user):
    """Start a trading bot"""
    try:
        data = request.get_json()
        bot_id = data.get('bot_id')
        
        if not bot_id:
            return jsonify({
                'success': False,
                'error': 'Bot ID is required'
            }), 400
        
        bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
        if not bot:
            return jsonify({
                'success': False,
                'error': 'Bot not found'
            }), 404
        
        if bot.is_active:
            return jsonify({
                'success': False,
                'error': 'Bot is already running'
            }), 400
        
        # Create bot configuration
        bot_config = TradingBotConfig(
            user_id=user.id,
            bot_id=bot.id,
            strategy_name=bot.strategy,
            symbol=bot.symbol,
            timeframe=bot.timeframe,
            parameters=json.loads(bot.parameters) if bot.parameters else {},
            risk_settings=json.loads(bot.risk_settings) if bot.risk_settings else {}
        )
        
        # Start the bot
        engine = get_trading_engine()
        result = engine.start_bot(bot_config)
        
        if result['success']:
            bot.is_active = True
            bot.started_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Bot {bot.name} started successfully',
                'data': {
                    'bot_id': bot.id,
                    'status': 'running'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to start bot')
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start bot'
        }), 500

@bot_control_bp.route('/stop', methods=['POST'])
@user_required
def stop_bot(user):
    """Stop a trading bot"""
    try:
        data = request.get_json()
        bot_id = data.get('bot_id')
        
        if not bot_id:
            return jsonify({
                'success': False,
                'error': 'Bot ID is required'
            }), 400
        
        bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
        if not bot:
            return jsonify({
                'success': False,
                'error': 'Bot not found'
            }), 404
        
        if not bot.is_active:
            return jsonify({
                'success': False,
                'error': 'Bot is not running'
            }), 400
        
        # Stop the bot
        engine = get_trading_engine()
        result = engine.stop_bot(bot.id)
        
        if result['success']:
            bot.is_active = False
            bot.stopped_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Bot {bot.name} stopped successfully',
                'data': {
                    'bot_id': bot.id,
                    'status': 'stopped'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to stop bot')
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to stop bot'
        }), 500

@bot_control_bp.route('/balance', methods=['GET'])
@user_required
def get_balance(user):
    """Get user's trading balance"""
    try:
        engine = get_trading_engine()
        balance_data = engine.get_balance()
        
        # Calculate total portfolio value
        total_value = 0
        balances = []
        
        for currency, amount in balance_data.items():
            if amount > 0:
                # Get current price for non-USD currencies
                if currency == 'USD' or currency == 'USDT':
                    usd_value = amount
                    price = 1.0
                else:
                    try:
                        ticker = engine.get_ticker(f"{currency}/USDT")
                        price = ticker['last']
                        usd_value = amount * price
                    except:
                        price = 0
                        usd_value = 0
                
                total_value += usd_value
                balances.append({
                    'currency': currency,
                    'amount': amount,
                    'usd_value': usd_value,
                    'price': price
                })
        
        # Get daily change (mock data for now)
        daily_change = 0.0  # This would be calculated from historical data
        daily_change_percent = 0.0
        
        return jsonify({
            'success': True,
            'data': {
                'total_value': total_value,
                'daily_change': daily_change,
                'daily_change_percent': daily_change_percent,
                'balances': balances,
                'last_updated': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get balance'
        }), 500

@bot_control_bp.route('/pnl', methods=['GET'])
@user_required
def get_pnl(user):
    """Get profit and loss data"""
    try:
        # Get time range from query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get trades for the user
        trades = Trade.query.filter(
            Trade.user_id == user.id,
            Trade.created_at >= start_date
        ).order_by(Trade.created_at.desc()).all()
        
        total_pnl = 0
        winning_trades = 0
        losing_trades = 0
        trade_data = []
        
        for trade in trades:
            pnl = float(trade.profit_loss) if trade.profit_loss else 0
            total_pnl += pnl
            
            if pnl > 0:
                winning_trades += 1
            elif pnl < 0:
                losing_trades += 1
            
            trade_data.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'amount': float(trade.amount),
                'price': float(trade.price),
                'pnl': pnl,
                'created_at': trade.created_at.isoformat()
            })
        
        total_trades = len(trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'trades': trade_data[:50]  # Limit to 50 recent trades
            }
        })
    except Exception as e:
        logger.error(f"Error getting PnL data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get PnL data'
        }), 500

@bot_control_bp.route('/trading-pairs', methods=['GET'])
@user_required
def get_trading_pairs(user):
    """Get available trading pairs"""
    try:
        engine = get_trading_engine()
        markets = engine.get_markets()
        
        # Filter for active markets
        active_pairs = []
        for symbol, market in markets.items():
            if market.get('active', False):
                active_pairs.append({
                    'symbol': symbol,
                    'base': market.get('base'),
                    'quote': market.get('quote'),
                    'active': market.get('active'),
                    'type': market.get('type'),
                    'spot': market.get('spot', False),
                    'future': market.get('future', False)
                })
        
        # Sort by popularity (volume)
        popular_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT']
        sorted_pairs = []
        
        # Add popular pairs first
        for pair in popular_pairs:
            for market in active_pairs:
                if market['symbol'] == pair:
                    sorted_pairs.append(market)
                    break
        
        # Add remaining pairs
        for market in active_pairs:
            if market not in sorted_pairs:
                sorted_pairs.append(market)
        
        return jsonify({
            'success': True,
            'data': {
                'pairs': sorted_pairs[:100],  # Limit to 100 pairs
                'total_pairs': len(active_pairs)
            }
        })
    except Exception as e:
        logger.error(f"Error getting trading pairs: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get trading pairs'
        }), 500

@bot_control_bp.route('/strategies', methods=['GET'])
@user_required
def get_strategies(user):
    """Get available trading strategies"""
    try:
        strategies = [
            {
                'name': 'rsi_strategy',
                'display_name': 'RSI Strategy',
                'description': 'Uses RSI indicator for overbought/oversold signals',
                'parameters': {
                    'rsi_period': {'type': 'int', 'default': 14, 'min': 5, 'max': 50},
                    'rsi_overbought': {'type': 'float', 'default': 70, 'min': 60, 'max': 90},
                    'rsi_oversold': {'type': 'float', 'default': 30, 'min': 10, 'max': 40}
                }
            },
            {
                'name': 'ema_crossover',
                'display_name': 'EMA Crossover',
                'description': 'Uses exponential moving average crossovers',
                'parameters': {
                    'fast_period': {'type': 'int', 'default': 12, 'min': 5, 'max': 50},
                    'slow_period': {'type': 'int', 'default': 26, 'min': 10, 'max': 100}
                }
            },
            {
                'name': 'macd_strategy',
                'display_name': 'MACD Strategy',
                'description': 'Uses MACD indicator for trend following',
                'parameters': {
                    'fast_period': {'type': 'int', 'default': 12, 'min': 5, 'max': 50},
                    'slow_period': {'type': 'int', 'default': 26, 'min': 10, 'max': 100},
                    'signal_period': {'type': 'int', 'default': 9, 'min': 5, 'max': 20}
                }
            },
            {
                'name': 'scalping_strategy',
                'display_name': 'Scalping Strategy',
                'description': 'High-frequency trading for small profits',
                'parameters': {
                    'profit_target': {'type': 'float', 'default': 0.5, 'min': 0.1, 'max': 2.0},
                    'stop_loss': {'type': 'float', 'default': 0.3, 'min': 0.1, 'max': 1.0}
                }
            },
            {
                'name': 'swing_trading',
                'display_name': 'Swing Trading',
                'description': 'Medium-term trading strategy',
                'parameters': {
                    'profit_target': {'type': 'float', 'default': 3.0, 'min': 1.0, 'max': 10.0},
                    'stop_loss': {'type': 'float', 'default': 2.0, 'min': 0.5, 'max': 5.0}
                }
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'strategies': strategies
            }
        })
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get strategies'
        }), 500

@bot_control_bp.route('/create', methods=['POST'])
@user_required
def create_bot(user):
    """Create a new trading bot"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'strategy', 'symbol', 'timeframe']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Create new bot
        bot = Bot(
            user_id=user.id,
            name=data['name'],
            strategy=data['strategy'],
            symbol=data['symbol'],
            timeframe=data['timeframe'],
            parameters=json.dumps(data.get('parameters', {})),
            risk_settings=json.dumps(data.get('risk_settings', {})),
            is_active=False
        )
        
        db.session.add(bot)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bot created successfully',
            'data': {
                'bot_id': bot.id,
                'name': bot.name,
                'strategy': bot.strategy,
                'symbol': bot.symbol
            }
        })
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create bot'
        }), 500

@bot_control_bp.route('/update/<bot_id>', methods=['PUT'])
@user_required
def update_bot(user, bot_id):
    """Update bot configuration"""
    try:
        bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
        if not bot:
            return jsonify({
                'success': False,
                'error': 'Bot not found'
            }), 404
        
        if bot.is_active:
            return jsonify({
                'success': False,
                'error': 'Cannot update active bot. Stop the bot first.'
            }), 400
        
        data = request.get_json()
        
        # Update bot fields
        if 'name' in data:
            bot.name = data['name']
        if 'strategy' in data:
            bot.strategy = data['strategy']
        if 'symbol' in data:
            bot.symbol = data['symbol']
        if 'timeframe' in data:
            bot.timeframe = data['timeframe']
        if 'parameters' in data:
            bot.parameters = json.dumps(data['parameters'])
        if 'risk_settings' in data:
            bot.risk_settings = json.dumps(data['risk_settings'])
        
        bot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bot updated successfully',
            'data': {
                'bot_id': bot.id,
                'name': bot.name,
                'strategy': bot.strategy,
                'symbol': bot.symbol
            }
        })
    except Exception as e:
        logger.error(f"Error updating bot: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update bot'
        }), 500

@bot_control_bp.route('/delete/<bot_id>', methods=['DELETE'])
@user_required
def delete_bot(user, bot_id):
    """Delete a trading bot"""
    try:
        bot = Bot.query.filter_by(id=bot_id, user_id=user.id).first()
        if not bot:
            return jsonify({
                'success': False,
                'error': 'Bot not found'
            }), 404
        
        if bot.is_active:
            return jsonify({
                'success': False,
                'error': 'Cannot delete active bot. Stop the bot first.'
            }), 400
        
        db.session.delete(bot)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bot deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting bot: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete bot'
        }), 500