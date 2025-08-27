import os
import logging
from typing import Optional, Dict, Any

# Legacy imports for backward compatibility
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .ema_crossover_strategy import EMACrossoverStrategy

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
            'total_strategies': 3,
            'active_strategies': 3,
            'inactive_strategies': 0,
            'dynamic_loading_enabled': False
        }