import ccxt
import pandas as pd
import numpy as np
import time
import uuid
import asyncio
import websockets
import json
import logging
from datetime import datetime, timedelta
from threading import Thread
from flask import current_app
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from ccxt.base.errors import BaseError, NetworkError, ExchangeError, InvalidOrder, InsufficientFunds, AuthenticationError

# Import license validation
from auth.license_manager import LicenseManager

# Import trading strategies
from .strategies.rsi_strategy import RSIStrategy
from .strategies.macd_strategy import MACDStrategy
from .strategies.ema_crossover_strategy import EMACrossoverStrategy
from .strategies.advanced_grid_strategy import AdvancedGridStrategy
from .strategies.smart_dca_strategy import SmartDCAStrategy
from .strategies.advanced_scalping_strategy import AdvancedScalpingStrategy
from .strategies.strategy_factory import StrategyFactory

# Import advanced components
from .advanced_risk_manager import AdvancedRiskManager
from .portfolio_manager import PortfolioManager
from .market_data_manager import MarketDataManager
from .backtesting_engine import BacktestingEngine

# Import models
from models.trade import Trade
from models.user import User
from models.bot import Bot

# Import utilities
from utils.notification import NotificationManager

# Create notification manager instance
notification_manager = NotificationManager()
from utils.logging_config import setup_logging
from utils.security import SecurityManager

@dataclass
class TradingBotConfig:
    """Configuration for individual trading bot"""
    user_id: int
    bot_id: str
    strategy_name: str
    symbol: str
    timeframe: str
    parameters: Dict[str, Any]
    risk_settings: Dict[str, Any]
    is_active: bool = True
    max_positions: int = 5
    position_size: float = 0.02  # 2% of portfolio per position
    stop_loss: float = 0.05  # 5% stop loss
    take_profit: float = 0.10  # 10% take profit

