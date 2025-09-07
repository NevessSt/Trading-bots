from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from ...strategy_plugin_system import IndicatorPlugin

class BollingerBandsIndicator(IndicatorPlugin):
    """Bollinger Bands technical indicator"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        self.period = period
        self.std_dev = std_dev
        self.price_column = kwargs.get('price_column', 'close')
    
    def calculate(self, data: pd.DataFrame, **kwargs) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        if not self.validate_data(data):
            raise ValueError("Invalid data for Bollinger Bands indicator")
        
        price_series = data[self.price_column]
        
        # Calculate moving average (middle band)
        middle_band = price_series.rolling(window=self.period).mean()
        
        # Calculate standard deviation
        std = price_series.rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * self.std_dev)
        lower_band = middle_band - (std * self.std_dev)
        
        # Calculate additional metrics
        bandwidth = (upper_band - lower_band) / middle_band
        percent_b = (price_series - lower_band) / (upper_band - lower_band)
        
        # Squeeze detection (low volatility)
        squeeze = bandwidth < bandwidth.rolling(window=50).quantile(0.1)
        
        return {
            'bb_upper': upper_band,
            'bb_middle': middle_band,
            'bb_lower': lower_band,
            'bb_bandwidth': bandwidth,
            'bb_percent_b': percent_b,
            'bb_squeeze': squeeze.astype(int)
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'id': 'bollinger_bands',
            'name': 'Bollinger Bands',
            'version': '1.0.0',
            'author': 'Trading Bot System',
            'description': 'Bollinger Bands with bandwidth and %B calculations',
            'type': 'indicator',
            'category': 'volatility',
            'created_at': datetime.now().isoformat(),
            'tags': ['volatility', 'bands', 'mean_reversion'],
            'parameters': {
                'period': {
                    'type': 'int',
                    'default': 20,
                    'min': 5,
                    'max': 100,
                    'description': 'Moving average period'
                },
                'std_dev': {
                    'type': 'float',
                    'default': 2.0,
                    'min': 0.5,
                    'max': 4.0,
                    'description': 'Standard deviation multiplier'
                },
                'price_column': {
                    'type': 'string',
                    'default': 'close',
                    'options': ['open', 'high', 'low', 'close'],
                    'description': 'Price column to use for calculation'
                }
            },
            'outputs': {
                'bb_upper': 'Upper Bollinger Band',
                'bb_middle': 'Middle Bollinger Band (SMA)',
                'bb_lower': 'Lower Bollinger Band',
                'bb_bandwidth': 'Bollinger Band Width',
                'bb_percent_b': 'Percent B (%B)',
                'bb_squeeze': 'Squeeze Signal (1=squeeze, 0=normal)'
            },
            'usage_examples': [
                {
                    'description': 'Standard Bollinger Bands',
                    'parameters': {'period': 20, 'std_dev': 2.0}
                },
                {
                    'description': 'Tight Bollinger Bands for scalping',
                    'parameters': {'period': 10, 'std_dev': 1.5}
                },
                {
                    'description': 'Wide Bollinger Bands for swing trading',
                    'parameters': {'period': 50, 'std_dev': 2.5}
                }
            ]
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'period': self.period,
            'std_dev': self.std_dev,
            'price_column': self.price_column
        }
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        required_columns = [self.price_column]
        return (
            all(col in data.columns for col in required_columns) and 
            len(data) >= self.period and
            not data[self.price_column].isna().all()
        )
    
    def get_trading_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on Bollinger Bands"""
        bb_data = self.calculate(data)
        
        signals_df = data.copy()
        
        # Add Bollinger Bands data
        for key, series in bb_data.items():
            signals_df[key] = series
        
        # Generate signals
        signals_df['bb_signal'] = 0
        signals_df['bb_signal_strength'] = 0.0
        
        # Buy signals: Price touches lower band and %B is low
        buy_condition = (
            (signals_df[self.price_column] <= signals_df['bb_lower'] * 1.01) &
            (signals_df['bb_percent_b'] < 0.2) &
            (signals_df['bb_squeeze'] == 0)  # Not in squeeze
        )
        
        # Sell signals: Price touches upper band and %B is high
        sell_condition = (
            (signals_df[self.price_column] >= signals_df['bb_upper'] * 0.99) &
            (signals_df['bb_percent_b'] > 0.8) &
            (signals_df['bb_squeeze'] == 0)  # Not in squeeze
        )
        
        # Apply signals
        signals_df.loc[buy_condition, 'bb_signal'] = 1
        signals_df.loc[sell_condition, 'bb_signal'] = -1
        
        # Calculate signal strength based on %B position
        signals_df['bb_signal_strength'] = np.where(
            signals_df['bb_signal'] == 1,
            1 - signals_df['bb_percent_b'],  # Stronger when closer to lower band
            np.where(
                signals_df['bb_signal'] == -1,
                signals_df['bb_percent_b'],  # Stronger when closer to upper band
                0.5
            )
        )
        
        return signals_df
    
    def get_support_resistance_levels(self, data: pd.DataFrame) -> Dict[str, float]:
        """Get current support and resistance levels"""
        bb_data = self.calculate(data)
        
        latest_upper = bb_data['bb_upper'].iloc[-1]
        latest_lower = bb_data['bb_lower'].iloc[-1]
        latest_middle = bb_data['bb_middle'].iloc[-1]
        
        return {
            'resistance': latest_upper,
            'support': latest_lower,
            'pivot': latest_middle,
            'bandwidth': bb_data['bb_bandwidth'].iloc[-1],
            'percent_b': bb_data['bb_percent_b'].iloc[-1]
        }

