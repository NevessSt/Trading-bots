import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

class StrategyTemplateGenerator:
    """Generator for creating new trading strategy templates with standardized structure"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the strategy template generator
        
        Args:
            output_dir: Directory to output generated strategies
        """
        self.logger = logging.getLogger(__name__)
        
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), 'strategies', 'generated')
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Template configurations
        self.strategy_types = {
            'trend_following': {
                'base_indicators': ['sma', 'ema', 'macd'],
                'signal_logic': 'crossover',
                'risk_profile': 'medium'
            },
            'mean_reversion': {
                'base_indicators': ['rsi', 'bollinger_bands', 'stochastic'],
                'signal_logic': 'threshold',
                'risk_profile': 'high'
            },
            'momentum': {
                'base_indicators': ['rsi', 'macd', 'atr'],
                'signal_logic': 'momentum',
                'risk_profile': 'high'
            },
            'arbitrage': {
                'base_indicators': ['price_spread', 'volume'],
                'signal_logic': 'spread_analysis',
                'risk_profile': 'low'
            },
            'custom': {
                'base_indicators': [],
                'signal_logic': 'custom',
                'risk_profile': 'medium'
            }
        }
    
    def generate_strategy(self, 
                         strategy_name: str,
                         strategy_type: str,
                         parameters: Dict[str, Any],
                         author: str = "Generated",
                         description: str = None) -> str:
        """
        Generate a new strategy template
        
        Args:
            strategy_name: Name of the strategy
            strategy_type: Type of strategy (trend_following, mean_reversion, etc.)
            parameters: Strategy parameters with types and defaults
            author: Strategy author
            description: Strategy description
            
        Returns:
            Path to the generated strategy file
        """
        if strategy_type not in self.strategy_types:
            raise ValueError(f"Unknown strategy type: {strategy_type}. Available: {list(self.strategy_types.keys())}")
        
        if description is None:
            description = f"Auto-generated {strategy_type} strategy"
        
        # Generate class name
        class_name = self._to_class_name(strategy_name)
        file_name = self._to_file_name(strategy_name)
        
        # Generate strategy code
        strategy_code = self._generate_strategy_code(
            class_name=class_name,
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            parameters=parameters,
            author=author,
            description=description
        )
        
        # Write to file
        file_path = self.output_dir / f"{file_name}.py"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(strategy_code)
        
        # Generate metadata file
        self._generate_metadata_file(file_path, {
            'id': file_name,
            'name': strategy_name,
            'class_name': class_name,
            'strategy_type': strategy_type,
            'parameters': parameters,
            'author': author,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0'
        })
        
        self.logger.info(f"Generated strategy '{strategy_name}' at {file_path}")
        return str(file_path)
    
    def _generate_strategy_code(self, 
                               class_name: str,
                               strategy_name: str,
                               strategy_type: str,
                               parameters: Dict[str, Any],
                               author: str,
                               description: str) -> str:
        """
        Generate the actual strategy code
        """
        template_config = self.strategy_types[strategy_type]
        
        # Generate imports
        imports = self._generate_imports(template_config)
        
        # Generate parameter initialization
        param_init = self._generate_parameter_init(parameters)
        
        # Generate signal logic based on strategy type
        signal_logic = self._generate_signal_logic(strategy_type, template_config, parameters)
        
        # Generate parameter bounds
        param_bounds = self._generate_parameter_bounds(parameters)
        
        return f'''import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
{imports}
from ..base_strategy import BaseStrategy

class {class_name}(BaseStrategy):
    """
    {description}
    
    Strategy Type: {strategy_type}
    Author: {author}
    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the {strategy_name} strategy
        
        Parameters:
{self._generate_param_docstring(parameters)}
        """
        super().__init__()
        self.name = '{strategy_name}'
        self.description = '{description}'
        self.strategy_type = '{strategy_type}'
        self.logger = logging.getLogger(f"{{__name__}}.{{self.name}}")
        
        # Initialize parameters with defaults
{param_init}
        
        # Update with provided parameters
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.logger.warning(f"Unknown parameter: {{key}}")
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the strategy logic
        
        Args:
            df: OHLCV DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            DataFrame with additional columns for signals and indicators
        """
        try:
            # Make a copy to avoid modifying original data
            result_df = df.copy()
            
            # Ensure we have enough data
            if len(df) < self._get_min_periods():
                self.logger.warning(f"Insufficient data: {{len(df)}} < {{self._get_min_periods()}}")
                result_df['signal'] = 0
                return result_df
            
{signal_logic}
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {{e}}")
            result_df = df.copy()
            result_df['signal'] = 0
            return result_df
    
    def _get_min_periods(self) -> int:
        """
        Get minimum number of periods required for signal generation
        """
        # Calculate based on parameters
{self._generate_min_periods_logic(parameters)}
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current strategy parameters
        
        Returns:
            Dictionary of parameter names and values
        """
        return {{
{self._generate_get_parameters(parameters)}
        }}
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """
        Update strategy parameters
        
        Args:
            parameters: Dictionary of parameter names and values
        """
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.logger.info(f"Updated {{key}} = {{value}}")
            else:
                self.logger.warning(f"Unknown parameter: {{key}}")
    
    def get_parameter_bounds(self) -> Dict[str, tuple]:
        """
        Get parameter bounds for optimization
        
        Returns:
            Dictionary of parameter bounds (min, max)
        """
        return {{
{param_bounds}
        }}
    
    def validate_parameters(self) -> bool:
        """
        Validate current parameters
        
        Returns:
            True if parameters are valid, False otherwise
        """
        bounds = self.get_parameter_bounds()
        
        for param_name, (min_val, max_val) in bounds.items():
            current_val = getattr(self, param_name)
            if not (min_val <= current_val <= max_val):
                self.logger.error(f"Parameter {{param_name}} = {{current_val}} is out of bounds [{{min_val}}, {{max_val}}]")
                return False
        
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy information
        
        Returns:
            Dictionary with strategy metadata
        """
        return {{
            'name': self.name,
            'description': self.description,
            'strategy_type': self.strategy_type,
            'parameters': self.get_parameters(),
            'parameter_bounds': self.get_parameter_bounds(),
            'min_periods': self._get_min_periods(),
            'risk_profile': '{template_config['risk_profile']}',
            'indicators': {template_config['base_indicators']}
        }}
'''
    
    def _generate_imports(self, template_config: Dict[str, Any]) -> str:
        """Generate necessary imports based on indicators"""
        imports = []
        
        indicators = template_config.get('base_indicators', [])
        if 'sma' in indicators or 'ema' in indicators:
            imports.append("# Technical analysis imports")
        if 'rsi' in indicators:
            imports.append("# RSI calculation imports")
        if 'macd' in indicators:
            imports.append("# MACD calculation imports")
        if 'bollinger_bands' in indicators:
            imports.append("# Bollinger Bands calculation imports")
            
        return '\n'.join(imports) if imports else ''
    
    def _generate_parameter_init(self, parameters: Dict[str, Any]) -> str:
        """Generate parameter initialization code"""
        lines = []
        for param_name, param_config in parameters.items():
            default_value = param_config.get('default', 0)
            if isinstance(default_value, str):
                lines.append(f"        self.{param_name} = '{default_value}'")
            else:
                lines.append(f"        self.{param_name} = {default_value}")
        return '\n'.join(lines)
    
    def _generate_signal_logic(self, strategy_type: str, template_config: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Generate signal logic based on strategy type"""
        if strategy_type == 'trend_following':
            return self._generate_trend_following_logic(parameters)
        elif strategy_type == 'mean_reversion':
            return self._generate_mean_reversion_logic(parameters)
        elif strategy_type == 'momentum':
            return self._generate_momentum_logic(parameters)
        elif strategy_type == 'arbitrage':
            return self._generate_arbitrage_logic(parameters)
        else:
            return self._generate_custom_logic(parameters)
    
    def _generate_trend_following_logic(self, parameters: Dict[str, Any]) -> str:
        """Generate trend following signal logic"""
        return '''            # Calculate moving averages
            result_df['sma_fast'] = result_df['close'].rolling(window=self.fast_period).mean()
            result_df['sma_slow'] = result_df['close'].rolling(window=self.slow_period).mean()
            
            # Generate signals based on crossover
            result_df['signal'] = 0
            result_df.loc[result_df['sma_fast'] > result_df['sma_slow'], 'signal'] = 1  # Buy signal
            result_df.loc[result_df['sma_fast'] < result_df['sma_slow'], 'signal'] = -1  # Sell signal
            
            # Add signal strength
            result_df['signal_strength'] = abs(result_df['sma_fast'] - result_df['sma_slow']) / result_df['close']
            
            self.logger.debug(f"Generated {len(result_df[result_df['signal'] != 0])} signals")'''
    
    def _generate_mean_reversion_logic(self, parameters: Dict[str, Any]) -> str:
        """Generate mean reversion signal logic"""
        return '''            # Calculate RSI
            delta = result_df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            result_df['rsi'] = 100 - (100 / (1 + rs))
            
            # Generate signals based on RSI thresholds
            result_df['signal'] = 0
            result_df.loc[result_df['rsi'] < self.oversold_threshold, 'signal'] = 1  # Buy signal
            result_df.loc[result_df['rsi'] > self.overbought_threshold, 'signal'] = -1  # Sell signal
            
            # Add signal strength based on RSI distance from thresholds
            result_df['signal_strength'] = np.where(
                result_df['signal'] == 1,
                (self.oversold_threshold - result_df['rsi']) / self.oversold_threshold,
                np.where(
                    result_df['signal'] == -1,
                    (result_df['rsi'] - self.overbought_threshold) / (100 - self.overbought_threshold),
                    0
                )
            )
            
            self.logger.debug(f"Generated {len(result_df[result_df['signal'] != 0])} signals")'''
    
    def _generate_momentum_logic(self, parameters: Dict[str, Any]) -> str:
        """Generate momentum signal logic"""
        return '''            # Calculate momentum indicators
            result_df['price_change'] = result_df['close'].pct_change(periods=self.momentum_period)
            result_df['volume_sma'] = result_df['volume'].rolling(window=self.volume_period).mean()
            result_df['volume_ratio'] = result_df['volume'] / result_df['volume_sma']
            
            # Generate signals based on momentum and volume
            result_df['signal'] = 0
            
            # Buy signals: positive momentum with high volume
            buy_condition = (
                (result_df['price_change'] > self.momentum_threshold) &
                (result_df['volume_ratio'] > self.volume_threshold)
            )
            result_df.loc[buy_condition, 'signal'] = 1
            
            # Sell signals: negative momentum with high volume
            sell_condition = (
                (result_df['price_change'] < -self.momentum_threshold) &
                (result_df['volume_ratio'] > self.volume_threshold)
            )
            result_df.loc[sell_condition, 'signal'] = -1
            
            # Add signal strength
            result_df['signal_strength'] = abs(result_df['price_change']) * result_df['volume_ratio']
            
            self.logger.debug(f"Generated {len(result_df[result_df['signal'] != 0])} signals")'''
    
    def _generate_arbitrage_logic(self, parameters: Dict[str, Any]) -> str:
        """Generate arbitrage signal logic"""
        return '''            # Calculate price spreads and opportunities
            result_df['price_sma'] = result_df['close'].rolling(window=self.spread_period).mean()
            result_df['price_spread'] = (result_df['close'] - result_df['price_sma']) / result_df['price_sma']
            
            # Generate signals based on spread thresholds
            result_df['signal'] = 0
            result_df.loc[result_df['price_spread'] > self.spread_threshold, 'signal'] = -1  # Sell (overpriced)
            result_df.loc[result_df['price_spread'] < -self.spread_threshold, 'signal'] = 1  # Buy (underpriced)
            
            # Add signal strength based on spread magnitude
            result_df['signal_strength'] = abs(result_df['price_spread'])
            
            self.logger.debug(f"Generated {len(result_df[result_df['signal'] != 0])} signals")'''
    
    def _generate_custom_logic(self, parameters: Dict[str, Any]) -> str:
        """Generate custom signal logic template"""
        return '''            # TODO: Implement custom signal logic
            # This is a template - customize based on your strategy requirements
            
            # Example: Simple price-based signals
            result_df['signal'] = 0
            result_df['signal_strength'] = 0.5
            
            # Add your custom indicators and signal logic here
            # Example:
            # result_df['custom_indicator'] = your_calculation(result_df)
            # result_df.loc[your_buy_condition, 'signal'] = 1
            # result_df.loc[your_sell_condition, 'signal'] = -1
            
            self.logger.debug(f"Generated {len(result_df[result_df['signal'] != 0])} signals")'''
    
    def _generate_parameter_bounds(self, parameters: Dict[str, Any]) -> str:
        """Generate parameter bounds code"""
        lines = []
        for param_name, param_config in parameters.items():
            min_val = param_config.get('min', 1)
            max_val = param_config.get('max', 100)
            lines.append(f"            '{param_name}': ({min_val}, {max_val}),")
        return '\n'.join(lines)
    
    def _generate_min_periods_logic(self, parameters: Dict[str, Any]) -> str:
        """Generate minimum periods calculation"""
        period_params = []
        for param_name, param_config in parameters.items():
            if 'period' in param_name.lower():
                period_params.append(f"self.{param_name}")
        
        if period_params:
            return f"        return max({', '.join(period_params)}) + 10"
        else:
            return "        return 50  # Default minimum periods"
    
    def _generate_get_parameters(self, parameters: Dict[str, Any]) -> str:
        """Generate get_parameters method body"""
        lines = []
        for param_name in parameters.keys():
            lines.append(f"            '{param_name}': self.{param_name},")
        return '\n'.join(lines)
    
    def _generate_param_docstring(self, parameters: Dict[str, Any]) -> str:
        """Generate parameter documentation"""
        lines = []
        for param_name, param_config in parameters.items():
            param_type = param_config.get('type', 'float')
            default = param_config.get('default', 'N/A')
            description = param_config.get('description', f'{param_name} parameter')
            lines.append(f"        {param_name} ({param_type}): {description} (default: {default})")
        return '\n'.join(lines)
    
    def _generate_metadata_file(self, strategy_file: Path, metadata: Dict[str, Any]):
        """Generate metadata file for the strategy"""
        metadata_file = strategy_file.with_suffix('.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def _to_class_name(self, strategy_name: str) -> str:
        """Convert strategy name to class name"""
        # Remove special characters and convert to PascalCase
        words = ''.join(c if c.isalnum() else ' ' for c in strategy_name).split()
        return ''.join(word.capitalize() for word in words) + 'Strategy'
    
    def _to_file_name(self, strategy_name: str) -> str:
        """Convert strategy name to file name"""
        # Convert to snake_case
        name = ''.join(c if c.isalnum() else '_' for c in strategy_name.lower())
        # Remove multiple underscores
        while '__' in name:
            name = name.replace('__', '_')
        return name.strip('_') + '_strategy'
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List available strategy templates"""
        return [
            {
                'type': strategy_type,
                'description': f"{strategy_type.replace('_', ' ').title()} strategy template",
                'indicators': config['base_indicators'],
                'signal_logic': config['signal_logic'],
                'risk_profile': config['risk_profile']
            }
            for strategy_type, config in self.strategy_types.items()
        ]
    
    def generate_example_strategies(self):
        """Generate example strategies for each template type"""
        examples = {
            'trend_following': {
                'name': 'Dual Moving Average Crossover',
                'parameters': {
                    'fast_period': {'type': 'int', 'default': 10, 'min': 5, 'max': 50, 'description': 'Fast moving average period'},
                    'slow_period': {'type': 'int', 'default': 30, 'min': 20, 'max': 100, 'description': 'Slow moving average period'}
                }
            },
            'mean_reversion': {
                'name': 'RSI Mean Reversion',
                'parameters': {
                    'rsi_period': {'type': 'int', 'default': 14, 'min': 5, 'max': 30, 'description': 'RSI calculation period'},
                    'oversold_threshold': {'type': 'float', 'default': 30, 'min': 10, 'max': 40, 'description': 'RSI oversold threshold'},
                    'overbought_threshold': {'type': 'float', 'default': 70, 'min': 60, 'max': 90, 'description': 'RSI overbought threshold'}
                }
            },
            'momentum': {
                'name': 'Volume Momentum',
                'parameters': {
                    'momentum_period': {'type': 'int', 'default': 5, 'min': 1, 'max': 20, 'description': 'Momentum calculation period'},
                    'momentum_threshold': {'type': 'float', 'default': 0.02, 'min': 0.01, 'max': 0.1, 'description': 'Minimum momentum for signal'},
                    'volume_period': {'type': 'int', 'default': 20, 'min': 10, 'max': 50, 'description': 'Volume average period'},
                    'volume_threshold': {'type': 'float', 'default': 1.5, 'min': 1.0, 'max': 3.0, 'description': 'Volume ratio threshold'}
                }
            },
            'arbitrage': {
                'name': 'Price Spread Arbitrage',
                'parameters': {
                    'spread_period': {'type': 'int', 'default': 20, 'min': 10, 'max': 50, 'description': 'Spread calculation period'},
                    'spread_threshold': {'type': 'float', 'default': 0.01, 'min': 0.005, 'max': 0.05, 'description': 'Minimum spread for signal'}
                }
            }
        }
        
        generated_files = []
        for strategy_type, config in examples.items():
            try:
                file_path = self.generate_strategy(
                    strategy_name=config['name'],
                    strategy_type=strategy_type,
                    parameters=config['parameters'],
                    author="Template Generator",
                    description=f"Example {strategy_type} strategy generated from template"
                )
                generated_files.append(file_path)
            except Exception as e:
                self.logger.error(f"Failed to generate example {strategy_type}: {e}")
        
        return generated_files