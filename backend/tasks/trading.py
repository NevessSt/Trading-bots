"""Trading-related Celery tasks for async execution."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from celery import Task
from celery.exceptions import Retry

from celery_app import celery_app
from models.trade import Trade
from models.bot import Bot
from models.user import User
from bot_engine.trading_engine import TradingEngine
from bot_engine.exchange_manager import ExchangeManager
from bot_engine.market_data_manager import MarketDataManager
from bot_engine.portfolio_manager import PortfolioManager
from services.notification_service import NotificationService
from utils.logging_config import get_trade_logger
from database import db

logger = get_trade_logger()

class TradingTask(Task):
    """Base class for trading tasks with error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Trading task {task_id} failed: {exc}")
        # Send failure notification
        try:
            notification_service = NotificationService()
            notification_service.send_system_alert(
                f"Trading task failed: {task_id}",
                f"Error: {str(exc)}",
                severity='high'
            )
        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")

@celery_app.task(bind=True, base=TradingTask, max_retries=3, default_retry_delay=60)
def execute_trade_async(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a trade asynchronously.
    
    Args:
        trade_data: Dictionary containing trade parameters
            - user_id: User ID
            - bot_id: Bot ID
            - symbol: Trading pair
            - side: 'buy' or 'sell'
            - quantity: Amount to trade
            - order_type: 'market', 'limit', etc.
            - price: Price for limit orders (optional)
            - stop_loss: Stop loss price (optional)
            - take_profit: Take profit price (optional)
    
    Returns:
        Dictionary with execution results
    """
    try:
        logger.info(f"Starting async trade execution: {trade_data}")
        
        # Validate required parameters
        required_fields = ['user_id', 'bot_id', 'symbol', 'side', 'quantity', 'order_type']
        for field in required_fields:
            if field not in trade_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Get bot and user
        bot = Bot.query.get(trade_data['bot_id'])
        if not bot:
            raise ValueError(f"Bot not found: {trade_data['bot_id']}")
        
        user = User.query.get(trade_data['user_id'])
        if not user:
            raise ValueError(f"User not found: {trade_data['user_id']}")
        
        # Initialize trading engine
        exchange_manager = ExchangeManager()
        exchange = exchange_manager.get_exchange(bot.exchange, user.id)
        
        trading_engine = TradingEngine(
            exchange=exchange,
            user_id=user.id,
            bot_id=bot.id
        )
        
        # Create trade record
        trade = Trade(
            user_id=trade_data['user_id'],
            bot_id=trade_data['bot_id'],
            symbol=trade_data['symbol'],
            side=trade_data['side'],
            quantity=float(trade_data['quantity']),
            order_type=trade_data['order_type'],
            price=float(trade_data.get('price', 0)) if trade_data.get('price') else None,
            stop_loss=float(trade_data.get('stop_loss', 0)) if trade_data.get('stop_loss') else None,
            take_profit=float(trade_data.get('take_profit', 0)) if trade_data.get('take_profit') else None,
            status='pending'
        )
        
        db.session.add(trade)
        db.session.commit()
        
        # Execute the trade
        if trade_data['order_type'] == 'market':
            result = trading_engine.execute_market_order(
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                quantity=float(trade_data['quantity'])
            )
        elif trade_data['order_type'] == 'limit':
            if not trade_data.get('price'):
                raise ValueError("Price required for limit orders")
            result = trading_engine.execute_limit_order(
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                quantity=float(trade_data['quantity']),
                price=float(trade_data['price'])
            )
        else:
            raise ValueError(f"Unsupported order type: {trade_data['order_type']}")
        
        # Update trade record
        trade.status = 'completed' if result.get('success') else 'failed'
        trade.executed_at = datetime.utcnow()
        trade.executed_price = result.get('price')
        trade.executed_quantity = result.get('quantity')
        trade.fees = result.get('fees', 0)
        trade.order_id = result.get('order_id')
        
        if not result.get('success'):
            trade.error_message = result.get('error', 'Unknown error')
        
        db.session.commit()
        
        # Send notification
        send_trade_notification.delay({
            'trade_id': trade.id,
            'user_id': user.id,
            'success': result.get('success', False),
            'symbol': trade_data['symbol'],
            'side': trade_data['side'],
            'quantity': trade_data['quantity'],
            'price': result.get('price')
        })
        
        logger.info(f"Trade execution completed: {trade.id}")
        
        return {
            'success': True,
            'trade_id': trade.id,
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Trade execution failed: {exc}")
        
        # Update trade record if it exists
        if 'trade' in locals():
            trade.status = 'failed'
            trade.error_message = str(exc)
            db.session.commit()
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying trade execution (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(exc),
            'trade_id': locals().get('trade', {}).get('id')
        }

@celery_app.task(bind=True, max_retries=2)
def update_market_data(self, symbols: Optional[List[str]] = None):
    """Update market data for specified symbols or all active symbols."""
    try:
        logger.info("Starting market data update")
        
        if not symbols:
            # Get all active trading pairs from bots
            active_bots = Bot.query.filter_by(is_active=True).all()
            symbols = list(set([bot.trading_pair for bot in active_bots if bot.trading_pair]))
        
        if not symbols:
            logger.info("No symbols to update")
            return {'success': True, 'updated_symbols': []}
        
        market_data_manager = MarketDataManager()
        updated_symbols = []
        
        for symbol in symbols:
            try:
                # Update price data
                price_data = market_data_manager.get_current_price(symbol)
                if price_data:
                    market_data_manager.cache_price_data(symbol, price_data)
                    updated_symbols.append(symbol)
                    
                # Update order book
                order_book = market_data_manager.get_order_book(symbol)
                if order_book:
                    market_data_manager.cache_order_book(symbol, order_book)
                    
            except Exception as e:
                logger.error(f"Failed to update data for {symbol}: {e}")
                continue
        
        logger.info(f"Market data update completed for {len(updated_symbols)} symbols")
        
        return {
            'success': True,
            'updated_symbols': updated_symbols,
            'total_symbols': len(symbols)
        }
        
    except Exception as exc:
        logger.error(f"Market data update failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30)
        
        return {'success': False, 'error': str(exc)}

@celery_app.task(bind=True, max_retries=2)
def sync_portfolios(self):
    """Sync portfolio data for all active users."""
    try:
        logger.info("Starting portfolio sync")
        
        # Get all users with active bots
        users_with_bots = db.session.query(User).join(Bot).filter(
            Bot.is_active == True
        ).distinct().all()
        
        synced_users = []
        exchange_manager = ExchangeManager()
        
        for user in users_with_bots:
            try:
                # Get user's exchanges
                user_bots = Bot.query.filter_by(user_id=user.id, is_active=True).all()
                exchanges = list(set([bot.exchange for bot in user_bots]))
                
                for exchange_name in exchanges:
                    try:
                        exchange = exchange_manager.get_exchange(exchange_name, user.id)
                        portfolio_manager = PortfolioManager(exchange, user.id)
                        
                        # Sync portfolio
                        portfolio_data = portfolio_manager.get_portfolio_summary()
                        if portfolio_data:
                            portfolio_manager.update_portfolio_cache(portfolio_data)
                            
                    except Exception as e:
                        logger.error(f"Failed to sync {exchange_name} for user {user.id}: {e}")
                        continue
                
                synced_users.append(user.id)
                
            except Exception as e:
                logger.error(f"Failed to sync portfolio for user {user.id}: {e}")
                continue
        
        logger.info(f"Portfolio sync completed for {len(synced_users)} users")
        
        return {
            'success': True,
            'synced_users': len(synced_users),
            'total_users': len(users_with_bots)
        }
        
    except Exception as exc:
        logger.error(f"Portfolio sync failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60)
        
        return {'success': False, 'error': str(exc)}

@celery_app.task
def process_order_book(symbol: str, depth: int = 20):
    """Process and analyze order book data."""
    try:
        logger.info(f"Processing order book for {symbol}")
        
        market_data_manager = MarketDataManager()
        order_book = market_data_manager.get_order_book(symbol, depth)
        
        if not order_book:
            return {'success': False, 'error': 'Failed to fetch order book'}
        
        # Analyze order book
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'best_bid': order_book['bids'][0][0] if order_book['bids'] else None,
            'best_ask': order_book['asks'][0][0] if order_book['asks'] else None,
            'spread': None,
            'bid_volume': sum([bid[1] for bid in order_book['bids'][:5]]),
            'ask_volume': sum([ask[1] for ask in order_book['asks'][:5]]),
        }
        
        if analysis['best_bid'] and analysis['best_ask']:
            analysis['spread'] = analysis['best_ask'] - analysis['best_bid']
            analysis['spread_percent'] = (analysis['spread'] / analysis['best_ask']) * 100
        
        # Cache analysis
        market_data_manager.cache_order_book_analysis(symbol, analysis)
        
        return {'success': True, 'analysis': analysis}
        
    except Exception as exc:
        logger.error(f"Order book processing failed for {symbol}: {exc}")
        return {'success': False, 'error': str(exc)}

@celery_app.task
def calculate_indicators(symbol: str, timeframe: str = '1h', indicators: List[str] = None):
    """Calculate technical indicators for a symbol."""
    try:
        if not indicators:
            indicators = ['sma_20', 'ema_12', 'rsi_14', 'macd']
        
        logger.info(f"Calculating indicators for {symbol}: {indicators}")
        
        market_data_manager = MarketDataManager()
        
        # Get historical data
        historical_data = market_data_manager.get_historical_data(
            symbol, timeframe, limit=100
        )
        
        if not historical_data:
            return {'success': False, 'error': 'Failed to fetch historical data'}
        
        # Calculate indicators
        indicator_results = {}
        
        for indicator in indicators:
            try:
                if indicator.startswith('sma_'):
                    period = int(indicator.split('_')[1])
                    indicator_results[indicator] = market_data_manager.calculate_sma(
                        historical_data, period
                    )
                elif indicator.startswith('ema_'):
                    period = int(indicator.split('_')[1])
                    indicator_results[indicator] = market_data_manager.calculate_ema(
                        historical_data, period
                    )
                elif indicator.startswith('rsi_'):
                    period = int(indicator.split('_')[1])
                    indicator_results[indicator] = market_data_manager.calculate_rsi(
                        historical_data, period
                    )
                elif indicator == 'macd':
                    indicator_results[indicator] = market_data_manager.calculate_macd(
                        historical_data
                    )
                    
            except Exception as e:
                logger.error(f"Failed to calculate {indicator}: {e}")
                continue
        
        # Cache results
        market_data_manager.cache_indicators(symbol, timeframe, indicator_results)
        
        return {
            'success': True,
            'symbol': symbol,
            'timeframe': timeframe,
            'indicators': indicator_results
        }
        
    except Exception as exc:
        logger.error(f"Indicator calculation failed for {symbol}: {exc}")
        return {'success': False, 'error': str(exc)}