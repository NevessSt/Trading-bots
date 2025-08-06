import pandas as pd
import numpy as np
from bot_engine.strategies.base_strategy import BaseStrategy

class EMACrossoverStrategy(BaseStrategy):
    """Exponential Moving Average (EMA) Crossover trading strategy"""
    
    def __init__(self, fast_period=9, slow_period=21):
        """Initialize the EMA Crossover strategy
        
        Args:
            fast_period (int): Fast EMA period
            slow_period (int): Slow EMA period
        """
        super().__init__()
        self.name = 'EMA Crossover Strategy'
        self.description = 'Generates buy signals when fast EMA crosses above slow EMA and sell signals when fast EMA crosses below slow EMA'
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, df):
        """Generate trading signals based on EMA crossover
        
        Args:
            df (pandas.DataFrame): OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with signals
        """
        # Make a copy of the dataframe
        df = df.copy()
        
        # Calculate EMAs
        df['ema_fast'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate buy signals (1) when fast EMA crosses above slow EMA
        df.loc[(df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)), 'signal'] = 1
        
        # Generate sell signals (-1) when fast EMA crosses below slow EMA
        df.loc[(df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)), 'signal'] = -1
        
        return df
    
    def get_parameters(self):
        """Get strategy parameters
        
        Returns:
            dict: Strategy parameters
        """
        return {
            'fast_period': self.fast_period,
            'slow_period': self.slow_period
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