class BollingerBandsPlugin(BollingerBandsIndicator):
    """Plugin wrapper for Bollinger Bands indicator"""
    
    def __init__(self):
        super().__init__()
    
    def get_dependencies(self) -> list:
        return ['pandas', 'numpy']
    
    def validate_environment(self) -> bool:
        try:
            import pandas
            import numpy
            return True
        except ImportError:
            return False
    
    def on_load(self):
        """Called when plugin is loaded"""
        print(f"Loaded Bollinger Bands Indicator Plugin v{self.get_metadata()['version']}")
    
    def on_unload(self):
        """Called when plugin is unloaded"""
        print("Unloaded Bollinger Bands Indicator Plugin")

# Additional utility functions for the plugin
def detect_bollinger_squeeze(bb_bandwidth: pd.Series, lookback_period: int = 50) -> pd.Series:
    """Detect Bollinger Band squeeze periods"""
    rolling_min = bb_bandwidth.rolling(window=lookback_period).min()
    squeeze_threshold = rolling_min * 1.1  # 10% above minimum
    return bb_bandwidth < squeeze_threshold

def calculate_bollinger_momentum(price: pd.Series, bb_upper: pd.Series, bb_lower: pd.Series) -> pd.Series:
    """Calculate momentum based on Bollinger Band position"""
    bb_position = (price - bb_lower) / (bb_upper - bb_lower)
    momentum = bb_position.diff()
    return momentum

def find_bollinger_reversals(data: pd.DataFrame, bb_data: Dict[str, pd.Series]) -> pd.DataFrame:
    """Find potential reversal points using Bollinger Bands"""
    result = data.copy()
    
    # Add Bollinger Bands data
    for key, series in bb_data.items():
        result[key] = series
    
    # Find reversals at bands
    result['bb_reversal'] = 0
    
    # Bullish reversal: Price below lower band then moves back inside
    bullish_reversal = (
        (result['close'].shift(1) < result['bb_lower'].shift(1)) &
        (result['close'] > result['bb_lower'])
    )
    
    # Bearish reversal: Price above upper band then moves back inside
    bearish_reversal = (
        (result['close'].shift(1) > result['bb_upper'].shift(1)) &
        (result['close'] < result['bb_upper'])
    )
    
    result.loc[bullish_reversal, 'bb_reversal'] = 1
    result.loc[bearish_reversal, 'bb_reversal'] = -1
    
    return result