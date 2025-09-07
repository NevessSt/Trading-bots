# Trading Bot Plugin System Guide

## Overview

The Trading Bot Plugin System provides a flexible and extensible framework for adding custom trading strategies and technical indicators without modifying the core codebase. This system supports hot-reloading, dependency management, and comprehensive validation.

## Features

- **Strategy Plugins**: Create custom trading strategies with standardized interfaces
- **Indicator Plugins**: Develop technical indicators with reusable calculations
- **Hot Reloading**: Automatically reload plugins when files change
- **Dependency Management**: Automatic validation of required packages
- **Template Generation**: Built-in templates for quick plugin development
- **Plugin Marketplace**: Share and discover community plugins
- **Performance Monitoring**: Track plugin execution times and performance

## Architecture

```
Plugin System Architecture:

┌─────────────────────────────────────────────────────────────┐
│                    Plugin Manager                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Strategy Plugins│    │    Indicator Plugins            │ │
│  │                 │    │                                 │ │
│  │ • Momentum      │    │ • Bollinger Bands              │ │
│  │ • Mean Reversion│    │ • Custom RSI                    │ │
│  │ • Arbitrage     │    │ • MACD Variants                 │ │
│  │ • Custom Logic  │    │ • Volume Indicators             │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Plugin System Core                          │
│  • Discovery & Loading  • Validation  • Hot Reload         │
├─────────────────────────────────────────────────────────────┤
│              Integration Layer                              │
│  • Strategy Factory  • Indicator Manager  • API Routes     │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Creating Your First Strategy Plugin

```python
# Generate a template
from bot_engine.plugin_manager_integration import get_plugin_manager

