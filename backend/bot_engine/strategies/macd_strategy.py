import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    """Moving Average Convergence Divergence (MACD) trading strategy"""
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        """Initialize the MACD strategy
        
        Args:
            fast_period (int): Fast EMA period
            slow_period (int): Slow EMA period
            signal_period (int): Signal line period
        """
        super().__init__()
        self.name = 'MACD Strategy'
        self.description = 'Generates buy signals when MACD line crosses above signal line and sell signals when MACD line crosses below signal line'
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def generate_signals(self, df):
        """Generate trading signals based on MACD
        
        Args:
            df (pandas.DataFrame): OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with signals
        """
        # Make a copy of the dataframe
        df = df.copy()
        
        # Calculate MACD
        df['macd'], df['macd_signal'], df['macd_hist'] = self._calculate_macd(
            df['close'],
            self.fast_period,
            self.slow_period,
            self.signal_period
        )
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate buy signals (1) when MACD line crosses above signal line
        df.loc[(df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'signal'] = 1
        
        # Generate sell signals (-1) when MACD line crosses below signal line
        df.loc[(df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'signal'] = -1
        
        return df
    
    def _calculate_macd(self, prices, fast_period, slow_period, signal_period):
        """Calculate Moving Average Convergence Divergence (MACD)
        
        Args:
            prices (pandas.Series): Price data
            fast_period (int): Fast EMA period
            slow_period (int): Slow EMA period
            signal_period (int): Signal line period
            
        Returns:
            tuple: (MACD line, signal line, histogram)
        """
        # Calculate fast and slow EMAs
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def get_parameters(self):
        """Get strategy parameters
        
        Returns:
            dict: Strategy parameters
        """
        return {
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'signal_period': self.signal_period
        }
    
    def set_parameters(self, parameters):
        """Set strategy parameters
        
        Args:
            parameters (dict): Strategy parameters
        """
        if 'fast_period' in parameters:
            self.fast_period = parameters['fast_period']
        if 'slow_period' in parameters:
            self.slow_period = parameters['slow_period']
        if 'signal_period' in parameters:
            self.signal_period = parameters['signal_period']