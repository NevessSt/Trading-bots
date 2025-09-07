from typing import Dict, Any, Optional
from .strategies.base_strategy import BaseStrategy
from .strategies.rsi_strategy import RSIStrategy
from .strategies.macd_strategy import MACDStrategy
from .strategies.ema_crossover_strategy import EMACrossoverStrategy
from .strategies.advanced_grid_strategy import AdvancedGridStrategy
from .strategies.smart_dca_strategy import SmartDCAStrategy
from .strategies.advanced_scalping_strategy import AdvancedScalpingStrategy
from .plugin_manager_integration import get_plugin_manager
import logging
import os

class StrategyFactory:
    """Factory class for creating trading strategy instances"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._strategies = {
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'ema_crossover': EMACrossoverStrategy,
            'advanced_grid': AdvancedGridStrategy,
            'smart_dca': SmartDCAStrategy,
            'advanced_scalping': AdvancedScalpingStrategy
        }
    
    def create_strategy(self, strategy_name: str, parameters: Optional[Dict[str, Any]] = None) -> BaseStrategy:
        """Create a strategy instance
        
        Args:
            strategy_name: Name of the strategy to create
            parameters: Strategy parameters
            
        Returns:
            BaseStrategy instance
            
        Raises:
            ValueError: If strategy name is not found
        """
        try:
            # First try plugin strategies
            try:
                plugin_manager = get_plugin_manager()
                plugin_strategies = {p.name: p for p in plugin_manager.strategy_factory.plugin_system.list_plugins('strategy')}
                
                if strategy_name in plugin_strategies:
                    strategy_instance = plugin_manager.strategy_factory.plugin_system.create_strategy_instance(strategy_name)
                    if parameters:
                        strategy_instance.set_parameters(parameters)
                    self.logger.info(f"Created plugin strategy instance: {strategy_name}")
                    return strategy_instance
            except Exception as e:
                self.logger.debug(f"Plugin strategy creation failed for {strategy_name}: {e}")
            
            # Then try built-in strategies
            if strategy_name not in self._strategies:
                available = list(self._strategies.keys())
                raise ValueError(f"Unknown strategy '{strategy_name}'. Available strategies: {available}")
            
            strategy_class = self._strategies[strategy_name]
            strategy_instance = strategy_class()
            
            # Set parameters if provided
            if parameters:
                strategy_instance.set_parameters(parameters)
            
            self.logger.info(f"Created strategy instance: {strategy_name}")
            return strategy_instance
            
        except Exception as e:
            self.logger.error(f"Failed to create strategy {strategy_name}: {e}")
            raise
    
    def get_available_strategies(self) -> Dict[str, str]:
        """Get list of available strategies with descriptions including plugins"""
        descriptions = {
            'rsi': 'RSI-based momentum strategy with overbought/oversold signals',
            'macd': 'MACD crossover strategy for trend following',
            'ema_crossover': 'EMA crossover strategy for trend identification',
            'advanced_grid': 'Advanced grid trading with dynamic spacing',
            'smart_dca': 'Intelligent Dollar Cost Averaging with market analysis',
            'advanced_scalping': 'High-frequency scalping with multi-timeframe analysis'
        }
        
        # Add plugin strategies
        try:
            plugin_manager = get_plugin_manager()
            plugin_strategies = plugin_manager.strategy_factory.get_available_strategies()
            
            # Filter out legacy strategies to avoid duplicates
            for strategy_id, strategy_info in plugin_strategies.items():
                if strategy_info.get('type') == 'plugin':
                    descriptions[strategy_id] = strategy_info.get('description', f'Plugin strategy: {strategy_id}')
        except Exception as e:
            self.logger.warning(f"Failed to load plugin strategies: {e}")
        
        return descriptions
    
    def get_strategy_parameters(self, strategy_name: str) -> Dict[str, Any]:
        """Get default parameters for a strategy"""
        defaults = {
            'rsi': {
                'period': {'type': 'int', 'default': 14, 'min': 5, 'max': 50, 'description': 'RSI calculation period'},
                'overbought': {'type': 'float', 'default': 70, 'min': 60, 'max': 90, 'description': 'Overbought threshold'},
                'oversold': {'type': 'float', 'default': 30, 'min': 10, 'max': 40, 'description': 'Oversold threshold'}
            },
            'macd': {
                'fast_period': {'type': 'int', 'default': 12, 'min': 5, 'max': 20, 'description': 'Fast EMA period'},
                'slow_period': {'type': 'int', 'default': 26, 'min': 20, 'max': 50, 'description': 'Slow EMA period'},
                'signal_period': {'type': 'int', 'default': 9, 'min': 5, 'max': 15, 'description': 'Signal line period'}
            },
            'ema_crossover': {
                'fast_period': {'type': 'int', 'default': 12, 'min': 5, 'max': 20, 'description': 'Fast EMA period'},
                'slow_period': {'type': 'int', 'default': 26, 'min': 20, 'max': 50, 'description': 'Slow EMA period'}
            },
            'advanced_grid': {
                'grid_size': {'type': 'int', 'default': 10, 'min': 5, 'max': 50, 'description': 'Number of grid levels'},
                'grid_spacing': {'type': 'float', 'default': 0.01, 'min': 0.005, 'max': 0.05, 'description': 'Grid spacing percentage'},
                'base_order_size': {'type': 'float', 'default': 0.01, 'min': 0.001, 'max': 0.1, 'description': 'Base order size'},
                'safety_order_size': {'type': 'float', 'default': 0.02, 'min': 0.001, 'max': 0.2, 'description': 'Safety order size'}
            },
            'smart_dca': {
                'dca_levels': {'type': 'int', 'default': 5, 'min': 2, 'max': 20, 'description': 'Number of DCA levels'},
                'dca_multiplier': {'type': 'float', 'default': 1.5, 'min': 1.1, 'max': 3.0, 'description': 'DCA size multiplier'},
                'price_deviation': {'type': 'float', 'default': 0.02, 'min': 0.01, 'max': 0.1, 'description': 'Price deviation for DCA trigger'},
                'cooldown_period': {'type': 'int', 'default': 300, 'min': 60, 'max': 3600, 'description': 'Cooldown between orders (seconds)'}
            },
            'advanced_scalping': {
                'scalp_target': {'type': 'float', 'default': 0.005, 'min': 0.001, 'max': 0.02, 'description': 'Scalping profit target'},
                'max_hold_time': {'type': 'int', 'default': 300, 'min': 60, 'max': 1800, 'description': 'Maximum hold time (seconds)'},
                'volume_threshold': {'type': 'float', 'default': 1.5, 'min': 1.0, 'max': 5.0, 'description': 'Volume threshold multiplier'},
                'spread_threshold': {'type': 'float', 'default': 0.001, 'min': 0.0005, 'max': 0.005, 'description': 'Maximum spread threshold'}
            }
        }
        
        return defaults.get(strategy_name, {})
    
    def validate_parameters(self, strategy_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize strategy parameters
        
        Args:
            strategy_name: Name of the strategy
            parameters: Parameters to validate
            
        Returns:
            Dict with validation results and sanitized parameters
        """
        if strategy_name not in self._strategies:
            return {'valid': False, 'error': f'Unknown strategy: {strategy_name}'}
        
        param_specs = self.get_strategy_parameters(strategy_name)
        sanitized = {}
        errors = []
        
        for param_name, param_spec in param_specs.items():
            if param_name in parameters:
                value = parameters[param_name]
                param_type = param_spec['type']
                
                # Type validation
                try:
                    if param_type == 'int':
                        value = int(value)
                    elif param_type == 'float':
                        value = float(value)
                    elif param_type == 'str':
                        value = str(value)
                except (ValueError, TypeError):
                    errors.append(f"Invalid type for {param_name}: expected {param_type}")
                    continue
                
                # Range validation
                if 'min' in param_spec and value < param_spec['min']:
                    errors.append(f"{param_name} must be >= {param_spec['min']}")
                    continue
                
                if 'max' in param_spec and value > param_spec['max']:
                    errors.append(f"{param_name} must be <= {param_spec['max']}")
                    continue
                
                sanitized[param_name] = value
            else:
                # Use default value
                sanitized[param_name] = param_spec['default']
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        return {'valid': True, 'parameters': sanitized}