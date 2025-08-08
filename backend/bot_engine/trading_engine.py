import ccxt
import pandas as pd
import numpy as np
import time
import uuid
import asyncio
import websockets
import json
from datetime import datetime, timedelta
from threading import Thread
from flask import current_app
import os
from ccxt.base.errors import BaseError, NetworkError, ExchangeError, InvalidOrder, InsufficientFunds
from concurrent.futures import ThreadPoolExecutor

# Import strategies
from .strategies.rsi_strategy import RSIStrategy
from .strategies.macd_strategy import MACDStrategy
from .strategies.ema_crossover_strategy import EMACrossoverStrategy

# Import risk manager
from .risk_manager import RiskManager

# Import models
from models.trade import Trade
from models.user import User
from models.bot import Bot

# Import utils
from utils.notification import NotificationManager
from utils.logger import logger
from utils.security import security_manager

class TradingEngine:
    """Main trading engine that manages all trading operations"""
    
    def __init__(self, api_key=None, api_secret=None, testnet=None):
        """Initialize the trading engine
        
        Args:
            api_key (str, optional): Binance API key
            api_secret (str, optional): Binance API secret
            testnet (bool, optional): Use testnet environment
        """
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        self.testnet = testnet if testnet is not None else os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
        self.exchange = None
        self.active_bots = {}  # Dict of active bots: {bot_id: bot_thread}
        self.websocket_connections = {}  # Dict of WebSocket connections: {symbol: connection}
        self.real_time_data = {}  # Dict of real-time price data: {symbol: latest_data}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.strategies = {
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'ema_crossover': EMACrossoverStrategy
        }
        self.notification_manager = NotificationManager()
        
        # Initialize exchange if API credentials are provided
        if self.api_key and self.api_secret:
            try:
                self.initialize_exchange()
                logger.info(f"Trading engine initialized - Testnet: {self.testnet}")
            except Exception as e:
                logger.error(f"Failed to initialize trading engine: {str(e)}")
                raise
    
    def initialize_exchange(self):
        """Initialize the Binance exchange connection"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API key and secret are required")
            
            # Validate API key format
            if not security_manager.validate_api_keys(self.api_key, self.api_secret):
                raise ValueError("Invalid API key format")
            
            self.exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'sandbox': self.testnet,
                'enableRateLimit': True,
                'timeout': 30000,  # 30 seconds timeout
                'rateLimit': 1200,  # 1200ms between requests
            })
            
            # Test connection
            self.exchange.load_markets()
            
            # Test API permissions
            account_info = self.exchange.fetch_balance()
            
            logger.info(f"Exchange connection established - Testnet: {self.testnet}")
            
        except ccxt.AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            raise ValueError("Invalid API credentials")
        except ccxt.NetworkError as e:
            logger.error(f"Network error: {str(e)}")
            raise ConnectionError("Failed to connect to exchange")
        except Exception as e:
            logger.error(f"Error initializing exchange: {str(e)}")
            self.exchange = None
            raise
    
    def get_active_bots(self, user_id):
        """Get active bots for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of active bot IDs
        """
        user = User.find_by_id(user_id)
        if not user:
            return []
        
        return user.get('settings', {}).get('active_bots', [])
    
    def start_bot(self, user_id, symbol, strategy, interval, amount, take_profit, stop_loss):
        """Start a new trading bot
        
        Args:
            user_id (str): User ID
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            strategy (str): Strategy ID
            interval (str): Candlestick interval (e.g., '1h', '4h', '1d')
            amount (float): Amount to trade
            take_profit (float): Take profit percentage
            stop_loss (float): Stop loss percentage
            
        Returns:
            str: Bot ID
        """
        try:
            # Validate parameters
            if not self.exchange:
                logger.error("Exchange not initialized")
                raise Exception("Exchange not initialized")
            
            if strategy not in self.strategies:
                logger.error(f"Strategy '{strategy}' not found")
                raise Exception(f"Strategy '{strategy}' not found")
            
            # Validate symbol
            if symbol not in self.exchange.markets:
                logger.error(f"Symbol '{symbol}' not available on exchange")
                raise Exception(f"Symbol '{symbol}' not available on exchange")
            
            # Validate parameters
            if amount <= 0:
                logger.error(f"Invalid amount: {amount}")
                raise Exception(f"Invalid amount: {amount}")
            
            if take_profit <= 0 or stop_loss <= 0:
                logger.error(f"Invalid take_profit ({take_profit}) or stop_loss ({stop_loss})")
                raise Exception(f"Invalid take_profit ({take_profit}) or stop_loss ({stop_loss})")
            
            # Check if user already has a bot running for this symbol
            for existing_bot_id, bot_info in self.active_bots.items():
                if (bot_info['config']['user_id'] == user_id and 
                    bot_info['config']['symbol'] == symbol and 
                    bot_info['is_running']):
                    logger.warning(f"User {user_id} already has a bot running for {symbol}")
                    raise Exception(f"Bot already running for {symbol}")
            
            # Generate bot ID
            bot_id = str(uuid.uuid4())
            
            # Create bot configuration
            bot_config = {
                'id': bot_id,
                'user_id': user_id,
                'symbol': symbol,
                'strategy': strategy,
                'interval': interval,
                'amount': amount,
                'take_profit': take_profit,
                'stop_loss': stop_loss,
                'is_running': True,
                'created_at': datetime.utcnow()
            }
            
            # Create bot thread
            bot_thread = Thread(
                target=self._run_bot,
                args=(bot_config,),
                daemon=True
            )
            
            # Store bot thread
            self.active_bots[bot_id] = {
                'thread': bot_thread,
                'config': bot_config,
                'is_running': True
            }
            
            # Start bot thread
            bot_thread.start()
            
            # Log bot start
            logger.info(f"Bot {bot_id} started for user {user_id} - Symbol: {symbol}, Strategy: {strategy}, Amount: {amount}")
            
            # Notify user
            self.notification_manager.send_notification(
                user_id,
                f"Trading bot started for {symbol} using {strategy} strategy"
            )
            
            return bot_id
            
        except Exception as e:
            logger.error(f"Error starting bot for user {user_id}: {str(e)}")
            raise
    
    def stop_bot(self, user_id, bot_id):
        """Stop a trading bot
        
        Args:
            user_id (str): User ID
            bot_id (str): Bot ID
            
        Returns:
            bool: True if bot was stopped, False otherwise
        """
        if bot_id not in self.active_bots:
            return False
        
        # Check if bot belongs to user
        bot_config = self.active_bots[bot_id]['config']
        if bot_config['user_id'] != user_id:
            return False
        
        # Set bot to stop
        self.active_bots[bot_id]['is_running'] = False
        self.active_bots[bot_id]['config']['is_running'] = False
        
        # Notify user
        self.notification_manager.send_notification(
            user_id,
            f"Trading bot stopped for {bot_config['symbol']}"
        )
        
        return True
    
    def stop_all_bots(self, user_id):
        """Stop all trading bots for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of stopped bot IDs
        """
        stopped_bots = []
        
        for bot_id, bot_data in list(self.active_bots.items()):
            if bot_data['config']['user_id'] == user_id:
                if self.stop_bot(user_id, bot_id):
                    stopped_bots.append(bot_id)
        
        return stopped_bots
    
    def _run_bot(self, bot_config):
        """Run a trading bot (executed in a separate thread)
        
        Args:
            bot_config (dict): Bot configuration
        """
        bot_id = bot_config['id']
        user_id = bot_config['user_id']
        symbol = bot_config['symbol']
        strategy_id = bot_config['strategy']
        interval = bot_config['interval']
        
        # Initialize strategy
        strategy_class = self.strategies[strategy_id]
        strategy = strategy_class()
        
        # Initialize risk manager
        risk_manager = RiskManager(user_id)
        
        print(f"Bot {bot_id} started for {symbol} using {strategy_id} strategy")
        
        # Trading loop
        while self.active_bots.get(bot_id, {}).get('is_running', False):
            try:
                # Fetch market data
                ohlcv = self.exchange.fetch_ohlcv(symbol, interval)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Generate signals
                signals = strategy.generate_signals(df)
                
                # Get last signal
                last_signal = signals.iloc[-1]['signal'] if not signals.empty else 0
                
                # Check if we should execute a trade
                if last_signal != 0:
                    # Enhanced risk management checks
                    if not risk_manager.can_trade(user_id, symbol, bot_config['amount'], last_signal > 0):
                        logger.warning(f"Trade blocked by risk management for bot {bot_id}")
                        continue
                    
                    # Check daily loss limit
                    if not risk_manager.check_daily_loss_limit(user_id):
                        logger.warning(f"Daily loss limit exceeded for user {user_id}, bot {bot_id}")
                        continue
                    
                    # Check position exposure
                    if not risk_manager.check_position_exposure(user_id, symbol, bot_config['amount']):
                        logger.warning(f"Position exposure limit exceeded for user {user_id}, symbol {symbol}")
                        continue
                    
                    # Execute trade
                    trade_result = self._execute_trade(
                        user_id=user_id,
                        symbol=symbol,
                        amount=bot_config['amount'],
                        side='buy' if last_signal > 0 else 'sell',
                        take_profit=bot_config['take_profit'],
                        stop_loss=bot_config['stop_loss']
                    )
                    
                    # Record trade
                    if trade_result:
                        trade_id = Trade.create({
                            'user_id': user_id,
                            'bot_id': bot_id,
                            'symbol': symbol,
                            'type': 'buy' if last_signal > 0 else 'sell',
                            'amount': bot_config['amount'],
                            'price': trade_result['price'],
                            'quantity': trade_result['quantity'],
                            'fee': trade_result['fee'],
                            'timestamp': datetime.utcnow(),
                            'status': 'completed',
                            'order_id': trade_result['order_id']
                        })
                        
                        # Notify user
                        self.notification_manager.send_notification(
                            user_id,
                            f"Trade executed: {trade_result['side']} {trade_result['quantity']} {symbol} at {trade_result['price']}"
                        )
                
                # Check open positions for stop-loss/take-profit
                self._monitor_open_positions(user_id)
                
                # Sleep before next iteration
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in bot {bot_id}: {str(e)}")
                time.sleep(60)  # Wait before retrying
        
        print(f"Bot {bot_id} stopped")
    
    def _monitor_open_positions(self, user_id):
        """Monitor open positions for stop-loss and take-profit conditions"""
        try:
            # Get open positions from risk manager
            open_positions = self.risk_manager._get_open_positions(user_id)
            
            for position in open_positions:
                trade_id = position.get('trade_id')
                symbol = position.get('symbol')
                entry_price = position.get('entry_price')
                side = position.get('side')
                quantity = position.get('quantity')
                take_profit_pct = position.get('take_profit_pct')
                stop_loss_pct = position.get('stop_loss_pct')
                
                if not all([trade_id, symbol, entry_price, side]):
                    continue
                
                # Get current market price
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    current_price = ticker['last']
                except Exception as e:
                    logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
                    continue
                
                # Check if position should be closed
                should_close, reason = self.risk_manager.should_close_position(
                    entry_price, current_price, side, take_profit_pct, stop_loss_pct
                )
                
                if should_close:
                    logger.info(f"Closing position {trade_id} due to {reason}")
                    
                    # Execute closing trade
                    close_side = 'sell' if side == 'buy' else 'buy'
                    close_result = self._execute_market_order(symbol, close_side, quantity)
                    
                    if close_result and 'error' not in close_result:
                        # Calculate PnL
                        if side == 'buy':
                            pnl = (current_price - entry_price) * quantity
                        else:
                            pnl = (entry_price - current_price) * quantity
                        
                        # Update trade in database
                        Trade.close_trade(trade_id, current_price, pnl)
                        
                        # Send notification
                        notification_manager.send_notification(
                            user_id=user_id,
                            message=f"Position closed: {symbol} at {current_price} ({reason}) - PnL: ${pnl:.2f}",
                            notification_type='trade'
                        )
                        
                        logger.info(f"Position {trade_id} closed successfully - PnL: ${pnl:.2f}")
                    else:
                        logger.error(f"Failed to close position {trade_id}: {close_result.get('error', 'Unknown error')}")
                        
        except Exception as e:
            logger.error(f"Error monitoring positions for user {user_id}: {str(e)}")
    
    def _execute_market_order(self, symbol, side, quantity):
        """Execute a market order for closing positions"""
        try:
            order = self.exchange.create_market_order(symbol, side, quantity)
            
            logger.info(f"Market order executed: {side} {quantity} {symbol}")
            
            return {
                'order_id': order['id'],
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': order.get('average') or order.get('price'),
                'status': order['status']
            }
            
        except InsufficientFunds:
            error_msg = "Insufficient funds for market order"
            logger.error(error_msg)
            return {'error': error_msg}
        except InvalidOrder as e:
            error_msg = f"Invalid market order: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg}
        except NetworkError as e:
            error_msg = f"Network error during market order: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg}
        except ExchangeError as e:
            error_msg = f"Exchange error during market order: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during market order: {str(e)}"
            logger.error(error_msg)
            return {'error': error_msg}
    
    def _execute_trade(self, user_id, symbol, amount, side, take_profit, stop_loss):
        """Execute a trade
        
        Args:
            user_id (str): User ID
            symbol (str): Trading symbol
            amount (float): Amount to trade
            side (str): Trade side ('buy' or 'sell')
            take_profit (float): Take profit percentage
            stop_loss (float): Stop loss percentage
            
        Returns:
            dict: Trade result or None if failed
        """
        order_id = None
        tp_order_id = None
        sl_order_id = None
        
        try:
            # Get current market price
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            
            # Calculate quantity based on amount
            quantity = amount / price
            
            # Check minimum order size
            market = self.exchange.markets[symbol]
            min_amount = market.get('limits', {}).get('amount', {}).get('min', 0)
            if quantity < min_amount:
                raise ValueError(f"Order quantity {quantity} below minimum {min_amount}")
            
            # Check account balance
            balance = self.exchange.fetch_balance()
            if side == 'buy':
                base_currency = symbol.split('/')[1]  # e.g., USDT from BTC/USDT
                available_balance = balance['free'].get(base_currency, 0)
                if amount > available_balance:
                    raise InsufficientFunds(f"Insufficient {base_currency} balance: {available_balance} < {amount}")
            else:
                quote_currency = symbol.split('/')[0]  # e.g., BTC from BTC/USDT
                available_balance = balance['free'].get(quote_currency, 0)
                if quantity > available_balance:
                    raise InsufficientFunds(f"Insufficient {quote_currency} balance: {available_balance} < {quantity}")
            
            # Execute market order
            logger.info(f"Executing {side} order: {quantity} {symbol} at ~{price}")
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=quantity
            )
            order_id = order['id']
            
            # Wait for order to fill
            time.sleep(2)
            filled_order = self.exchange.fetch_order(order_id, symbol)
            actual_price = filled_order.get('average', price)
            actual_quantity = filled_order.get('filled', quantity)
            fee = filled_order.get('fee', {}).get('cost', amount * 0.001)
            
            # Log successful trade
            logger.log_trade(user_id, None, symbol, side, actual_quantity, actual_price, 'FILLED', order_id)
            
            # Set take profit and stop loss orders
            try:
                if side == 'buy':
                    tp_price = actual_price * (1 + take_profit / 100)
                    sl_price = actual_price * (1 - stop_loss / 100)
                    opposite_side = 'sell'
                else:
                    tp_price = actual_price * (1 - take_profit / 100)
                    sl_price = actual_price * (1 + stop_loss / 100)
                    opposite_side = 'buy'
                
                # Create take profit order
                tp_order = self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=opposite_side,
                    amount=actual_quantity,
                    price=tp_price
                )
                tp_order_id = tp_order['id']
                logger.info(f"Take profit order created: {tp_order_id} at {tp_price}")
                
                # Create stop loss order
                sl_order = self.exchange.create_order(
                    symbol=symbol,
                    type='stop_market',
                    side=opposite_side,
                    amount=actual_quantity,
                    params={'stopPrice': sl_price}
                )
                sl_order_id = sl_order['id']
                logger.info(f"Stop loss order created: {sl_order_id} at {sl_price}")
                
            except Exception as e:
                logger.warning(f"Failed to create TP/SL orders: {str(e)}")
            
            return {
                'order_id': order_id,
                'side': side,
                'quantity': actual_quantity,
                'price': actual_price,
                'fee': fee,
                'take_profit_order_id': tp_order_id,
                'stop_loss_order_id': sl_order_id
            }
            
        except InsufficientFunds as e:
            error_msg = f"Insufficient funds for {side} order: {str(e)}"
            logger.error(error_msg)
            logger.log_trade(user_id, None, symbol, side, amount, 0, 'FAILED', None, error_msg)
            return None
            
        except InvalidOrder as e:
            error_msg = f"Invalid order for {side} {symbol}: {str(e)}"
            logger.error(error_msg)
            logger.log_trade(user_id, None, symbol, side, amount, 0, 'FAILED', None, error_msg)
            return None
            
        except NetworkError as e:
            error_msg = f"Network error during {side} order: {str(e)}"
            logger.error(error_msg)
            logger.log_trade(user_id, None, symbol, side, amount, 0, 'FAILED', None, error_msg)
            return None
            
        except ExchangeError as e:
            error_msg = f"Exchange error during {side} order: {str(e)}"
            logger.error(error_msg)
            logger.log_trade(user_id, None, symbol, side, amount, 0, 'FAILED', None, error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error executing {side} trade: {str(e)}"
            logger.error(error_msg)
            logger.log_trade(user_id, None, symbol, side, amount, 0, 'FAILED', None, error_msg)
            return None
    
    def get_account_balance(self, user_id):
        """Get account balance for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Account balance
        """
        try:
            # Fetch balance from exchange
            balance = self.exchange.fetch_balance()
            
            # Extract relevant information
            result = {
                'total': {},
                'free': {},
                'used': {}
            }
            
            # Include only non-zero balances
            for currency, data in balance['total'].items():
                if data > 0:
                    result['total'][currency] = data
                    result['free'][currency] = balance['free'].get(currency, 0)
                    result['used'][currency] = balance['used'].get(currency, 0)
            
            return result
            
        except Exception as e:
            print(f"Error fetching account balance: {str(e)}")
            return {}
    
    def get_available_symbols(self):
        """Get available trading symbols
        
        Returns:
            list: List of available symbols
        """
        try:
            markets = self.exchange.fetch_markets()
            symbols = [market['symbol'] for market in markets if market['active']]
            return symbols
        except Exception as e:
            print(f"Error fetching available symbols: {str(e)}")
            return []
    
    def calculate_performance(self, user_id, period='30d'):
        """Calculate trading performance for a user
        
        Args:
            user_id (str): User ID
            period (str): Time period ('1d', '7d', '30d', 'all')
            
        Returns:
            dict: Performance metrics
        """
        # Calculate start date based on period
        end_date = datetime.utcnow()
        
        if period == '1d':
            start_date = end_date - timedelta(days=1)
        elif period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        else:  # 'all'
            start_date = None
        
        # Get trades within period
        if start_date:
            trades = Trade.get_trades_by_date_range(user_id, start_date, end_date)
        else:
            trades = Trade.find({'user_id': user_id})
        
        if not trades:
            return {
                'total_trades': 0,
                'profitable_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit_loss': 0,
                'average_profit_loss': 0,
                'largest_profit': 0,
                'largest_loss': 0
            }
        
        # Calculate metrics
        total_trades = len(trades)
        profitable_trades = sum(1 for trade in trades if trade.get('profit_loss', 0) > 0)
        losing_trades = sum(1 for trade in trades if trade.get('profit_loss', 0) < 0)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        profit_losses = [trade.get('profit_loss', 0) for trade in trades]
        total_profit_loss = sum(profit_losses)
        average_profit_loss = total_profit_loss / total_trades if total_trades > 0 else 0
        largest_profit = max(profit_losses) if profit_losses else 0
        largest_loss = min(profit_losses) if profit_losses else 0
        
        return {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit_loss': total_profit_loss,
            'average_profit_loss': average_profit_loss,
            'largest_profit': largest_profit,
            'largest_loss': largest_loss
        }
    
    def create_bot(self, user_id, bot_data):
        """Create a new bot
        
        Args:
            user_id (str): User ID
            bot_data (dict): Bot configuration data
            
        Returns:
            str: Bot ID
        """
        bot_data['user_id'] = user_id
        return Bot.create(bot_data)
    
    def get_user_bots(self, user_id, skip=0, limit=10):
        """Get all bots for a user
        
        Args:
            user_id (str): User ID
            skip (int): Number of documents to skip
            limit (int): Maximum number of documents to return
            
        Returns:
            list: List of bots
        """
        return Bot.find_by_user(user_id, skip, limit)
    
    def get_bot(self, bot_id, user_id=None):
        """Get bot by ID
        
        Args:
            bot_id (str): Bot ID
            user_id (str): User ID (for authorization)
            
        Returns:
            dict: Bot data or None
        """
        bot = Bot.find_by_id(bot_id)
        if bot and user_id and bot.get('user_id') != user_id:
            return None
        return bot
    
    def update_bot(self, bot_id, user_id, update_data):
        """Update bot
        
        Args:
            bot_id (str): Bot ID
            user_id (str): User ID (for authorization)
            update_data (dict): Data to update
            
        Returns:
            bool: True if updated successfully
        """
        bot = Bot.find_by_id(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return False
        
        # Don't allow updating certain fields
        restricted_fields = ['user_id', 'created_at', '_id']
        for field in restricted_fields:
            update_data.pop(field, None)
        
        return Bot.update(bot_id, update_data)
    
    def delete_bot(self, bot_id, user_id):
        """Delete bot
        
        Args:
            bot_id (str): Bot ID
            user_id (str): User ID (for authorization)
            
        Returns:
            bool: True if deleted successfully
        """
        bot = Bot.find_by_id(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return False
        
        # Stop bot if running
        if bot_id in self.active_bots:
            self.stop_bot(bot_id, user_id)
        
        return Bot.delete(bot_id)
    
    def start_bot_by_id(self, bot_id, user_id):
        """Start bot by ID
        
        Args:
            bot_id (str): Bot ID
            user_id (str): User ID (for authorization)
            
        Returns:
            bool: True if started successfully
        """
        bot = Bot.find_by_id(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return False
        
        # Check if bot is already running
        if bot_id in self.active_bots:
            return False
        
        # Start the bot using existing start_bot method
        success = self.start_bot(
            user_id=user_id,
            symbol=bot['symbol'],
            strategy=bot['strategy'],
            interval=bot['interval'],
            amount=bot['amount'],
            take_profit=bot.get('take_profit', 2.0),
            stop_loss=bot.get('stop_loss', 1.0),
            bot_id=bot_id
        )
        
        if success:
            Bot.set_running_status(bot_id, True)
            Bot.set_active_status(bot_id, True)
        
        return success
    
    def stop_bot_by_id(self, bot_id, user_id):
        """Stop bot by ID
        
        Args:
            bot_id (str): Bot ID
            user_id (str): User ID (for authorization)
            
        Returns:
            bool: True if stopped successfully
        """
        bot = Bot.find_by_id(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return False
        
        success = self.stop_bot(bot_id, user_id)
        if success:
            Bot.set_running_status(bot_id, False)
        
        return success
    
    def get_bot_trades(self, bot_id, user_id, skip=0, limit=10):
        """Get trades for a specific bot
        
        Args:
            bot_id (str): Bot ID
            user_id (str): User ID (for authorization)
            skip (int): Number of documents to skip
            limit (int): Maximum number of documents to return
            
        Returns:
            list: List of trades
        """
        bot = Bot.find_by_id(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return []
        
        return Trade.find({
            'bot_id': bot_id,
            'user_id': user_id
        }, skip=skip, limit=limit)
    
    async def start_websocket_stream(self, symbol):
        """Start WebSocket stream for real-time price data
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
        """
        try:
            if symbol in self.websocket_connections:
                return  # Already connected
            
            # Binance WebSocket URL for ticker stream
            ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@ticker"
            
            async def websocket_handler():
                try:
                    async with websockets.connect(ws_url) as websocket:
                        self.websocket_connections[symbol] = websocket
                        logger.info(f"WebSocket connected for {symbol}")
                        
                        async for message in websocket:
                            data = json.loads(message)
                            
                            # Update real-time data
                            self.real_time_data[symbol] = {
                                'symbol': data['s'],
                                'price': float(data['c']),
                                'change': float(data['P']),
                                'volume': float(data['v']),
                                'high': float(data['h']),
                                'low': float(data['l']),
                                'timestamp': datetime.utcnow()
                            }
                            
                            # Notify active bots about price update
                            await self._notify_bots_price_update(symbol, self.real_time_data[symbol])
                            
                except websockets.exceptions.ConnectionClosed:
                    logger.warning(f"WebSocket connection closed for {symbol}")
                except Exception as e:
                    logger.error(f"WebSocket error for {symbol}: {str(e)}")
                finally:
                    if symbol in self.websocket_connections:
                        del self.websocket_connections[symbol]
            
            # Run WebSocket handler in executor
            self.executor.submit(asyncio.run, websocket_handler())
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket stream for {symbol}: {str(e)}")
    
    async def _notify_bots_price_update(self, symbol, price_data):
        """Notify active bots about price updates
        
        Args:
            symbol (str): Trading symbol
            price_data (dict): Real-time price data
        """
        for bot_id, bot_info in self.active_bots.items():
            if (bot_info['config']['symbol'] == symbol and 
                bot_info['is_running']):
                # Update bot with latest price data
                bot_info['latest_price'] = price_data
    
    def get_real_time_data(self, symbol):
        """Get real-time data for a symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            dict: Real-time price data or None
        """
        return self.real_time_data.get(symbol)
    
    def get_all_real_time_data(self):
        """Get all real-time data
        
        Returns:
            dict: All real-time price data
        """
        return self.real_time_data.copy()
    
    def stop_websocket_stream(self, symbol):
        """Stop WebSocket stream for a symbol
        
        Args:
            symbol (str): Trading symbol
        """
        if symbol in self.websocket_connections:
            try:
                # Close WebSocket connection
                connection = self.websocket_connections[symbol]
                if not connection.closed:
                    asyncio.run(connection.close())
                del self.websocket_connections[symbol]
                
                # Remove real-time data
                if symbol in self.real_time_data:
                    del self.real_time_data[symbol]
                    
                logger.info(f"WebSocket stream stopped for {symbol}")
            except Exception as e:
                logger.error(f"Error stopping WebSocket stream for {symbol}: {str(e)}")
    
    def get_market_data(self, symbol, interval='1h', limit=100):
        """Get historical market data
        
        Args:
            symbol (str): Trading symbol
            interval (str): Candlestick interval
            limit (int): Number of candles to fetch
            
        Returns:
            pandas.DataFrame: OHLCV data
        """
        try:
            if not self.exchange:
                raise Exception("Exchange not initialized")
            
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, interval, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_account_balance(self):
        """Get account balance
        
        Returns:
            dict: Account balance information
        """
        try:
            if not self.exchange:
                raise Exception("Exchange not initialized")
            
            balance = self.exchange.fetch_balance()
            
            # Format balance data
            formatted_balance = {
                'total_value': 0.0,
                'available_balance': 0.0,
                'assets': []
            }
            
            for currency, amounts in balance.items():
                if currency not in ['info', 'free', 'used', 'total'] and amounts['total'] > 0:
                    asset_info = {
                        'currency': currency,
                        'free': amounts['free'],
                        'used': amounts['used'],
                        'total': amounts['total']
                    }
                    formatted_balance['assets'].append(asset_info)
                    
                    # Add to total value (simplified - would need price conversion in real implementation)
                    if currency == 'USDT':
                        formatted_balance['total_value'] += amounts['total']
                        formatted_balance['available_balance'] += amounts['free']
            
            return formatted_balance
            
        except Exception as e:
            logger.error(f"Error fetching account balance: {str(e)}")
            return {'total_value': 0.0, 'available_balance': 0.0, 'assets': []}
    
    def cleanup(self):
        """Cleanup resources"""
        # Stop all WebSocket streams
        for symbol in list(self.websocket_connections.keys()):
            self.stop_websocket_stream(symbol)
        
        # Stop all active bots
        for bot_id in list(self.active_bots.keys()):
            self.active_bots[bot_id]['is_running'] = False
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Trading engine cleanup completed")