class TradingEngine:
    """Production-ready Advanced Trading Engine with comprehensive features"""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None, 
                 testnet: bool = True,
                 initial_capital: float = 100000,
                 max_concurrent_bots: int = 50,
                 enable_advanced_features: bool = True):
        """
        Initialize the trading engine with advanced capabilities
        
        Args:
            api_key: Exchange API key
            api_secret: Exchange API secret
            testnet: Use testnet/sandbox mode
            initial_capital: Initial capital for portfolio management
            max_concurrent_bots: Maximum number of concurrent trading bots
            enable_advanced_features: Enable advanced features (portfolio optimization, etc.)
        """
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        self.testnet = testnet if testnet is not None else os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
        self.initial_capital = initial_capital
        self.max_concurrent_bots = max_concurrent_bots
        self.enable_advanced_features = enable_advanced_features
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate license
        if not self._validate_license():
            raise Exception("License validation failed. Please activate your license.")
        
        # Initialize exchange connections
        self.exchanges = {}
        self.primary_exchange = None
        self.exchange = None  # Keep for backward compatibility
        self._initialize_exchanges()
        
        # Initialize advanced components
        self.market_data_manager = MarketDataManager(
            exchanges_config=self._get_exchanges_config(),
            cache_enabled=True,
            use_redis=False  # Can be enabled for production
        )
        
        self.portfolio_manager = PortfolioManager(
            initial_capital=initial_capital,
            max_positions=20,
            max_position_size=0.1,  # 10% max per position
            max_leverage=2.0
        )
        
        self.risk_manager = AdvancedRiskManager(
            max_portfolio_risk=0.02,  # 2% max portfolio risk per trade
            max_correlation=0.7,
            max_sector_allocation=0.3
        )
        
        self.backtesting_engine = BacktestingEngine(
            initial_capital=initial_capital,
            commission_rate=0.001,
            slippage_rate=0.0005
        )
        
        # Strategy factory for creating strategies
        self.strategy_factory = StrategyFactory()
        
        # Bot management
        self.active_bots: Dict[str, TradingBotConfig] = {}
        self.bot_threads: Dict[str, Thread] = {}
        self.bot_performance: Dict[str, Dict] = {}
        self.websocket_connections = {}  # Dict of WebSocket connections: {symbol: connection}
        
        # Performance tracking
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        self.start_time = datetime.now()
        
        # Real-time data
        self.real_time_data = {}  # Dict of real-time price data: {symbol: latest_data}
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_bots)
        
        # Legacy strategy mapping for backward compatibility
        self.strategies = {
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'ema_crossover': EMACrossoverStrategy,
            'advanced_grid': AdvancedGridStrategy,
            'smart_dca': SmartDCAStrategy,
            'advanced_scalping': AdvancedScalpingStrategy
        }
        
        # Real-time data processing
        self.price_update_thread = None
        self.is_running = False
        
        # Emergency stop mechanism
        self.emergency_stop = False
        self.max_daily_loss = 0.10  # 10% max daily loss
        
        # Initialize exchange if API credentials are provided
        if self.api_key and self.api_secret:
            try:
                self.initialize_exchange()
                self.logger.info(f"Trading engine initialized - Testnet: {self.testnet}")
            except Exception as e:
                self.logger.error(f"Failed to initialize trading engine: {str(e)}")
                raise
        
        self.logger.info(f"Advanced Trading Engine initialized successfully with {len(self.exchanges)} exchanges")
    
    def _get_default_strategy_parameters(self, strategy_name: str) -> Dict[str, Any]:
        """Get default parameters for a strategy"""
        defaults = {
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
            'ema_crossover': {'fast_period': 12, 'slow_period': 26},
            'advanced_grid': {'grid_size': 10, 'grid_spacing': 0.01},
            'smart_dca': {'dca_levels': 5, 'dca_multiplier': 1.5},
            'advanced_scalping': {'scalp_target': 0.005, 'max_hold_time': 300}
        }
        return defaults.get(strategy_name, {})
    
    def _run_advanced_bot(self, bot_config: TradingBotConfig, strategy_instance):
        """Run an advanced trading bot with comprehensive features"""
        bot_id = bot_config.bot_id
        user_id = bot_config.user_id
        symbol = bot_config.symbol
        
        self.logger.info(f"Advanced bot {bot_id} started for {symbol} using {bot_config.strategy_name} strategy")
        
        try:
            while bot_config.is_active and self.active_bots.get(bot_id):
                try:
                    # Get market data
                    market_data = self.market_data_manager.get_ohlcv(
                        symbol=symbol,
                        timeframe=bot_config.timeframe,
                        limit=100
                    )
                    
                    if market_data.empty:
                        time.sleep(60)
                        continue
                    
                    # Generate trading signals
                    signals = strategy_instance.generate_signals(market_data)
                    
                    if signals.empty:
                        time.sleep(60)
                        continue
                    
                    # Get latest signal
                    latest_signal = signals.iloc[-1]
                    
                    # Process signal if it's not neutral
                    if latest_signal.get('signal', 0) != 0:
                        self._process_trading_signal(
                            bot_config, 
                            latest_signal, 
                            market_data.iloc[-1]
                        )
                    
                    # Monitor existing positions
                    self._monitor_bot_positions(bot_config)
                    
                    # Update performance metrics
                    self._update_bot_performance(bot_id)
                    
                    # Sleep before next iteration
                    time.sleep(60)
                    
                except Exception as e:
                    self.logger.error(f"Error in bot {bot_id} iteration: {str(e)}")
                    time.sleep(60)
                    
        except Exception as e:
            self.logger.error(f"Critical error in bot {bot_id}: {str(e)}")
        finally:
            self.logger.info(f"Advanced bot {bot_id} stopped")
    
    def _process_trading_signal(self, bot_config: TradingBotConfig, signal, market_data):
        """Process a trading signal from strategy"""
        try:
            # Risk assessment
            portfolio_value = self.portfolio_manager.get_total_value()
            trade_amount = portfolio_value * bot_config.position_size
            
            risk_assessment = self.risk_manager.assess_trade_risk(
                symbol=bot_config.symbol,
                side='BUY' if signal['signal'] > 0 else 'SELL',
                quantity=trade_amount,
                price=market_data['close'],
                portfolio_value=portfolio_value
            )
            
            if not risk_assessment['allowed']:
                self.logger.warning(f"Trade blocked for bot {bot_config.bot_id}: {risk_assessment['reason']}")
                return
            
            # Execute trade
            trade_result = self._execute_advanced_trade(
                bot_config=bot_config,
                signal=signal,
                current_price=market_data['close']
            )
            
            if trade_result and trade_result.get('success'):
                # Update performance
                self.bot_performance[bot_config.bot_id]['trades'] += 1
                
                # Send notification
                notification_manager.send_notification(
                    bot_config.user_id,
                    f"Trade executed by bot {bot_config.bot_id}: {trade_result['side']} {bot_config.symbol}"
                )
                
        except Exception as e:
            self.logger.error(f"Error processing signal for bot {bot_config.bot_id}: {str(e)}")
    
    def _execute_advanced_trade(self, bot_config: TradingBotConfig, signal, current_price) -> Dict[str, Any]:
        """Execute an advanced trade with comprehensive error handling"""
        try:
            side = 'BUY' if signal['signal'] > 0 else 'SELL'
            portfolio_value = self.portfolio_manager.get_total_value()
            trade_amount = portfolio_value * bot_config.position_size
            quantity = trade_amount / current_price
            
            # Execute the trade
            order_result = self.exchange.create_market_order(
                symbol=bot_config.symbol,
                side=side.lower(),
                amount=quantity
            )
            
            if order_result:
                # Record trade in portfolio manager
                self.portfolio_manager.add_position(
                    symbol=bot_config.symbol,
                    side=side,
                    quantity=quantity,
                    price=current_price,
                    timestamp=datetime.now()
                )
                
                return {
                    'success': True,
                    'order_id': order_result.get('orderId'),
                    'side': side,
                    'quantity': quantity,
                    'price': current_price
                }
            
            return {'success': False, 'error': 'Order execution failed'}
            
        except Exception as e:
            self.logger.error(f"Error executing trade for bot {bot_config.bot_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _monitor_bot_positions(self, bot_config: TradingBotConfig):
        """Monitor positions for a specific bot"""
        try:
            positions = self.portfolio_manager.get_positions_by_symbol(bot_config.symbol)
            
            for position in positions:
                # Check stop loss and take profit
                current_price = self.market_data_manager.get_current_price(bot_config.symbol)
                
                if self._should_close_position(position, current_price, bot_config):
                    self._close_position(position, current_price, bot_config)
                    
        except Exception as e:
            self.logger.error(f"Error monitoring positions for bot {bot_config.bot_id}: {str(e)}")
    
    def _should_close_position(self, position, current_price, bot_config: TradingBotConfig) -> bool:
        """Determine if a position should be closed"""
        entry_price = position['price']
        side = position['side']
        
        if side == 'BUY':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Check take profit
        if pnl_pct >= bot_config.take_profit:
            return True
            
        # Check stop loss
        if pnl_pct <= -bot_config.stop_loss:
            return True
            
        return False
    
    def _close_position(self, position, current_price, bot_config: TradingBotConfig):
        """Close a position"""
        try:
            opposite_side = 'SELL' if position['side'] == 'BUY' else 'BUY'
            
            order_result = self.exchange.create_market_order(
                symbol=bot_config.symbol,
                side=opposite_side.lower(),
                amount=position['quantity']
            )
            
            if order_result:
                # Calculate PnL
                if position['side'] == 'BUY':
                    pnl = (current_price - position['price']) * position['quantity']
                else:
                    pnl = (position['price'] - current_price) * position['quantity']
                
                # Update portfolio
                self.portfolio_manager.close_position(position['id'])
                
                # Update bot performance
                if pnl > 0:
                    self.bot_performance[bot_config.bot_id]['wins'] += 1
                else:
                    self.bot_performance[bot_config.bot_id]['losses'] += 1
                
                self.bot_performance[bot_config.bot_id]['total_pnl'] += pnl
                
                self.logger.info(f"Position closed for bot {bot_config.bot_id}: PnL = {pnl}")
                
        except Exception as e:
            self.logger.error(f"Error closing position for bot {bot_config.bot_id}: {str(e)}")
    
    def _update_bot_performance(self, bot_id: str):
        """Update performance metrics for a bot"""
        try:
            if bot_id in self.bot_performance:
                performance = self.bot_performance[bot_id]
                
                # Calculate win rate
                total_trades = performance['wins'] + performance['losses']
                performance['win_rate'] = performance['wins'] / total_trades if total_trades > 0 else 0
                
                # Update last update time
                performance['last_update'] = datetime.now()
                
        except Exception as e:
            self.logger.error(f"Error updating performance for bot {bot_id}: {str(e)}")
    
    def _validate_license(self) -> bool:
        """Validate software license"""
        try:
            is_valid, message = verify_license()
            if not is_valid:
                self.logger.error(f"License validation failed: {message}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"License validation error: {e}")
            return False
    
    def _get_exchanges_config(self) -> Dict[str, Dict]:
        """Get configuration for all supported exchanges"""
        config = {}
        
        # Binance configuration
        if self.api_key and self.api_secret:
            config['binance'] = {
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                'testnet': self.testnet,
                'rate_limit': 1200  # requests per minute
            }
        
        # Add other exchanges as needed
        # config['coinbase'] = {...}
        # config['kraken'] = {...}
        
        return config
    
    def _initialize_exchanges(self):
        """Initialize connections to all configured exchanges"""
        try:
            # Initialize Binance (primary exchange)
            if self.api_key and self.api_secret:
                self.exchanges['binance'] = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'sandbox': self.testnet,
                    'enableRateLimit': True,
                })
                self.primary_exchange = 'binance'
                self.exchange = self.exchanges['binance']  # Backward compatibility
                
                # Test connection
                account_info = self.exchange.fetch_balance()
                self.logger.info(f"Binance connection established - Testnet: {self.testnet}")
            
            # Add other exchanges here
            # self.exchanges['coinbase'] = ...
            # self.exchanges['kraken'] = ...
            
        except Exception as e:
            self.logger.error(f"Failed to initialize exchanges: {e}")
            raise
    
    def initialize_exchange(self):
        """Initialize the Binance exchange connection"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API key and secret are required")
            
            self._initialize_exchanges()
            
        except ccxt.AuthenticationError as e:
            self.logger.error(f"Authentication error: {str(e)}")
            raise ValueError("Invalid API credentials")
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error: {str(e)}")
            raise ConnectionError("Failed to connect to exchange")
        except Exception as e:
            self.logger.error(f"Error initializing exchange: {str(e)}")
            self.exchange = None
            raise
    
    def get_active_bots(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active bots for a user with comprehensive information
        
        Args:
            user_id (int): User ID
            
        Returns:
            List[Dict[str, Any]]: List of active bot configurations with performance data
        """
        try:
            user_bots = []
            for bot_id, bot_config in self.active_bots.items():
                if bot_config.user_id == user_id:
                    # Get bot performance metrics
                    performance = self.bot_performance.get(bot_id, {})
                    
                    # Get current positions
                    positions = self.portfolio_manager.get_positions_by_symbol(bot_config.symbol)
                    
                    # Get thread status
                    thread = self.bot_threads.get(bot_id)
                    is_alive = thread.is_alive() if thread else False
                    
                    bot_data = {
                        'bot_id': bot_id,
                        'strategy': bot_config.strategy_name,
                        'symbol': bot_config.symbol,
                        'timeframe': bot_config.timeframe,
                        'status': 'active' if is_alive else 'stopped',
                        'is_active': bot_config.is_active,
                        'position_size': bot_config.position_size,
                        'stop_loss': bot_config.stop_loss,
                        'take_profit': bot_config.take_profit,
                        'max_positions': bot_config.max_positions,
                        'current_positions': len(positions),
                        'performance': performance,
                        'risk_settings': bot_config.risk_settings,
                        'parameters': bot_config.parameters
                    }
                    user_bots.append(bot_data)
            
            return user_bots
            
        except Exception as e:
            self.logger.error(f"Error getting active bots for user {user_id}: {str(e)}")
            return []
    
    def start_bot(self, 
                  user_id: int, 
                  symbol: str, 
                  strategy_name: str, 
                  timeframe: str = '1h',
                  parameters: Optional[Dict[str, Any]] = None,
                  risk_settings: Optional[Dict[str, Any]] = None,
                  position_size: float = 0.02,
                  stop_loss: float = 0.05,
                  take_profit: float = 0.10,
                  max_positions: int = 5) -> Dict[str, Any]:
        """Start a new advanced trading bot for a user
        
        Args:
            user_id: User ID
            symbol: Trading symbol (e.g., 'BTCUSDT')
            strategy_name: Strategy name
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            parameters: Strategy-specific parameters
            risk_settings: Risk management settings
            position_size: Position size as percentage of portfolio
            stop_loss: Stop loss percentage
            take_profit: Take profit percentage
            max_positions: Maximum concurrent positions
            
        Returns:
            Dict containing bot creation result
        """
        try:
            # Validate license and features
            is_valid, message = verify_license()
            if not is_valid:
                self.logger.error(f"License validation failed: {message}")
                return {'success': False, 'error': f'License validation failed: {message}'}
            
            if not check_feature('basic_trading'):
                self.logger.error("Basic trading feature not available in license")
                return {'success': False, 'error': 'Basic trading feature not available in license'}
            
            # Check for advanced strategies
            advanced_strategies = ['advanced_grid', 'smart_dca', 'advanced_scalping']
            if strategy_name in advanced_strategies and not check_feature('advanced_trading'):
                self.logger.error(f"Advanced strategy '{strategy_name}' not available in license")
                return {'success': False, 'error': f'Advanced strategy {strategy_name} requires premium license'}
            
            # Check maximum concurrent bots
            user_bots = [bot for bot in self.active_bots.values() if bot.user_id == user_id]
            if len(user_bots) >= self.max_concurrent_bots:
                return {'success': False, 'error': f'Maximum concurrent bots limit reached ({self.max_concurrent_bots})'}
            
            # Validate exchange connection
            if not self.exchange:
                self.logger.error("Exchange not initialized")
                return {'success': False, 'error': 'Exchange not initialized'}
            
            # Validate strategy
            if strategy_name not in self.strategies:
                available_strategies = list(self.strategies.keys())
                return {'success': False, 'error': f'Unknown strategy: {strategy_name}. Available: {available_strategies}'}
            
            # Validate symbol
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    return {'success': False, 'error': f'Invalid or inactive symbol: {symbol}'}
            except Exception as e:
                return {'success': False, 'error': f'Symbol validation failed: {str(e)}'}
            
            # Set default parameters if not provided
            if parameters is None:
                parameters = self._get_default_strategy_parameters(strategy_name)
            
            if risk_settings is None:
                risk_settings = {
                    'max_position_size': position_size,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'max_daily_trades': 10,
                    'max_drawdown': 0.20
                }
            
            # Generate unique bot ID
            bot_id = f"{user_id}_{symbol}_{strategy_name}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Create bot configuration
            bot_config = TradingBotConfig(
                user_id=user_id,
                bot_id=bot_id,
                strategy_name=strategy_name,
                symbol=symbol,
                timeframe=timeframe,
                parameters=parameters,
                risk_settings=risk_settings,
                is_active=True,
                max_positions=max_positions,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Create strategy instance using factory
            try:
                strategy_instance = self.strategy_factory.create_strategy(
                    strategy_name, 
                    parameters
                )
            except Exception as e:
                return {'success': False, 'error': f'Failed to create strategy: {str(e)}'}
            
            # Perform risk assessment
            portfolio_value = self.portfolio_manager.get_total_value()
            trade_amount = portfolio_value * position_size
            
            risk_assessment = self.risk_manager.assess_trade_risk(
                symbol=symbol,
                side='BUY',  # Initial assessment
                quantity=trade_amount,
                price=float(ticker['price']),
                portfolio_value=portfolio_value
            )
            
            if not risk_assessment['allowed']:
                return {'success': False, 'error': f'Trade not allowed: {risk_assessment["reason"]}'}
            
            # Start bot thread
            bot_thread = Thread(
                target=self._run_advanced_bot,
                args=(bot_config, strategy_instance),
                daemon=True,
                name=f"Bot-{bot_id}"
            )
            bot_thread.start()
            
            # Store bot information
            self.active_bots[bot_id] = bot_config
            self.bot_threads[bot_id] = bot_thread
            self.bot_performance[bot_id] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'max_drawdown': 0.0,
                'start_time': datetime.now(),
                'last_trade_time': None
            }
            
            self.logger.info(f"Advanced bot {bot_id} started successfully for user {user_id} with strategy {strategy_name}")
            
            # Notify user
            notification_manager.send_notification(
                user_id,
                f"Advanced trading bot started for {symbol} using {strategy_name} strategy"
            )
            
            return {
                'success': True,
                'bot_id': bot_id,
                'strategy': strategy_name,
                'symbol': symbol,
                'timeframe': timeframe,
                'risk_score': risk_assessment.get('risk_score', 0),
                'message': f'Advanced bot started successfully with {strategy_name} strategy'
            }
            
        except Exception as e:
            self.logger.error(f"Error starting bot: {str(e)}")
            return {'success': False, 'error': f'Failed to start bot: {str(e)}'}
    
    def stop_bot(self, user_id: int, bot_id: str) -> Dict[str, Any]:
        """Stop a trading bot
        
        Args:
            user_id: User ID
            bot_id: Bot ID
            
        Returns:
            Dict containing stop result
        """
        try:
            if bot_id not in self.active_bots:
                return {'success': False, 'error': 'Bot not found'}
            
            # Check if bot belongs to user
            bot_config = self.active_bots[bot_id]
            if bot_config.user_id != user_id:
                return {'success': False, 'error': 'Unauthorized access to bot'}
            
            # Set bot to stop
            bot_config.is_active = False
            
            # Wait for thread to finish (with timeout)
            if bot_id in self.bot_threads:
                thread = self.bot_threads[bot_id]
                thread.join(timeout=10)
                if thread.is_alive():
                    self.logger.warning(f"Bot thread {bot_id} did not stop gracefully")
                del self.bot_threads[bot_id]
            
            # Clean up bot data
            del self.active_bots[bot_id]
            
            # Notify user
            notification_manager.send_notification(
                user_id,
                f"Trading bot stopped for {bot_config.symbol}"
            )
            
            self.logger.info(f"Bot {bot_id} stopped successfully for user {user_id}")
            
            return {
                'success': True,
                'message': f'Bot {bot_id} stopped successfully',
                'symbol': bot_config.symbol,
                'strategy': bot_config.strategy_name
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping bot {bot_id}: {str(e)}")
            return {'success': False, 'error': f'Failed to stop bot: {str(e)}'}
    
    def stop_all_bots(self, user_id: int) -> Dict[str, Any]:
        """Stop all trading bots for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict containing stop results
        """
        try:
            stopped_bots = []
            failed_bots = []
            
            for bot_id, bot_config in list(self.active_bots.items()):
                if bot_config.user_id == user_id:
                    result = self.stop_bot(user_id, bot_id)
                    if result['success']:
                        stopped_bots.append(bot_id)
                    else:
                        failed_bots.append({'bot_id': bot_id, 'error': result['error']})
            
            return {
                'success': True,
                'stopped_bots': stopped_bots,
                'failed_bots': failed_bots,
                'total_stopped': len(stopped_bots),
                'message': f'Stopped {len(stopped_bots)} bots successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping all bots for user {user_id}: {str(e)}")
            return {'success': False, 'error': f'Failed to stop bots: {str(e)}'}
    
    def _run_bot(self, bot_config):
        """Legacy bot runner for backward compatibility"""
        # Convert old config to new format
        new_config = TradingBotConfig(
            user_id=bot_config['user_id'],
            bot_id=bot_config['id'],
            strategy_name=bot_config['strategy'],
            symbol=bot_config['symbol'],
            timeframe=bot_config['interval'],
            parameters={},
            risk_settings={
                'stop_loss': bot_config['stop_loss'],
                'take_profit': bot_config['take_profit']
            },
            position_size=bot_config['amount'] / 10000  # Convert to percentage
        )
        
        # Create strategy instance
        strategy_class = self.strategies[bot_config['strategy']]
        strategy_instance = strategy_class()
        
        # Run with new advanced bot runner
        self._run_advanced_bot(new_config, strategy_instance)
    
    def get_bot_performance(self, bot_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific bot"""
        try:
            if bot_id not in self.bot_performance:
                return {
                    'trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'max_drawdown': 0.0,
                    'start_time': None,
                    'last_trade_time': None,
                    'status': 'inactive'
                }
            
            performance = self.bot_performance[bot_id].copy()
            
            # Calculate additional metrics
            total_trades = performance['wins'] + performance['losses']
            performance['win_rate'] = performance['wins'] / total_trades if total_trades > 0 else 0.0
            performance['total_trades'] = total_trades
            
            # Calculate runtime
            if performance.get('start_time'):
                runtime = datetime.now() - performance['start_time']
                performance['runtime_hours'] = runtime.total_seconds() / 3600
            
            # Calculate average PnL per trade
            if total_trades > 0:
                performance['avg_pnl_per_trade'] = performance['total_pnl'] / total_trades
            else:
                performance['avg_pnl_per_trade'] = 0.0
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error getting bot performance for {bot_id}: {str(e)}")
            return {}
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        try:
            portfolio_metrics = self.portfolio_manager.get_portfolio_metrics()
            risk_metrics = self.risk_manager.get_portfolio_risk_metrics()
            
            # Get active positions
            positions = self.portfolio_manager.get_all_positions()
            
            # Calculate total bot performance
            total_bot_trades = sum(perf.get('trades', 0) for perf in self.bot_performance.values())
            total_bot_pnl = sum(perf.get('total_pnl', 0) for perf in self.bot_performance.values())
            
            return {
                'portfolio_value': portfolio_metrics.get('total_value', 0),
                'total_pnl': portfolio_metrics.get('total_pnl', 0),
                'total_return': portfolio_metrics.get('total_return', 0),
                'active_positions': len(positions),
                'active_bots': len(self.active_bots),
                'total_trades': total_bot_trades,
                'total_bot_pnl': total_bot_pnl,
                'risk_score': risk_metrics.get('portfolio_risk_score', 0),
                'max_drawdown': portfolio_metrics.get('max_drawdown', 0),
                'sharpe_ratio': portfolio_metrics.get('sharpe_ratio', 0),
                'volatility': portfolio_metrics.get('volatility', 0),
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {str(e)}")
            return {}
    
    def run_backtest(self, 
                     strategy_name: str, 
                     symbol: str, 
                     timeframe: str,
                     start_date: str,
                     end_date: str,
                     parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run backtest for a strategy"""
        try:
            # Create strategy instance
            strategy_instance = self.strategy_factory.create_strategy(strategy_name, parameters)
            
            # Get historical data
            historical_data = self.market_data_manager.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if historical_data.empty:
                return {'success': False, 'error': 'No historical data available'}
            
            # Run backtest
            backtest_results = self.backtesting_engine.run_backtest(
                strategy=strategy_instance,
                data=historical_data,
                symbol=symbol
            )
            
            return {
                'success': True,
                'results': backtest_results,
                'strategy': strategy_name,
                'symbol': symbol,
                'timeframe': timeframe,
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            self.logger.error(f"Error running backtest: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def optimize_strategy(self, 
                         strategy_name: str,
                         symbol: str,
                         timeframe: str,
                         start_date: str,
                         end_date: str,
                         parameter_ranges: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize strategy parameters"""
        try:
            # Get historical data
            historical_data = self.market_data_manager.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if historical_data.empty:
                return {'success': False, 'error': 'No historical data available'}
            
            # Create strategy instance
            strategy_instance = self.strategy_factory.create_strategy(strategy_name)
            
            # Run optimization
            optimization_results = self.backtesting_engine.optimize_parameters(
                strategy=strategy_instance,
                data=historical_data,
                symbol=symbol,
                parameter_ranges=parameter_ranges
            )
            
            return {
                'success': True,
                'results': optimization_results,
                'strategy': strategy_name,
                'symbol': symbol,
                'timeframe': timeframe
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing strategy: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview and statistics"""
        try:
            # Get market data for major symbols
            major_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
            market_data = {}
            
            for symbol in major_symbols:
                try:
                    ticker = self.market_data_manager.get_current_price(symbol)
                    if ticker:
                        market_data[symbol] = {
                            'price': ticker,
                            'change_24h': 0,  # Would need 24h data
                            'volume_24h': 0   # Would need volume data
                        }
                except Exception:
                    continue
            
            # Get exchange status
            exchange_status = 'connected' if self.exchange else 'disconnected'
            
            return {
                'market_data': market_data,
                'exchange_status': exchange_status,
                'active_bots': len(self.active_bots),
                'total_symbols_tracked': len(market_data),
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market overview: {str(e)}")
            return {}
    
    def emergency_stop_all(self, reason: str = "Emergency stop triggered") -> Dict[str, Any]:
        """Emergency stop all trading activities"""
        try:
            self.emergency_stop = True
            stopped_bots = []
            
            # Stop all bots
            for bot_id, bot_config in list(self.active_bots.items()):
                bot_config.is_active = False
                stopped_bots.append(bot_id)
            
            # Close all open positions (if enabled)
            if hasattr(self, 'close_all_positions_on_emergency') and self.close_all_positions_on_emergency:
                positions = self.portfolio_manager.get_all_positions()
                for position in positions:
                    try:
                        self.portfolio_manager.close_position(position['id'])
                    except Exception as e:
                        self.logger.error(f"Error closing position {position['id']}: {str(e)}")
            
            self.logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
            
            return {
                'success': True,
                'stopped_bots': stopped_bots,
                'reason': reason,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            # Check exchange connection
            exchange_healthy = False
            try:
                if self.exchange:
                    self.exchange.fetch_ticker('BTCUSDT')
                    exchange_healthy = True
            except Exception:
                pass
            
            # Check active threads
            active_threads = sum(1 for thread in self.bot_threads.values() if thread.is_alive())
            
            # Check memory usage (basic)
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            # Check database connection
            db_healthy = True
            try:
                # Test portfolio manager database
                self.portfolio_manager.get_total_value()
            except Exception:
                db_healthy = False
            
            health_status = {
                'overall_status': 'healthy' if exchange_healthy and db_healthy else 'degraded',
                'exchange_connection': 'healthy' if exchange_healthy else 'unhealthy',
                'database_connection': 'healthy' if db_healthy else 'unhealthy',
                'active_bots': len(self.active_bots),
                'active_threads': active_threads,
                'memory_usage_mb': memory_usage,
                'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
                'emergency_stop': self.emergency_stop,
                'last_check': datetime.now()
            }
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error checking system health: {str(e)}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'last_check': datetime.now()
            }
    
    def cleanup(self):
        """Cleanup resources when shutting down"""
        try:
            self.logger.info("Starting trading engine cleanup...")
            
            # Stop all bots gracefully
            for bot_id in list(self.active_bots.keys()):
                bot_config = self.active_bots[bot_id]
                bot_config.is_active = False
            
            # Wait for threads to finish
            for thread in self.bot_threads.values():
                thread.join(timeout=5)
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            # Close market data connections
            if hasattr(self.market_data_manager, 'cleanup'):
                self.market_data_manager.cleanup()
            
            self.logger.info("Trading engine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
    
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