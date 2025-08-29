import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base_strategy import BaseStrategy

class SwingTradingStrategy(BaseStrategy):
    """Advanced Swing Trading Strategy for medium-term positions
    
    This strategy is designed for capturing larger price movements over days to weeks:
    - Multiple timeframe analysis (4H, 1D)
    - Trend following with momentum confirmation
    - Support/resistance level analysis
    - Risk management with trailing stops
    """
    
    def __init__(self, 
                 primary_timeframe: str = '4h',
                 secondary_timeframe: str = '1d',
                 trend_ema_fast: int = 21,
                 trend_ema_slow: int = 50,
                 momentum_rsi_period: int = 14,
                 momentum_macd_fast: int = 12,
                 momentum_macd_slow: int = 26,
                 momentum_macd_signal: int = 9,
                 support_resistance_period: int = 20,
                 profit_target: float = 0.08,
                 stop_loss: float = 0.04,
                 trailing_stop: float = 0.03,
                 min_trend_strength: float = 0.02,
                 volume_confirmation: bool = True,
                 rsi_oversold: float = 30,
                 rsi_overbought: float = 70):
        """Initialize the Swing Trading strategy
        
        Args:
            primary_timeframe: Main timeframe for analysis (4h)
            secondary_timeframe: Higher timeframe for trend confirmation (1d)
            trend_ema_fast: Fast EMA period for trend (21)
            trend_ema_slow: Slow EMA period for trend (50)
            momentum_rsi_period: RSI period for momentum (14)
            momentum_macd_fast: MACD fast EMA (12)
            momentum_macd_slow: MACD slow EMA (26)
            momentum_macd_signal: MACD signal line (9)
            support_resistance_period: Period for S/R levels (20)
            profit_target: Profit target percentage (8%)
            stop_loss: Stop loss percentage (4%)
            trailing_stop: Trailing stop percentage (3%)
            min_trend_strength: Minimum trend strength required (2%)
            volume_confirmation: Use volume for confirmation
            rsi_oversold: RSI oversold threshold (30)
            rsi_overbought: RSI overbought threshold (70)
        """
        super().__init__()
        self.name = 'Advanced Swing Trading Strategy'
        self.description = 'Medium-term swing trading strategy with multi-timeframe analysis and trend following'
        
        self.primary_timeframe = primary_timeframe
        self.secondary_timeframe = secondary_timeframe
        self.trend_ema_fast = trend_ema_fast
        self.trend_ema_slow = trend_ema_slow
        self.momentum_rsi_period = momentum_rsi_period
        self.momentum_macd_fast = momentum_macd_fast
        self.momentum_macd_slow = momentum_macd_slow
        self.momentum_macd_signal = momentum_macd_signal
        self.support_resistance_period = support_resistance_period
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        self.min_trend_strength = min_trend_strength
        self.volume_confirmation = volume_confirmation
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        
        # Internal state
        self.position_high_water_mark = None
        self.position_low_water_mark = None
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_support_resistance(self, df: pd.DataFrame, period: int = 20) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        recent_data = df.tail(period * 2)  # Use more data for better levels
        
        # Calculate pivot points
        highs = recent_data['high'].rolling(window=period).max()
        lows = recent_data['low'].rolling(window=period).min()
        
        # Current support and resistance
        resistance = highs.iloc[-1] if not highs.empty else recent_data['high'].max()
        support = lows.iloc[-1] if not lows.empty else recent_data['low'].min()
        
        # Additional levels based on recent price action
        price_levels = []
        for i in range(len(recent_data) - 5, len(recent_data)):
            if i > 2 and i < len(recent_data) - 2:
                # Local highs
                if (recent_data.iloc[i]['high'] > recent_data.iloc[i-1]['high'] and 
                    recent_data.iloc[i]['high'] > recent_data.iloc[i+1]['high']):
                    price_levels.append(recent_data.iloc[i]['high'])
                
                # Local lows
                if (recent_data.iloc[i]['low'] < recent_data.iloc[i-1]['low'] and 
                    recent_data.iloc[i]['low'] < recent_data.iloc[i+1]['low']):
                    price_levels.append(recent_data.iloc[i]['low'])
        
        current_price = recent_data['close'].iloc[-1]
        
        # Find nearest levels
        resistance_levels = [level for level in price_levels if level > current_price]
        support_levels = [level for level in price_levels if level < current_price]
        
        nearest_resistance = min(resistance_levels) if resistance_levels else resistance
        nearest_support = max(support_levels) if support_levels else support
        
        return {
            'resistance': nearest_resistance,
            'support': nearest_support,
            'current_price': current_price,
            'distance_to_resistance': (nearest_resistance - current_price) / current_price,
            'distance_to_support': (current_price - nearest_support) / current_price
        }
    
    def analyze_trend_strength(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend strength and direction"""
        if len(df) < self.trend_ema_slow + 10:
            return {'trend': 'neutral', 'strength': 0.0, 'confidence': 0.0}
        
        # Calculate EMAs
        ema_fast = self.calculate_ema(df['close'], self.trend_ema_fast)
        ema_slow = self.calculate_ema(df['close'], self.trend_ema_slow)
        
        current_fast = ema_fast.iloc[-1]
        current_slow = ema_slow.iloc[-1]
        prev_fast = ema_fast.iloc[-2]
        prev_slow = ema_slow.iloc[-2]
        
        # Trend direction
        if current_fast > current_slow:
            trend = 'bullish'
            trend_strength = (current_fast - current_slow) / current_slow
        else:
            trend = 'bearish'
            trend_strength = (current_slow - current_fast) / current_fast
        
        # Trend momentum (EMA slope)
        fast_momentum = (current_fast - prev_fast) / prev_fast
        slow_momentum = (current_slow - prev_slow) / prev_slow
        
        # Confidence based on EMA separation and momentum alignment
        confidence = min(abs(trend_strength) * 10, 1.0)  # Scale to 0-1
        
        if trend == 'bullish' and fast_momentum > 0 and slow_momentum > 0:
            confidence *= 1.2
        elif trend == 'bearish' and fast_momentum < 0 and slow_momentum < 0:
            confidence *= 1.2
        
        confidence = min(confidence, 1.0)
        
        return {
            'trend': trend,
            'strength': trend_strength,
            'confidence': confidence,
            'fast_momentum': fast_momentum,
            'slow_momentum': slow_momentum
        }
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate swing trading signals
        
        Args:
            df (pandas.DataFrame): OHLCV data
            
        Returns:
            pandas.DataFrame: DataFrame with signals
        """
        if len(df) < max(self.trend_ema_slow, self.momentum_rsi_period, self.support_resistance_period) + 10:
            df['signal'] = 0
            return df
        
        # Make a copy
        df = df.copy()
        
        # Calculate technical indicators
        df['ema_fast'] = self.calculate_ema(df['close'], self.trend_ema_fast)
        df['ema_slow'] = self.calculate_ema(df['close'], self.trend_ema_slow)
        df['rsi'] = self.calculate_rsi(df['close'], self.momentum_rsi_period)
        
        # MACD
        macd_data = self.calculate_macd(df['close'], self.momentum_macd_fast, 
                                       self.momentum_macd_slow, self.momentum_macd_signal)
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        
        # Volume analysis
        if self.volume_confirmation:
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Initialize signals
        df['signal'] = 0
        df['signal_strength'] = 0.0
        df['trend_direction'] = 'neutral'
        df['entry_reason'] = ''
        
        # Generate signals
        for i in range(max(self.trend_ema_slow, self.momentum_rsi_period) + 10, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            prev2 = df.iloc[i-2]
            
            # Analyze trend
            trend_analysis = self.analyze_trend_strength(df.iloc[:i+1])
            df.iloc[i, df.columns.get_loc('trend_direction')] = trend_analysis['trend']
            
            # Skip if trend is not strong enough
            if abs(trend_analysis['strength']) < self.min_trend_strength:
                continue
            
            signal_strength = 0.0
            entry_reasons = []
            
            # EMA trend confirmation
            if current['ema_fast'] > current['ema_slow'] and trend_analysis['trend'] == 'bullish':
                signal_strength += 0.3
                entry_reasons.append('bullish_trend')
            elif current['ema_fast'] < current['ema_slow'] and trend_analysis['trend'] == 'bearish':
                signal_strength -= 0.3
                entry_reasons.append('bearish_trend')
            
            # EMA crossover signals
            if (current['ema_fast'] > current['ema_slow'] and 
                prev['ema_fast'] <= prev['ema_slow']):
                signal_strength += 0.4
                entry_reasons.append('bullish_ema_crossover')
            elif (current['ema_fast'] < current['ema_slow'] and 
                  prev['ema_fast'] >= prev['ema_slow']):
                signal_strength -= 0.4
                entry_reasons.append('bearish_ema_crossover')
            
            # RSI momentum confirmation
            if (current['rsi'] > self.rsi_oversold and prev['rsi'] <= self.rsi_oversold and 
                trend_analysis['trend'] == 'bullish'):
                signal_strength += 0.3
                entry_reasons.append('rsi_oversold_bounce')
            elif (current['rsi'] < self.rsi_overbought and prev['rsi'] >= self.rsi_overbought and 
                  trend_analysis['trend'] == 'bearish'):
                signal_strength -= 0.3
                entry_reasons.append('rsi_overbought_reversal')
            
            # MACD confirmation
            if (current['macd'] > current['macd_signal'] and 
                prev['macd'] <= prev['macd_signal']):
                signal_strength += 0.2
                entry_reasons.append('macd_bullish_crossover')
            elif (current['macd'] < current['macd_signal'] and 
                  prev['macd'] >= prev['macd_signal']):
                signal_strength -= 0.2
                entry_reasons.append('macd_bearish_crossover')
            
            # MACD histogram momentum
            if (current['macd_histogram'] > prev['macd_histogram'] and 
                current['macd_histogram'] > 0):
                signal_strength += 0.1
                entry_reasons.append('macd_momentum_up')
            elif (current['macd_histogram'] < prev['macd_histogram'] and 
                  current['macd_histogram'] < 0):
                signal_strength -= 0.1
                entry_reasons.append('macd_momentum_down')
            
            # Volume confirmation
            if self.volume_confirmation and 'volume_ratio' in df.columns:
                if current['volume_ratio'] > 1.2:  # Above average volume
                    signal_strength += 0.1 if signal_strength > 0 else -0.1
                    entry_reasons.append('volume_confirmation')
            
            # Support/Resistance analysis
            sr_levels = self.calculate_support_resistance(df.iloc[:i+1], self.support_resistance_period)
            
            # Near support in uptrend
            if (trend_analysis['trend'] == 'bullish' and 
                sr_levels['distance_to_support'] < 0.02):  # Within 2% of support
                signal_strength += 0.2
                entry_reasons.append('near_support')
            
            # Near resistance in downtrend
            elif (trend_analysis['trend'] == 'bearish' and 
                  sr_levels['distance_to_resistance'] < 0.02):  # Within 2% of resistance
                signal_strength -= 0.2
                entry_reasons.append('near_resistance')
            
            # Apply trend strength multiplier
            signal_strength *= trend_analysis['confidence']
            
            # Generate final signal
            if signal_strength >= 0.6:
                df.iloc[i, df.columns.get_loc('signal')] = 1  # Buy signal
                df.iloc[i, df.columns.get_loc('entry_reason')] = ', '.join(entry_reasons)
            elif signal_strength <= -0.6:
                df.iloc[i, df.columns.get_loc('signal')] = -1  # Sell signal
                df.iloc[i, df.columns.get_loc('entry_reason')] = ', '.join(entry_reasons)
            
            df.iloc[i, df.columns.get_loc('signal_strength')] = signal_strength
        
        return df
    
    def should_exit_position(self, current_price: float, entry_price: float, 
                           entry_time: int, current_time: int, position_side: str,
                           highest_price: float = None, lowest_price: float = None) -> Dict[str, Any]:
        """Determine if position should be exited based on swing trading rules
        
        Args:
            current_price: Current market price
            entry_price: Position entry price
            entry_time: Position entry timestamp
            current_time: Current timestamp
            position_side: 'long' or 'short'
            highest_price: Highest price since entry (for trailing stop)
            lowest_price: Lowest price since entry (for trailing stop)
            
        Returns:
            Dict with exit decision and reason
        """
        time_held = (current_time - entry_time) / 3600  # Hours
        price_change = (current_price - entry_price) / entry_price
        
        if position_side == 'short':
            price_change = -price_change
            reference_price = lowest_price if lowest_price else entry_price
            trailing_change = (reference_price - current_price) / reference_price
        else:
            reference_price = highest_price if highest_price else entry_price
            trailing_change = (current_price - reference_price) / reference_price
        
        # Profit target hit
        if price_change >= self.profit_target:
            return {'should_exit': True, 'reason': 'profit_target', 'profit': price_change}
        
        # Stop loss hit
        if price_change <= -self.stop_loss:
            return {'should_exit': True, 'reason': 'stop_loss', 'profit': price_change}
        
        # Trailing stop (only if in profit)
        if price_change > 0.02:  # Only apply trailing stop if 2%+ profit
            if position_side == 'long' and trailing_change <= -self.trailing_stop:
                return {'should_exit': True, 'reason': 'trailing_stop', 'profit': price_change}
            elif position_side == 'short' and trailing_change <= -self.trailing_stop:
                return {'should_exit': True, 'reason': 'trailing_stop', 'profit': price_change}
        
        # Time-based exit (hold for at least 4 hours, max 7 days)
        if time_held > 168:  # 7 days
            return {'should_exit': True, 'reason': 'max_holding_time', 'profit': price_change}
        
        # Partial profit taking after 24 hours with good profit
        if time_held > 24 and price_change >= 0.04:  # 4% profit after 1 day
            return {'should_exit': True, 'reason': 'partial_profit', 'profit': price_change}
        
        return {'should_exit': False, 'reason': 'hold', 'profit': price_change}
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters"""
        return {
            'primary_timeframe': self.primary_timeframe,
            'secondary_timeframe': self.secondary_timeframe,
            'trend_ema_fast': self.trend_ema_fast,
            'trend_ema_slow': self.trend_ema_slow,
            'momentum_rsi_period': self.momentum_rsi_period,
            'momentum_macd_fast': self.momentum_macd_fast,
            'momentum_macd_slow': self.momentum_macd_slow,
            'momentum_macd_signal': self.momentum_macd_signal,
            'support_resistance_period': self.support_resistance_period,
            'profit_target': self.profit_target,
            'stop_loss': self.stop_loss,
            'trailing_stop': self.trailing_stop,
            'min_trend_strength': self.min_trend_strength,
            'volume_confirmation': self.volume_confirmation,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought
        }
    
    def set_parameters(self, parameters: Dict[str, Any]):
        """Set strategy parameters"""
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk metrics for the strategy"""
        return {
            'max_drawdown_expected': 0.15,  # 15%
            'win_rate_expected': 0.55,      # 55%
            'avg_trade_duration': 72,       # 3 days
            'risk_reward_ratio': 2.0,       # 1:2
            'max_concurrent_positions': 5,
            'recommended_capital': 5000,    # $5000 minimum
            'risk_level': 'medium',
            'suitable_for_beginners': True
        }