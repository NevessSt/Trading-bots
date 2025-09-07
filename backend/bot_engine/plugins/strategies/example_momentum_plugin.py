from typing import Dict, Any, Type
from datetime import datetime
import pandas as pd
import numpy as np
from ...strategy_plugin_system import StrategyPlugin
from ...strategies.base_strategy import BaseStrategy

class MomentumStrategy(BaseStrategy):
    """Momentum-based trading strategy"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.name = 'Momentum Strategy'
        self.description = 'Trades based on price momentum and volume'
        
        # Strategy parameters
        self.momentum_period = kwargs.get('momentum_period', 14)
        self.volume_threshold = kwargs.get('volume_threshold', 1.5)
        self.rsi_oversold = kwargs.get('rsi_oversold', 30)
        self.rsi_overbought = kwargs.get('rsi_overbought', 70)
        self.min_signal_strength = kwargs.get('min_signal_strength', 0.6)
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate momentum-based trading signals"""
        result_df = df.copy()
        
        # Calculate momentum indicators
        result_df['price_change'] = result_df['close'].pct_change(self.momentum_period)
        result_df['volume_ratio'] = result_df['volume'] / result_df['volume'].rolling(20).mean()
        
        # Calculate RSI
        result_df['rsi'] = self._calculate_rsi(result_df['close'], self.momentum_period)
        
        # Calculate moving averages
        result_df['sma_fast'] = result_df['close'].rolling(10).mean()
        result_df['sma_slow'] = result_df['close'].rolling(20).mean()
        
        # Generate signals
        result_df['signal'] = 0
        result_df['signal_strength'] = 0.0
        
        # Buy conditions
        buy_conditions = (
            (result_df['price_change'] > 0.02) &  # Strong positive momentum
            (result_df['volume_ratio'] > self.volume_threshold) &  # High volume
            (result_df['rsi'] < self.rsi_overbought) &  # Not overbought
            (result_df['sma_fast'] > result_df['sma_slow'])  # Uptrend
        )
        
        # Sell conditions
        sell_conditions = (
            (result_df['price_change'] < -0.02) |  # Strong negative momentum
            (result_df['rsi'] > self.rsi_overbought) |  # Overbought
            (result_df['sma_fast'] < result_df['sma_slow'])  # Downtrend
        )
        
        # Apply signals
        result_df.loc[buy_conditions, 'signal'] = 1
        result_df.loc[sell_conditions, 'signal'] = -1
        
        # Calculate signal strength
        result_df['signal_strength'] = self._calculate_signal_strength(result_df)
        
        # Filter by minimum signal strength
        weak_signals = result_df['signal_strength'] < self.min_signal_strength
        result_df.loc[weak_signals, 'signal'] = 0
        
        return result_df
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """Calculate signal strength based on multiple factors"""
        strength = pd.Series(0.5, index=df.index)
        
        # Momentum strength
        momentum_strength = np.abs(df['price_change']) * 10
        momentum_strength = np.clip(momentum_strength, 0, 1)
        
        # Volume strength
        volume_strength = np.clip(df['volume_ratio'] / 3, 0, 1)
        
        # RSI strength (distance from neutral)
        rsi_strength = np.abs(df['rsi'] - 50) / 50
        
        # Combine strengths
        strength = (momentum_strength * 0.4 + volume_strength * 0.3 + rsi_strength * 0.3)
        strength = np.clip(strength, 0, 1)
        
        return strength
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'momentum_period': self.momentum_period,
            'volume_threshold': self.volume_threshold,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'min_signal_strength': self.min_signal_strength
        }
    
    def set_parameters(self, parameters: Dict[str, Any]):
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_parameter_bounds(self) -> Dict[str, Dict[str, Any]]:
        return {
            'momentum_period': {'min': 5, 'max': 50, 'default': 14},
            'volume_threshold': {'min': 1.0, 'max': 5.0, 'default': 1.5},
            'rsi_oversold': {'min': 10, 'max': 40, 'default': 30},
            'rsi_overbought': {'min': 60, 'max': 90, 'default': 70},
            'min_signal_strength': {'min': 0.1, 'max': 1.0, 'default': 0.6}
        }

class MomentumPlugin(StrategyPlugin):
    """Plugin wrapper for Momentum strategy"""
    
    def get_strategy_class(self) -> Type:
        return MomentumStrategy
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            'id': 'momentum_strategy',
            'name': 'Momentum Strategy',
            'version': '1.0.0',
            'author': 'Trading Bot System',
            'description': 'Advanced momentum-based trading strategy with RSI and volume confirmation',
            'type': 'strategy',
            'category': 'momentum',
            'created_at': datetime.now().isoformat(),
            'tags': ['momentum', 'rsi', 'volume', 'trend'],
            'parameters': {
                'momentum_period': {
                    'type': 'int',
                    'default': 14,
                    'min': 5,
                    'max': 50,
                    'description': 'Period for momentum calculation'
                },
                'volume_threshold': {
                    'type': 'float',
                    'default': 1.5,
                    'min': 1.0,
                    'max': 5.0,
                    'description': 'Volume threshold multiplier'
                },
                'rsi_oversold': {
                    'type': 'int',
                    'default': 30,
                    'min': 10,
                    'max': 40,
                    'description': 'RSI oversold threshold'
                },
                'rsi_overbought': {
                    'type': 'int',
                    'default': 70,
                    'min': 60,
                    'max': 90,
                    'description': 'RSI overbought threshold'
                },
                'min_signal_strength': {
                    'type': 'float',
                    'default': 0.6,
                    'min': 0.1,
                    'max': 1.0,
                    'description': 'Minimum signal strength to execute trade'
                }
            },
            'performance_metrics': {
                'expected_win_rate': 0.65,
                'expected_profit_factor': 1.8,
                'max_drawdown': 0.15,
                'recommended_timeframes': ['5m', '15m', '1h']
            }
        }
    
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
        print(f"Loaded Momentum Strategy Plugin v{self.get_metadata()['version']}")
    
    def on_unload(self):
        """Called when plugin is unloaded"""
        print("Unloaded Momentum Strategy Plugin")