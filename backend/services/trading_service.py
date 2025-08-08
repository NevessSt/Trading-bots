"""Trading service for bot and trade management."""

from flask import current_app
from datetime import datetime, timedelta
from decimal import Decimal
from models import Bot, Trade, APIKey, User, db
from typing import Dict, List, Optional
import json


class TradingService:
    """Service for handling trading operations."""
    
    @staticmethod
    def create_bot(user_id, bot_data_or_name, strategy=None, trading_pair=None, config=None, api_key_id=None):
        """Create a new trading bot.
        
        Args:
            user_id: ID of the user creating the bot
            bot_data_or_name: Either a dictionary with bot data or the bot name string
            strategy: Bot strategy (if bot_data_or_name is a string)
            trading_pair: Trading pair (if bot_data_or_name is a string)
            config: Bot configuration (if bot_data_or_name is a string)
            api_key_id: API key ID (if bot_data_or_name is a string)
        """
        # Handle dictionary format
        if isinstance(bot_data_or_name, dict):
            bot_data = bot_data_or_name
            name = bot_data.get('name')
            strategy = bot_data.get('strategy')
            trading_pair = bot_data.get('symbol') or bot_data.get('trading_pair')
            config = bot_data.get('config', {})
            api_key_id = bot_data.get('api_key_id')
        else:
            # Handle individual parameters
            name = bot_data_or_name
        
        # Validate user exists
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Validate API key if provided
        if api_key_id:
            api_key = APIKey.query.filter_by(id=api_key_id, user_id=user_id).first()
            if not api_key or not api_key.is_active:
                raise ValueError("Invalid or inactive API key")
        
        # Create bot
        bot = Bot(
            user_id=user_id,
            name=name,
            strategy=strategy,
            symbol=trading_pair or 'BTCUSDT',  # Default symbol if not provided
            base_amount=config.get('initial_balance', 1000) if isinstance(config, dict) else 1000,
            api_key_id=api_key_id
        )
        
        # Set additional configuration if provided
        if isinstance(config, dict):
            bot.set_strategy_config(config)
        
        db.session.add(bot)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Bot created successfully',
            'bot': {
                'id': bot.id,
                'name': bot.name,
                'strategy': bot.strategy,
                'symbol': bot.symbol,
                'status': 'stopped'  # Default status for new bots
            }
        }
    
    @staticmethod
    def get_user_bots(user_id, status=None, limit=10, offset=0):
        """Get bots for a user with optional filtering."""
        query = Bot.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Bot.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_bot_by_id(bot_id, user_id):
        """Get bot by ID, ensuring it belongs to the user."""
        return Bot.query.filter_by(id=bot_id, user_id=user_id).first()
    
    @staticmethod
    def update_bot_config(bot_id, user_id, config):
        """Update bot configuration."""
        bot = TradingService.get_bot_by_id(bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        bot.config = config
        bot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return bot
    
    @staticmethod
    def start_bot(bot_id, user_id):
        """Start a trading bot."""
        bot = TradingService.get_bot_by_id(bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        if bot.status == 'running':
            raise ValueError("Bot is already running")
        
        bot.status = 'running'
        bot.is_active = True
        bot.last_run_at = datetime.utcnow()
        bot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return bot
    
    @staticmethod
    def stop_bot(bot_id, user_id):
        """Stop a trading bot."""
        bot = TradingService.get_bot_by_id(bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        bot.status = 'stopped'
        bot.is_active = False
        bot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return bot
    
    @staticmethod
    def pause_bot(bot_id, user_id):
        """Pause a trading bot."""
        bot = TradingService.get_bot_by_id(bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        bot.status = 'paused'
        bot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return bot
    
    @staticmethod
    def delete_bot(bot_id, user_id):
        """Delete a trading bot."""
        bot = TradingService.get_bot_by_id(bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        # Stop bot if running
        if bot.status == 'running':
            TradingService.stop_bot(bot_id, user_id)
        
        db.session.delete(bot)
        db.session.commit()
        
        return True
    
    @staticmethod
    def create_trade(bot_id, user_id, trading_pair, side, quantity, price, **kwargs):
        """Create a new trade record."""
        # Validate bot belongs to user
        bot = TradingService.get_bot_by_id(bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        # Calculate total value
        total_value = Decimal(str(quantity)) * Decimal(str(price))
        
        trade = Trade(
            bot_id=bot_id,
            user_id=user_id,
            trading_pair=trading_pair,
            side=side,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            total_value=total_value,
            **kwargs
        )
        
        db.session.add(trade)
        db.session.commit()
        
        # Update bot statistics
        TradingService._update_bot_stats(bot)
        
        return trade
    
    @staticmethod
    def get_user_trades(user_id, bot_id=None, limit=50, offset=0):
        """Get trades for a user with optional bot filtering."""
        query = Trade.query.filter_by(user_id=user_id)
        
        if bot_id:
            query = query.filter_by(bot_id=bot_id)
        
        return query.order_by(Trade.executed_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_bot_performance(bot_id, user_id):
        """Get performance metrics for a bot."""
        bot = TradingService.get_bot_by_id(bot_id, user_id)
        if not bot:
            raise ValueError("Bot not found")
        
        trades = Trade.query.filter_by(bot_id=bot_id).all()
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_profit_loss': Decimal('0'),
                'win_rate': 0,
                'average_profit': Decimal('0'),
                'average_loss': Decimal('0')
            }
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.profit_loss > 0])
        losing_trades = len([t for t in trades if t.profit_loss < 0])
        total_profit_loss = sum(t.profit_loss for t in trades)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        winning_amounts = [t.profit_loss for t in trades if t.profit_loss > 0]
        losing_amounts = [t.profit_loss for t in trades if t.profit_loss < 0]
        
        average_profit = sum(winning_amounts) / len(winning_amounts) if winning_amounts else Decimal('0')
        average_loss = sum(losing_amounts) / len(losing_amounts) if losing_amounts else Decimal('0')
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_profit_loss': total_profit_loss,
            'win_rate': round(win_rate, 2),
            'average_profit': average_profit,
            'average_loss': average_loss
        }
    
    @staticmethod
    def _update_bot_stats(bot):
        """Update bot statistics after a trade."""
        trades = Trade.query.filter_by(bot_id=bot.id).all()
        
        bot.total_trades = len(trades)
        bot.winning_trades = len([t for t in trades if t.profit_loss > 0])
        bot.total_profit_loss = sum(t.profit_loss for t in trades)
        
        if bot.total_trades > 0:
            bot.win_rate = (bot.winning_trades / bot.total_trades) * 100
        else:
            bot.win_rate = 0
        
        bot.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def validate_trading_pair(trading_pair):
        """Validate trading pair format."""
        # Basic validation - should be like BTC/USDT, ETH/BTC, etc.
        if '/' not in trading_pair:
            return False
        
        parts = trading_pair.split('/')
        if len(parts) != 2:
            return False
        
        base, quote = parts
        if not base or not quote:
            return False
        
        return True
    
    @staticmethod
    def get_supported_strategies():
        """Get list of supported trading strategies."""
        return [
            'grid',
            'dca',
            'scalping',
            'sma_crossover',
            'rsi_oversold',
            'bollinger_bands',
            'macd_signal'
        ]