manager = get_plugin_manager()
template_path = manager.create_custom_strategy_template("My Custom Strategy")
print(f"Template created at: {template_path}")
```

### 2. Basic Strategy Plugin Structure

```python
from typing import Dict, Any, Type
from datetime import datetime
import pandas as pd
import numpy as np
from ..strategy_plugin_system import StrategyPlugin
from ..strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    """Your custom trading strategy"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.name = 'My Custom Strategy'
        self.description = 'Description of your strategy'
        
        # Strategy parameters
        self.param1 = kwargs.get('param1', 10)
        self.param2 = kwargs.get('param2', 0.02)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        result_df = df.copy()
        
        # Your signal logic here
        result_df['signal'] = 0  # 1 for buy, -1 for sell, 0 for hold
        result_df['signal_strength'] = 0.5  # 0-1 confidence score
        
        return result_df
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'param1': self.param1,
            'param2': self.param2
        }
    
    def set_parameters(self, parameters: Dict[str, Any]):
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)

class MyCustomPlugin(StrategyPlugin):
    """Plugin wrapper"""
    
    def get_strategy_class(self) -> Type:
        return MyCustomStrategy
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'id': 'my_custom_strategy',
            'name': 'My Custom Strategy',
            'version': '1.0.0',
            'author': 'Your Name',
            'description': 'Your strategy description',
            'type': 'strategy',
            'parameters': {
                'param1': {
                    'type': 'int',
                    'default': 10,
                    'min': 1,
                    'max': 100,
                    'description': 'Parameter 1 description'
                }
            }
        }
```

### 3. Basic Indicator Plugin Structure

```python
from typing import Dict, Any
import pandas as pd
import numpy as np
from ..strategy_plugin_system import IndicatorPlugin

class MyCustomIndicator(IndicatorPlugin):
    """Your custom indicator"""
    
    def __init__(self, period: int = 14, **kwargs):
        self.period = period
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> pd.Series:
        """Calculate the indicator"""
        # Your calculation logic here
        return data['close'].rolling(window=self.period).mean()
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'id': 'my_custom_indicator',
            'name': 'My Custom Indicator',
            'version': '1.0.0',
            'author': 'Your Name',
            'description': 'Your indicator description',
            'type': 'indicator'
        }
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        return 'close' in data.columns and len(data) >= self.period
```

## Plugin Development Guide

### Strategy Plugin Development

#### Required Methods

1. **`generate_signals(df: pd.DataFrame) -> pd.DataFrame`**
   - Main logic for generating trading signals
   - Must return DataFrame with 'signal' and 'signal_strength' columns
   - Signal values: 1 (buy), -1 (sell), 0 (hold)
   - Signal strength: 0.0-1.0 confidence score

2. **`get_parameters() -> Dict[str, Any]`**
   - Return current parameter values
   - Used for serialization and UI display

3. **`set_parameters(parameters: Dict[str, Any])`**
   - Update strategy parameters
   - Should validate parameter values

#### Optional Methods

- **`backtest(data: pd.DataFrame) -> Dict[str, Any]`**: Run backtesting
- **`get_parameter_bounds() -> Dict[str, Dict[str, Any]]`**: Parameter validation
- **`calculate_position_size(signal_strength: float) -> float`**: Position sizing

#### Best Practices

1. **Parameter Validation**
```python
def set_parameters(self, parameters: Dict[str, Any]):
    for key, value in parameters.items():
        if key == 'period' and not (5 <= value <= 100):
            raise ValueError(f"Period must be between 5 and 100, got {value}")
        if hasattr(self, key):
            setattr(self, key, value)
```

2. **Error Handling**
```python
def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
    try:
        result_df = df.copy()
        # Your logic here
        return result_df
    except Exception as e:
        self.logger.error(f"Signal generation failed: {e}")
        # Return safe default
        result_df = df.copy()
        result_df['signal'] = 0
        result_df['signal_strength'] = 0.0
        return result_df
```

3. **Performance Optimization**
```python
# Use vectorized operations
result_df['sma'] = df['close'].rolling(window=self.period).mean()

# Avoid loops when possible
# BAD:
for i in range(len(df)):
    result_df.loc[i, 'signal'] = calculate_signal(df.iloc[i])

# GOOD:
result_df['signal'] = np.where(condition, 1, 0)
```

### Indicator Plugin Development

#### Required Methods

1. **`calculate(data: pd.DataFrame, **kwargs) -> Any`**
   - Main calculation logic
   - Can return Series, DataFrame, or Dict of Series
   - Should handle edge cases gracefully

2. **`get_metadata() -> Dict[str, Any]`**
   - Plugin information and parameters
   - Used for discovery and UI generation

3. **`validate_data(data: pd.DataFrame) -> bool`**
   - Validate input data requirements
   - Check for required columns and minimum data length

#### Advanced Features

1. **Multiple Outputs**
```python
def calculate(self, data: pd.DataFrame, **kwargs) -> Dict[str, pd.Series]:
    price = data['close']
    sma = price.rolling(window=self.period).mean()
    std = price.rolling(window=self.period).std()
    
    return {
        'sma': sma,
        'upper_band': sma + (std * 2),
        'lower_band': sma - (std * 2),
        'bandwidth': (std * 4) / sma
    }
```

2. **Parameter Validation**
```python
def validate_data(self, data: pd.DataFrame) -> bool:
    required_columns = ['close', 'volume']
    return (
        all(col in data.columns for col in required_columns) and
        len(data) >= self.period and
        not data[required_columns].isna().all().any()
    )
```

## Plugin Management

### Installing Plugins

```python
from bot_engine.plugin_manager_integration import install_plugin

# Install from file
plugin_id = install_plugin('/path/to/my_plugin.py')
print(f"Installed plugin: {plugin_id}")
```

### Listing Available Plugins

```python
from bot_engine.plugin_manager_integration import get_available_strategies, get_available_indicators

# List strategies
strategies = get_available_strategies()
for name, info in strategies.items():
    print(f"{name}: {info['description']}")

# List indicators
indicators = get_available_indicators()
for name, info in indicators.items():
    print(f"{name}: {info['description']}")
```

### Using Plugins

```python
from bot_engine.plugin_manager_integration import create_strategy, calculate_indicator
import pandas as pd

# Create strategy instance
strategy = create_strategy('my_custom_strategy', param1=20, param2=0.05)

# Generate signals
data = pd.DataFrame(...)  # Your market data
signals = strategy.generate_signals(data)

# Calculate indicator
indicator_result = calculate_indicator('bollinger_bands', data, period=20, std_dev=2.0)
```

## Configuration

### Plugin System Configuration

Edit `plugin_config.json` to customize plugin system behavior:

```json
{
  "auto_reload": true,
  "validate_plugins": true,
  "max_plugins": 100,
  "plugin_timeout": 30,
  "development_mode": {
    "enable_hot_reload": true,
    "debug_logging": true,
    "allow_unsigned_plugins": true
  },
  "performance_monitoring": {
    "enable_metrics": true,
    "log_execution_time": true,
    "max_execution_time_ms": 5000
  }
}
```

### Plugin Directories

Default plugin locations:
- `backend/bot_engine/plugins/strategies/` - Strategy plugins
- `backend/bot_engine/plugins/indicators/` - Indicator plugins
- `backend/bot_engine/strategies/custom/` - Custom strategies

## Testing Plugins

### Unit Testing

```python
import unittest
import pandas as pd
import numpy as np
from your_plugin import MyCustomStrategy

class TestMyCustomStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = MyCustomStrategy(param1=10, param2=0.02)
        
        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='1H')
        self.test_data = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100)
        })
    
    def test_generate_signals(self):
        """Test signal generation"""
        result = self.strategy.generate_signals(self.test_data)
        
        # Check required columns exist
        self.assertIn('signal', result.columns)
        self.assertIn('signal_strength', result.columns)
        
        # Check signal values are valid
        self.assertTrue(result['signal'].isin([-1, 0, 1]).all())
        self.assertTrue((result['signal_strength'] >= 0).all())
        self.assertTrue((result['signal_strength'] <= 1).all())
    
    def test_parameters(self):
        """Test parameter management"""
        # Test get_parameters
        params = self.strategy.get_parameters()
        self.assertEqual(params['param1'], 10)
        self.assertEqual(params['param2'], 0.02)
        
        # Test set_parameters
        new_params = {'param1': 20, 'param2': 0.05}
        self.strategy.set_parameters(new_params)
        
        updated_params = self.strategy.get_parameters()
        self.assertEqual(updated_params['param1'], 20)
        self.assertEqual(updated_params['param2'], 0.05)

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```python
def test_plugin_integration():
    """Test plugin system integration"""
    from bot_engine.plugin_manager_integration import get_plugin_manager
    
    manager = get_plugin_manager()
    
    # Test plugin loading
    strategies = manager.strategy_factory.get_available_strategies()
    assert 'my_custom_strategy' in strategies
    
    # Test strategy creation
    strategy = manager.strategy_factory.create_strategy('my_custom_strategy')
    assert strategy is not None
    
    # Test signal generation
    test_data = create_test_data()
    signals = strategy.generate_signals(test_data)
    assert 'signal' in signals.columns
```

## Performance Optimization

### Profiling Plugins

```python
import cProfile
import pstats
from bot_engine.plugin_manager_integration import create_strategy

def profile_strategy(strategy_name: str, data: pd.DataFrame):
    """Profile strategy performance"""
    strategy = create_strategy(strategy_name)
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run strategy
    signals = strategy.generate_signals(data)
    
    profiler.disable()
    
    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return signals
```

### Optimization Tips

1. **Use Vectorized Operations**
   - Prefer pandas/numpy operations over Python loops
   - Use `.rolling()`, `.shift()`, `.diff()` for time series operations

2. **Minimize Data Copying**
   - Use `.copy()` only when necessary
   - Modify DataFrames in-place when possible

3. **Cache Expensive Calculations**
   - Store intermediate results
   - Use `@lru_cache` for pure functions

4. **Optimize Memory Usage**
   - Use appropriate data types (float32 vs float64)
   - Drop unnecessary columns early

## Troubleshooting

### Common Issues

1. **Plugin Not Loading**
   - Check file permissions
   - Verify plugin syntax
   - Check plugin directory configuration
   - Review logs for error messages

2. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify relative imports

3. **Performance Issues**
   - Profile plugin execution
   - Check for infinite loops
   - Optimize data operations
   - Reduce memory usage

4. **Signal Generation Errors**
   - Validate input data format
   - Handle edge cases (empty data, NaN values)
   - Check parameter bounds
   - Add error handling

### Debug Mode

Enable debug mode in `plugin_config.json`:

```json
{
  "development_mode": {
    "debug_logging": true,
    "enable_hot_reload": true
  },
  "logging": {
    "log_level": "DEBUG"
  }
}
```

### Log Analysis

Check plugin system logs:

```bash
# View recent plugin logs
tail -f logs/plugin_system.log

# Search for specific errors
grep "ERROR" logs/plugin_system.log

# Monitor plugin performance
grep "execution_time" logs/plugin_system.log
```

## Contributing

### Plugin Submission Guidelines

1. **Code Quality**
   - Follow PEP 8 style guidelines
   - Include comprehensive docstrings
   - Add type hints
   - Write unit tests

2. **Documentation**
   - Provide clear description
   - Document all parameters
   - Include usage examples
   - Add performance characteristics

3. **Testing**
   - Test with various market conditions
   - Validate edge cases
   - Benchmark performance
   - Test parameter ranges

### Plugin Review Process

1. Submit plugin file and documentation
2. Automated testing and validation
3. Code review by maintainers
4. Performance and security review
5. Integration testing
6. Publication to plugin marketplace

## API Reference

### StrategyPlugin Interface

```python
class StrategyPlugin(ABC):
    @abstractmethod
    def get_strategy_class(self) -> Type:
        """Return the strategy class"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        pass
    
    def get_dependencies(self) -> List[str]:
        """Return list of required dependencies"""
        return []
    
    def validate_environment(self) -> bool:
        """Validate that the environment supports this plugin"""
        return True
