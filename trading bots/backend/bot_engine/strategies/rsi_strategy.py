import pandas as pd
import numpy as np
from bot_engine.strategies.base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """Relative Strength Index (RSI) trading strategy"""
    
    def __init__(self, rsi_period=14, overbought=70, oversold=30):
        """Initialize the RSI strategy
        
        Args:
            rsi_period (int): RSI period
            overbought (int): Overbought threshold
            oversold (int): Oversold threshold
        """
        super().__init__()
        self.name = 'RSI Strategy'
        self.description = 'Generates buy signals when RSI crosses below oversold threshold and sell signals when RSI crosses above overbought threshold'
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
    
    def generate_signals(self, df):
        """Generate trading signals based on RSI
        
        Args:
            df (pandas.DataFrame): OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with signals
        """
        # Make a copy of the dataframe
        df = df.copy()
        
        # Calculate RSI
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        
        # Initialize signal column
        df['signal'] = 0
        
        # Generate buy signals (1) when RSI crosses below oversold threshold
        df.loc[(df['rsi'] < self.oversold) & (df['rsi'].shift(1) >= self.oversold), 'signal'] = 1
        
        # Generate sell signals (-1) when RSI crosses above overbought threshold
        df.loc[(df['rsi'] > self.overbought) & (df['rsi'].shift(1) <= self.overbought), 'signal'] = -1
        
        return df
    
    def _calculate_rsi(self, prices, period):
        """Calculate Relative Strength Index (RSI)
        
        Args:
            prices (pandas.Series): Price data
            period (int): RSI period
            
        Returns:
            pandas.Series: RSI values
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS
        rs = avg_gain / avg_loss
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def get_parameters(self):
        """Get strategy parameters
        
        Returns:
            dict: Strategy parameters
        """
        return {
            'rsi_period': self.rsi_period,
            'overbought': self.overbought,
            'oversold': self.oversold
        }
    
    def set_parameters(self, parameters):
        """Set strategy parameters
        
        Args:
            parameters (dict): Strategy parameters
        """
        if 'rsi_period' in parameters:
            self.rsi_period = parameters['rsi_period']
        if 'overbought' in parameters:
            self.overbought = parameters['overbought']
        if 'oversold' in parameters:
            self.oversold = parameters['oversold']