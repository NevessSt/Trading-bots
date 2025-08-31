import os
import logging
from typing import Optional, Dict, Any

# Legacy imports for backward compatibility
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .ema_crossover_strategy import EMACrossoverStrategy
from .scalping_strategy import ScalpingStrategy
from .swing_trading_strategy import SwingTradingStrategy
from .arbitrage_strategy import ArbitrageStrategy

# Import the dynamic strategy manager
try:
    from ..dynamic_strategy_manager import DynamicStrategyManager
except ImportError:
    DynamicStrategyManager = None

class StrategyFactory:
    """Enhanced factory class for creating trading strategies with dynamic loading support"""
    
    def __init__(self, enable_dynamic_loading=True):
        """
        Initialize the strategy factory
        
        Args:
            enable_dynamic_loading: Whether to enable dynamic strategy loading
        """
        self.logger = logging.getLogger(__name__)
        self.enable_dynamic_loading = enable_dynamic_loading and DynamicStrategyManager is not None
        
        # Initialize dynamic strategy manager if available
        self.dynamic_manager = None
        if self.enable_dynamic_loading:
            try:
                self.dynamic_manager = DynamicStrategyManager()
                self.logger.info("Dynamic strategy loading enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize dynamic strategy manager: {e}")
                self.enable_dynamic_loading = False
    
    def get_strategy(self, strategy_name, parameters=None):
        """Get a strategy instance by name with dynamic loading support
        
        Args:
            strategy_name (str): Name of the strategy
            parameters (dict, optional): Strategy parameters
            
        Returns:
            BaseStrategy: Strategy instance
        
        Raises:
            ValueError: If strategy name is not recognized
        """
        parameters = parameters or {}
        
        # Try dynamic loading first if enabled
        if self.enable_dynamic_loading and self.dynamic_manager:
            try:
                strategy = self.dynamic_manager.get_strategy(strategy_name, parameters)
                if strategy:
                    self.logger.info(f"Loaded strategy '{strategy_name}' dynamically")
                    return strategy
            except Exception as e:
                self.logger.warning(f"Dynamic loading failed for '{strategy_name}': {e}")
        
        # Fallback to legacy hardcoded strategies
        return self._get_legacy_strategy(strategy_name, parameters)
    
    def _get_legacy_strategy(self, strategy_name, parameters):
        """Get strategy using legacy hardcoded approach
        
        Args:
            strategy_name (str): Name of the strategy
            parameters (dict): Strategy parameters
            
        Returns:
            BaseStrategy: Strategy instance
        
        Raises:
            ValueError: If strategy name is not recognized
        """
        if strategy_name.lower() == 'rsi':
            strategy = RSIStrategy(
                rsi_period=parameters.get('rsi_period', 14),
                overbought=parameters.get('overbought', 70),
                oversold=parameters.get('oversold', 30)
            )
        elif strategy_name.lower() == 'macd':
            strategy = MACDStrategy(
                fast_period=parameters.get('fast_period', 12),
                slow_period=parameters.get('slow_period', 26),
                signal_period=parameters.get('signal_period', 9)
            )
        elif strategy_name.lower() == 'ema_crossover':
            strategy = EMACrossoverStrategy(
                fast_period=parameters.get('fast_period', 9),
                slow_period=parameters.get('slow_period', 21)
            )
        elif strategy_name.lower() == 'scalping':
            strategy = ScalpingStrategy(
                timeframes=parameters.get('timeframes', ['1m', '5m']),
                min_spread=parameters.get('min_spread', 0.0001),
                max_spread=parameters.get('max_spread', 0.001),
                volume_threshold=parameters.get('volume_threshold', 1000000),
                volatility_threshold=parameters.get('volatility_threshold', 0.005),
                quick_profit_target=parameters.get('quick_profit_target', 0.002),
                stop_loss=parameters.get('stop_loss', 0.003)
            )
        elif strategy_name.lower() == 'swing_trading':
            strategy = SwingTradingStrategy(
                primary_timeframe=parameters.get('primary_timeframe', '4h'),
                secondary_timeframe=parameters.get('secondary_timeframe', '1d'),
                trend_ema_fast=parameters.get('trend_ema_fast', 21),
                trend_ema_slow=parameters.get('trend_ema_slow', 50),
                profit_target=parameters.get('profit_target', 0.08),
                stop_loss=parameters.get('stop_loss', 0.04)
            )
        elif strategy_name.lower() == 'arbitrage':
            strategy = ArbitrageStrategy(
                min_profit_threshold=parameters.get('min_profit_threshold', 0.005),
                max_position_size=parameters.get('max_position_size', 1000),
                slippage_tolerance=parameters.get('slippage_tolerance', 0.002),
                transaction_cost=parameters.get('transaction_cost', 0.001),
                max_execution_time=parameters.get('max_execution_time', 30),
                enable_cross_exchange=parameters.get('enable_cross_exchange', True),
                enable_triangular=parameters.get('enable_triangular', True),
                enable_spot_futures=parameters.get('enable_spot_futures', False),
                max_daily_trades=parameters.get('max_daily_trades', 50),
                max_concurrent_trades=parameters.get('max_concurrent_trades', 3)
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy
    
    def create_strategy(self, strategy_name, parameters=None):
        """Alias for get_strategy for backward compatibility"""
        return self.get_strategy(strategy_name, parameters)
    
    def get_available_strategies(self):
        """Get a list of available strategies with dynamic loading support
        
        Returns:
            list: List of strategy information dictionaries
        """
        strategies = []
        
        # Get dynamically loaded strategies first
        if self.enable_dynamic_loading and self.dynamic_manager:
            try:
                dynamic_strategies = self.dynamic_manager.get_available_strategies()
                strategies.extend(dynamic_strategies)
                self.logger.info(f"Found {len(dynamic_strategies)} dynamic strategies")
            except Exception as e:
                self.logger.warning(f"Failed to get dynamic strategies: {e}")
        
        # Add legacy strategies (avoid duplicates)
        legacy_strategies = self._get_legacy_strategies()
        existing_ids = {s['id'] for s in strategies}
        
        for legacy_strategy in legacy_strategies:
            if legacy_strategy['id'] not in existing_ids:
                strategies.append(legacy_strategy)
        
        return strategies
    
    def _get_legacy_strategies(self):
        """Get legacy hardcoded strategies
        
        Returns:
            list: List of legacy strategy information dictionaries
        """
        return [
            {
                'id': 'rsi',
                'name': 'RSI Strategy',
                'description': 'Relative Strength Index strategy',
                'version': '1.0.0',
                'author': 'System',
                'parameters': {
                    'rsi_period': {
                        'type': 'integer',
                        'default': 14,
                        'min': 2,
                        'max': 50,
                        'description': 'RSI period'
                    },
                    'overbought': {
                        'type': 'integer',
                        'default': 70,
                        'min': 50,
                        'max': 90,
                        'description': 'Overbought threshold'
                    },
                    'oversold': {
                        'type': 'integer',
                        'default': 30,
                        'min': 10,
                        'max': 50,
                        'description': 'Oversold threshold'
                    }
                },
                'tags': ['technical_analysis', 'momentum'],
                'risk_level': 'medium',
                'min_capital': 100.0,
                'supported_timeframes': ['1m', '5m', '15m', '1h', '4h', '1d']
            },
            {
                'id': 'macd',
                'name': 'MACD Strategy',
                'description': 'Moving Average Convergence Divergence strategy',
                'version': '1.0.0',
                'author': 'System',
                'parameters': {
                    'fast_period': {
                        'type': 'integer',
                        'default': 12,
                        'min': 2,
                        'max': 50,
                        'description': 'Fast EMA period'
                    },
                    'slow_period': {
                        'type': 'integer',
                        'default': 26,
                        'min': 5,
                        'max': 100,
                        'description': 'Slow EMA period'
                    },
                    'signal_period': {
                        'type': 'integer',
                        'default': 9,
                        'min': 2,
                        'max': 50,
                        'description': 'Signal line period'
                    }
                },
                'tags': ['technical_analysis', 'trend_following'],
                'risk_level': 'medium',
                'min_capital': 100.0,
                'supported_timeframes': ['1m', '5m', '15m', '1h', '4h', '1d']
            },
            {
                'id': 'ema_crossover',
                'name': 'EMA Crossover Strategy',
                'description': 'Exponential Moving Average Crossover strategy',
                'version': '1.0.0',
                'author': 'System',
                'parameters': {
                    'fast_period': {
                        'type': 'integer',
                        'default': 9,
                        'min': 2,
                        'max': 50,
                        'description': 'Fast EMA period'
                    },
                    'slow_period': {
                        'type': 'integer',
                        'default': 21,
                        'min': 5,
                        'max': 100,
                        'description': 'Slow EMA period'
                    }
                },
                'tags': ['technical_analysis', 'trend_following'],
                'risk_level': 'low',
                'min_capital': 50.0,
                'supported_timeframes': ['5m', '15m', '1h', '4h', '1d']
            },
            {
                'id': 'scalping',
                'name': 'Advanced Scalping Strategy',
                'description': 'High-frequency scalping strategy with multi-timeframe analysis and order book data',
                'version': '1.0.0',
                'author': 'System',
                'parameters': {
                    'timeframes': {
                        'type': 'array',
                        'default': ['1m', '5m'],
                        'description': 'List of timeframes to analyze'
                    },
                    'min_spread': {
                        'type': 'float',
                        'default': 0.0001,
                        'min': 0.00001,
                        'max': 0.01,
                        'description': 'Minimum spread requirement'
                    },
                    'max_spread': {
                        'type': 'float',
                        'default': 0.001,
                        'min': 0.0001,
                        'max': 0.01,
                        'description': 'Maximum spread allowed'
                    },
                    'volume_threshold': {
                        'type': 'float',
                        'default': 1000000,
                        'min': 100000,
                        'max': 10000000,
                        'description': 'Minimum volume requirement'
                    },
                    'volatility_threshold': {
                        'type': 'float',
                        'default': 0.005,
                        'min': 0.001,
                        'max': 0.02,
                        'description': 'Minimum volatility requirement'
                    },
                    'quick_profit_target': {
                        'type': 'float',
                        'default': 0.002,
                        'min': 0.001,
                        'max': 0.01,
                        'description': 'Quick profit target percentage'
                    },
                    'stop_loss': {
                        'type': 'float',
                        'default': 0.003,
                        'min': 0.001,
                        'max': 0.01,
                        'description': 'Stop loss percentage'
                    }
                },
                'tags': ['scalping', 'high_frequency', 'technical_analysis'],
                'risk_level': 'high',
                'min_capital': 1000.0,
                'supported_timeframes': ['1m', '5m']
            },
            {
                'id': 'swing_trading',
                'name': 'Advanced Swing Trading Strategy',
                'description': 'Medium-term swing trading strategy with multi-timeframe analysis and trend following',
                'version': '1.0.0',
                'author': 'System',
                'parameters': {
                    'primary_timeframe': {
                        'type': 'string',
                        'default': '4h',
                        'description': 'Main timeframe for analysis'
                    },
                    'secondary_timeframe': {
                        'type': 'string',
                        'default': '1d',
                        'description': 'Higher timeframe for trend confirmation'
                    },
                    'trend_ema_fast': {
                        'type': 'integer',
                        'default': 21,
                        'min': 5,
                        'max': 50,
                        'description': 'Fast EMA period for trend'
                    },
                    'trend_ema_slow': {
                        'type': 'integer',
                        'default': 50,
                        'min': 20,
                        'max': 200,
                        'description': 'Slow EMA period for trend'
                    },
                    'profit_target': {
                        'type': 'float',
                        'default': 0.08,
                        'min': 0.02,
                        'max': 0.20,
                        'description': 'Profit target percentage'
                    },
                    'stop_loss': {
                        'type': 'float',
                        'default': 0.04,
                        'min': 0.01,
                        'max': 0.10,
                        'description': 'Stop loss percentage'
                    }
                },
                'tags': ['swing_trading', 'trend_following', 'technical_analysis'],
                'risk_level': 'medium',
                'min_capital': 5000.0,
                'supported_timeframes': ['4h', '1d']
            },
            {
                'id': 'arbitrage',
                'name': 'Arbitrage Strategy',
                'description': 'Cross-exchange and triangular arbitrage strategy for risk-free profits',
                'version': '1.0.0',
                'author': 'System',
                'parameters': {
                    'min_profit_threshold': {
                        'type': 'float',
                        'default': 0.005,
                        'min': 0.001,
                        'max': 0.02,
                        'description': 'Minimum profit threshold (as decimal)'
                    },
                    'max_position_size': {
                        'type': 'float',
                        'default': 1000,
                        'min': 100,
                        'max': 10000,
                        'description': 'Maximum position size in USD'
                    },
                    'slippage_tolerance': {
                        'type': 'float',
                        'default': 0.002,
                        'min': 0.001,
                        'max': 0.01,
                        'description': 'Maximum acceptable slippage'
                    },
                    'transaction_cost': {
                        'type': 'float',
                        'default': 0.001,
                        'min': 0.0005,
                        'max': 0.005,
                        'description': 'Estimated transaction cost per trade'
                    },
                    'max_execution_time': {
                        'type': 'integer',
                        'default': 30,
                        'min': 10,
                        'max': 120,
                        'description': 'Maximum execution time in seconds'
                    },
                    'enable_cross_exchange': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Enable cross-exchange arbitrage'
                    },
                    'enable_triangular': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Enable triangular arbitrage'
                    },
                    'enable_spot_futures': {
                        'type': 'boolean',
                        'default': False,
                        'description': 'Enable spot-futures arbitrage'
                    },
                    'max_daily_trades': {
                        'type': 'integer',
                        'default': 50,
                        'min': 10,
                        'max': 200,
                        'description': 'Maximum trades per day'
                    },
                    'max_concurrent_trades': {
                        'type': 'integer',
                        'default': 3,
                        'min': 1,
                        'max': 10,
                        'description': 'Maximum concurrent arbitrage trades'
                    }
                },
                'tags': ['arbitrage', 'cross_exchange', 'risk_free'],
                'risk_level': 'low',
                'min_capital': 2000.0,
                'supported_timeframes': ['1m', '5m']
            }
        ]
    
    def reload_strategies(self):
        """Reload all dynamic strategies
        
        Returns:
            int: Number of strategies reloaded
        """
        if self.enable_dynamic_loading and self.dynamic_manager:
            try:
                count = self.dynamic_manager.reload_all_strategies()
                self.logger.info(f"Reloaded {count} strategies")
                return count
            except Exception as e:
                self.logger.error(f"Failed to reload strategies: {e}")
                return 0
        return 0
    
    def add_strategy_from_code(self, strategy_code: str, strategy_name: str) -> Optional[str]:
        """Add a new strategy from code
        
        Args:
            strategy_code: Python code for the strategy
            strategy_name: Name for the strategy file
            
        Returns:
            Strategy ID if successful, None otherwise
        """
        if self.enable_dynamic_loading and self.dynamic_manager:
            try:
                return self.dynamic_manager.add_strategy_from_code(strategy_code, strategy_name)
            except Exception as e:
                self.logger.error(f"Failed to add strategy from code: {e}")
                return None
        return None
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded strategies
        
        Returns:
            Dictionary with strategy statistics
        """
        if self.enable_dynamic_loading and self.dynamic_manager:
            try:
                return self.dynamic_manager.get_strategy_stats()
            except Exception as e:
                self.logger.error(f"Failed to get strategy stats: {e}")
        
        # Return basic stats for legacy mode
        return {
            'total_strategies': 6,
            'active_strategies': 6,
            'inactive_strategies': 0,
            'dynamic_loading_enabled': False
        }