```

### IndicatorPlugin Interface

```python
class IndicatorPlugin(ABC):
    @abstractmethod
    def calculate(self, data: Any, **kwargs) -> Any:
        """Calculate the indicator"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return indicator metadata"""
        pass
    
    def validate_data(self, data: Any) -> bool:
        """Validate input data"""
        return True
```

### Plugin Manager Methods

```python
# Strategy management
create_strategy(strategy_name: str, **kwargs)
get_available_strategies() -> Dict[str, Dict[str, Any]]
install_plugin(plugin_file: str) -> Optional[str]

# Indicator management
calculate_indicator(indicator_name: str, data, **kwargs)
get_available_indicators() -> Dict[str, Dict[str, Any]]

# System management
get_plugin_manager() -> PluginManagerIntegration
get_system_overview() -> Dict[str, Any]
```

## Examples

See the `examples/` directory for complete plugin implementations:

- `momentum_strategy_plugin.py` - Advanced momentum strategy
- `bollinger_bands_plugin.py` - Bollinger Bands indicator
- `custom_rsi_plugin.py` - Custom RSI implementation
- `mean_reversion_plugin.py` - Mean reversion strategy

## Support

For questions and support:

- Check the troubleshooting section
- Review example plugins
- Check system logs
- Submit issues on GitHub
- Join the community Discord

---

*This guide covers the essential aspects of the Trading Bot Plugin System. For the latest updates and advanced features, refer to the official documentation and source code.*