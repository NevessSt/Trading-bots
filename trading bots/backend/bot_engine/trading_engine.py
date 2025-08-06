import ccxt
import pandas as pd
import numpy as np
import time
import uuid
from datetime import datetime, timedelta
from threading import Thread
from flask import current_app

# Import strategies
from bot_engine.strategies.rsi_strategy import RSIStrategy
from bot_engine.strategies.macd_strategy import MACDStrategy
from bot_engine.strategies.ema_crossover_strategy import EMACrossoverStrategy

# Import risk manager
from bot_engine.risk_manager import RiskManager

# Import models
from models.trade import Trade
from models.user import User

# Import utils
from utils.notification import NotificationManager

class TradingEngine:
    """Main trading engine that manages all trading operations"""
    
    def __init__(self, api_key=None, api_secret=None):
        """Initialize the trading engine
        
        Args:
            api_key (str, optional): Binance API key
            api_secret (str, optional): Binance API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None
        self.active_bots = {}  # Dict of active bots: {bot_id: bot_thread}
        self.strategies = {
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'ema_crossover': EMACrossoverStrategy
        }
        self.notification_manager = NotificationManager()
        
        # Initialize exchange if API credentials are provided
        if api_key and api_secret:
            self.initialize_exchange()
    
    def initialize_exchange(self):
        """Initialize the exchange connection"""
        try:
            self.exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True
            })
            self.exchange.load_markets()
            print("Exchange initialized successfully")
        except Exception as e:
            print(f"Error initializing exchange: {str(e)}")
            self.exchange = None
    
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
        # Validate parameters
        if not self.exchange:
            raise Exception("Exchange not initialized")
        
        if strategy not in self.strategies:
            raise Exception(f"Strategy '{strategy}' not found")
        
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
        
        # Notify user
        self.notification_manager.send_notification(
            user_id,
            f"Trading bot started for {symbol} using {strategy} strategy"
        )
        
        return bot_id
    
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
                    # Check risk management rules
                    if risk_manager.can_trade(user_id, symbol, bot_config['amount'], last_signal > 0):
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
                
                # Sleep before next iteration
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in bot {bot_id}: {str(e)}")
                time.sleep(60)  # Wait before retrying
        
        print(f"Bot {bot_id} stopped")
    
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
        try:
            # Get current market price
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            
            # Calculate quantity based on amount
            quantity = amount / price
            
            # Execute market order
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=quantity
            )
            
            # Calculate fee
            fee = amount * 0.001  # Assuming 0.1% fee
            
            # Set take profit and stop loss orders
            tp_price = price * (1 + take_profit / 100) if side == 'buy' else price * (1 - take_profit / 100)
            sl_price = price * (1 - stop_loss / 100) if side == 'buy' else price * (1 + stop_loss / 100)
            
            # Create take profit order
            tp_order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side='sell' if side == 'buy' else 'buy',
                amount=quantity,
                price=tp_price
            )
            
            # Create stop loss order
            sl_order = self.exchange.create_order(
                symbol=symbol,
                type='stop_loss',
                side='sell' if side == 'buy' else 'buy',
                amount=quantity,
                price=sl_price,
                params={'stopPrice': sl_price}
            )
            
            return {
                'order_id': order['id'],
                'side': side,
                'quantity': quantity,
                'price': price,
                'fee': fee,
                'take_profit_order_id': tp_order['id'],
                'stop_loss_order_id': sl_order['id']
            }
            
        except Exception as e:
            print(f"Error executing trade: {str(e)}")
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