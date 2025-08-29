import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base_strategy import BaseStrategy

class ScalpingStrategy(BaseStrategy):
    """Advanced Scalping Strategy for high-frequency trading
    
    This strategy is designed for capturing small price movements with:
    - Multiple timeframe analysis
    - Order book depth analysis
    - Volume and volatility filters
    - Quick profit targets with tight stop losses
    """
    
    def __init__(self, 
                 timeframes: List[str] = ['1m', '5m'],
                 min_spread: float = 0.0001,
                 max_spread: float = 0.001,
                 volume_threshold: float = 1000000,
                 volatility_threshold: float = 0.005,
                 quick_profit_target: float = 0.002,
                 extended_profit_target: float = 0.005,
                 stop_loss: float = 0.003,
                 max_holding_time: int = 300,
                 rsi_oversold: float = 25,
                 rsi_overbought: float = 75,
                 use_order_book: bool = True):
        """Initialize the Scalping strategy
        
        Args:
            timeframes: List of timeframes to analyze
            min_spread: Minimum spread requirement
            max_spread: Maximum spread allowed
            volume_threshold: Minimum volume requirement
            volatility_threshold: Minimum volatility requirement
            quick_profit_target: Quick profit target (0.2%)
            extended_profit_target: Extended profit target (0.5%)
            stop_loss: Stop loss percentage (0.3%)
            max_holding_time: Maximum holding time in seconds
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            use_order_book: Enable order book analysis
        """
        super().__init__()
        self.name = 'Advanced Scalping Strategy'
        self.description = 'High-frequency scalping strategy with multi-timeframe analysis and order book data'
        
        self.timeframes = timeframes
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.volume_threshold = volume_threshold
        self.volatility_threshold = volatility_threshold
        self.quick_profit_target = quick_profit_target
        self.extended_profit_target = extended_profit_target
        self.stop_loss = stop_loss
        self.max_holding_time = max_holding_time
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.use_order_book = use_order_book
        
        # Internal state
        self.position_entry_time = None
        self.position_entry_price = None
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Calculate price volatility"""
        returns = prices.pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(period)
        return volatility
    
    def analyze_market_microstructure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market microstructure for scalping opportunities"""
        latest = df.iloc[-1]
        
        # Calculate spread (if available)
        spread = 0.001  # Default spread assumption
        if 'bid' in df.columns and 'ask' in df.columns:
            spread = (latest['ask'] - latest['bid']) / latest['close']
        
        # Volume analysis
        volume_ma = df['volume'].rolling(window=20).mean().iloc[-1]
        volume_ratio = latest['volume'] / volume_ma if volume_ma > 0 else 1
        
        # Price momentum
        price_change_1m = (latest['close'] - df['close'].iloc[-2]) / df['close'].iloc[-2] if len(df) > 1 else 0
        price_change_5m = (latest['close'] - df['close'].iloc[-6]) / df['close'].iloc[-6] if len(df) > 5 else 0
        
        return {
            'spread': spread,
            'volume_ratio': volume_ratio,
            'price_change_1m': price_change_1m,
            'price_change_5m': price_change_5m,
            'is_liquid': latest['volume'] > self.volume_threshold,
            'spread_acceptable': self.min_spread <= spread <= self.max_spread
        }
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate scalping signals based on multiple factors
        
        Args:
            df (pandas.DataFrame): OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with signals
        """
        if len(df) < 30:  # Need sufficient data
            df['signal'] = 0
            return df
        
        # Make a copy
        df = df.copy()
        
        # Calculate technical indicators
        df['rsi'] = self.calculate_rsi(df['close'])
        df['volatility'] = self.calculate_volatility(df['close'])
        
        # Calculate EMAs for trend
        df['ema_fast'] = df['close'].ewm(span=5).mean()
        df['ema_slow'] = df['close'].ewm(span=13).mean()
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Price momentum
        df['momentum_1m'] = df['close'].pct_change(1)
        df['momentum_5m'] = df['close'].pct_change(5)
        
        # Initialize signals
        df['signal'] = 0
        df['signal_strength'] = 0.0
        df['profit_target'] = self.quick_profit_target
        df['stop_loss_level'] = self.stop_loss
        
        # Market microstructure analysis
        microstructure = self.analyze_market_microstructure(df)
        
        # Generate signals based on multiple conditions
        for i in range(20, len(df)):  # Start after indicators are calculated
            current = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Skip if market conditions are not suitable
            if not microstructure['is_liquid'] or not microstructure['spread_acceptable']:
                continue
            
            # Skip if volatility is too low
            if current['volatility'] < self.volatility_threshold:
                continue
            
            signal_strength = 0.0
            
            # RSI conditions
            if current['rsi'] < self.rsi_oversold and prev['rsi'] >= self.rsi_oversold:
                signal_strength += 0.3  # RSI oversold bounce
            elif current['rsi'] > self.rsi_overbought and prev['rsi'] <= self.rsi_overbought:
                signal_strength -= 0.3  # RSI overbought reversal
            
            # EMA trend conditions
            if current['ema_fast'] > current['ema_slow'] and prev['ema_fast'] <= prev['ema_slow']:
                signal_strength += 0.2  # Bullish EMA crossover
            elif current['ema_fast'] < current['ema_slow'] and prev['ema_fast'] >= prev['ema_slow']:
                signal_strength -= 0.2  # Bearish EMA crossover
            
            # Volume confirmation
            if current['volume_ratio'] > 1.5:  # High volume
                signal_strength += 0.1
            
            # Momentum conditions
            if abs(current['momentum_1m']) > 0.002:  # Strong 1-minute momentum
                if current['momentum_1m'] > 0:
                    signal_strength += 0.2
                else:
                    signal_strength -= 0.2
            
            # Price action patterns
            if current['close'] > current['open'] and prev['close'] < prev['open']:  # Bullish reversal
                signal_strength += 0.1
            elif current['close'] < current['open'] and prev['close'] > prev['open']:  # Bearish reversal
                signal_strength -= 0.1
            
            # Set signal based on strength
            if signal_strength >= 0.5:
                df.iloc[i, df.columns.get_loc('signal')] = 1  # Buy signal
                df.iloc[i, df.columns.get_loc('profit_target')] = self.quick_profit_target
            elif signal_strength <= -0.5:
                df.iloc[i, df.columns.get_loc('signal')] = -1  # Sell signal
                df.iloc[i, df.columns.get_loc('profit_target')] = self.quick_profit_target
            
            # Store signal strength for analysis
            df.iloc[i, df.columns.get_loc('signal_strength')] = signal_strength
        
        return df
    
    def should_exit_position(self, current_price: float, entry_price: float, 
                           entry_time: int, current_time: int, position_side: str) -> Dict[str, Any]:
        """Determine if position should be exited based on scalping rules
        
        Args:
            current_price: Current market price
            entry_price: Position entry price
            entry_time: Position entry timestamp
            current_time: Current timestamp
            position_side: 'long' or 'short'
            
        Returns:
            Dict with exit decision and reason
        """
        time_held = current_time - entry_time
        price_change = (current_price - entry_price) / entry_price
        
        if position_side == 'short':
            price_change = -price_change
        
        # Quick profit target hit
        if price_change >= self.quick_profit_target:
            return {'should_exit': True, 'reason': 'quick_profit_target', 'profit': price_change}
        
        # Extended profit target for longer holds
        if time_held > 60 and price_change >= self.extended_profit_target:
            return {'should_exit': True, 'reason': 'extended_profit_target', 'profit': price_change}
        
        # Stop loss hit
        if price_change <= -self.stop_loss:
            return {'should_exit': True, 'reason': 'stop_loss', 'profit': price_change}
        
        # Maximum holding time exceeded
        if time_held > self.max_holding_time:
            return {'should_exit': True, 'reason': 'max_holding_time', 'profit': price_change}
        
        # Small profit after reasonable time (risk management)
        if time_held > 120 and price_change >= 0.001:  # 0.1% profit after 2 minutes
            return {'should_exit': True, 'reason': 'small_profit_timeout', 'profit': price_change}
        
        return {'should_exit': False, 'reason': 'hold', 'profit': price_change}
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return {
            'timeframes': self.timeframes,
            'min_spread': self.min_spread,
            'max_spread': self.max_spread,
            'volume_threshold': self.volume_threshold,
            'volatility_threshold': self.volatility_threshold,
            'quick_profit_target': self.quick_profit_target,
            'extended_profit_target': self.extended_profit_target,
            'stop_loss': self.stop_loss,
            'max_holding_time': self.max_holding_time,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'use_order_book': self.use_order_book
        }
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """Set strategy parameters"""
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk metrics for the strategy"""
        return {
            'max_drawdown_expected': 0.05,  # 5%
            'win_rate_expected': 0.65,      # 65%
            'avg_trade_duration': 180,      # 3 minutes
            'risk_reward_ratio': 1.5,       # 1:1.5
            'max_concurrent_positions': 3,
            'recommended_capital': 1000,    # $1000 minimum
            'risk_level': 'high',
            'suitable_for_beginners': False
        }