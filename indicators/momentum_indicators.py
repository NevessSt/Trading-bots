"""Momentum Indicators Module

This module implements popular momentum-based technical indicators:
- RSI (Relative Strength Index)
- Stochastic Oscillator
- Williams %R
- CCI (Commodity Channel Index)
- ROC (Rate of Change)
- MFI (Money Flow Index)
- Ultimate Oscillator
- Awesome Oscillator

All indicators follow the BaseIndicator interface for consistency.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Optional
from dataclasses import dataclass

from .indicator_base import (
    BaseIndicator, 
    IndicatorResult, 
    IndicatorConfig, 
    SignalType, 
    TrendDirection,
    calculate_sma,
    calculate_ema
)

class RSI(BaseIndicator):
    """Relative Strength Index (RSI) Indicator
    
    RSI is a momentum oscillator that measures the speed and change of price movements.
    It oscillates between 0 and 100, with readings above 70 typically considered overbought
    and readings below 30 considered oversold.
    """
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        config.custom_params.update({
            'overbought': overbought,
            'oversold': oversold
        })
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate RSI"""
        if isinstance(data, pd.DataFrame):
            prices = data[self.config.source].values
        else:
            prices = data
        
        period = self.config.period
        overbought = self.config.custom_params['overbought']
        oversold = self.config.custom_params['oversold']
        
        # Calculate price changes
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gains = np.full_like(prices, np.nan)
        avg_losses = np.full_like(prices, np.nan)
        
        if len(gains) >= period:
            # Initial averages
            avg_gains[period] = np.mean(gains[:period])
            avg_losses[period] = np.mean(losses[:period])
            
            # Smoothed averages (Wilder's smoothing)
            for i in range(period + 1, len(prices)):
                avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
                avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
        
        # Calculate RSI
        rsi_values = np.full_like(prices, np.nan)
        for i in range(period, len(prices)):
            if avg_losses[i] == 0:
                rsi_values[i] = 100
            else:
                rs = avg_gains[i] / avg_losses[i]
                rsi_values[i] = 100 - (100 / (1 + rs))
        
        # Generate signals
        signals = self._generate_rsi_signals(rsi_values, overbought, oversold)
        
        # Determine trend
        trend = self._determine_rsi_trend(rsi_values)
        
        return IndicatorResult(
            values=rsi_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_rsi_strength(rsi_values, overbought, oversold),
            confidence=self._calculate_rsi_confidence(rsi_values, overbought, oversold)
        )
    
    def _generate_rsi_signals(self, rsi_values: np.ndarray, overbought: float, 
                             oversold: float) -> List[SignalType]:
        """Generate RSI trading signals"""
        signals = [SignalType.NEUTRAL] * len(rsi_values)
        
        for i in range(1, len(rsi_values)):
            if np.isnan(rsi_values[i]) or np.isnan(rsi_values[i-1]):
                continue
            
            current_rsi = rsi_values[i]
            prev_rsi = rsi_values[i-1]
            
            # Oversold to normal (buy signal)
            if prev_rsi <= oversold and current_rsi > oversold:
                signals[i] = SignalType.BUY
            # Overbought to normal (sell signal)
            elif prev_rsi >= overbought and current_rsi < overbought:
                signals[i] = SignalType.SELL
            # Strong oversold (strong buy)
            elif current_rsi <= 20:
                signals[i] = SignalType.STRONG_BUY
            # Strong overbought (strong sell)
            elif current_rsi >= 80:
                signals[i] = SignalType.STRONG_SELL
            # Normal ranges
            elif current_rsi < oversold:
                signals[i] = SignalType.BUY
            elif current_rsi > overbought:
                signals[i] = SignalType.SELL
            # Neutral zone with momentum
            elif oversold < current_rsi < 50:
                signals[i] = SignalType.BUY if current_rsi > prev_rsi else SignalType.HOLD
            elif 50 < current_rsi < overbought:
                signals[i] = SignalType.SELL if current_rsi < prev_rsi else SignalType.HOLD
            else:
                signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_rsi_trend(self, rsi_values: np.ndarray) -> TrendDirection:
        """Determine trend based on RSI levels and direction"""
        if len(rsi_values) < 3:
            return TrendDirection.UNKNOWN
        
        recent_rsi = rsi_values[-min(5, len(rsi_values)):]
        valid_rsi = recent_rsi[~np.isnan(recent_rsi)]
        
        if len(valid_rsi) < 2:
            return TrendDirection.UNKNOWN
        
        current_rsi = valid_rsi[-1]
        avg_rsi = np.mean(valid_rsi)
        
        # Trend based on RSI level and recent direction
        if current_rsi > 60 and avg_rsi > 55:
            return TrendDirection.UPTREND
        elif current_rsi < 40 and avg_rsi < 45:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_rsi_strength(self, rsi_values: np.ndarray, overbought: float, 
                               oversold: float) -> float:
        """Calculate RSI strength based on extreme readings"""
        if len(rsi_values) < 3:
            return 0.0
        
        recent_rsi = rsi_values[-min(10, len(rsi_values)):]
        valid_rsi = recent_rsi[~np.isnan(recent_rsi)]
        
        if len(valid_rsi) == 0:
            return 0.0
        
        current_rsi = valid_rsi[-1]
        
        # Strength based on distance from neutral (50)
        distance_from_neutral = abs(current_rsi - 50) / 50
        
        # Bonus for extreme readings
        if current_rsi <= 20 or current_rsi >= 80:
            distance_from_neutral *= 1.5
        elif current_rsi <= oversold or current_rsi >= overbought:
            distance_from_neutral *= 1.2
        
        return min(distance_from_neutral, 1.0)
    
    def _calculate_rsi_confidence(self, rsi_values: np.ndarray, overbought: float, 
                                 oversold: float) -> float:
        """Calculate RSI confidence based on consistency"""
        if len(rsi_values) < 5:
            return 0.5
        
        recent_rsi = rsi_values[-5:]
        valid_rsi = recent_rsi[~np.isnan(recent_rsi)]
        
        if len(valid_rsi) < 3:
            return 0.5
        
        # Confidence based on consistency of readings
        current_rsi = valid_rsi[-1]
        
        if current_rsi <= oversold or current_rsi >= overbought:
            # High confidence in extreme zones
            return 0.9
        elif 30 < current_rsi < 70:
            # Lower confidence in neutral zone
            return 0.6
        else:
            return 0.75

class StochasticOscillator(BaseIndicator):
    """Stochastic Oscillator Indicator
    
    The Stochastic Oscillator compares a particular closing price to a range
    of prices over a certain period. It consists of %K and %D lines.
    """
    
    def __init__(self, k_period: int = 14, d_period: int = 3, smooth_k: int = 3, **kwargs):
        config = IndicatorConfig(period=k_period, **kwargs)
        config.custom_params.update({
            'k_period': k_period,
            'd_period': d_period,
            'smooth_k': smooth_k
        })
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Stochastic Oscillator"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Stochastic requires OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        k_period = self.config.custom_params['k_period']
        d_period = self.config.custom_params['d_period']
        smooth_k = self.config.custom_params['smooth_k']
        
        # Calculate %K
        k_values = np.full_like(close, np.nan)
        
        for i in range(k_period - 1, len(close)):
            period_high = np.max(high[i - k_period + 1:i + 1])
            period_low = np.min(low[i - k_period + 1:i + 1])
            
            if period_high != period_low:
                k_values[i] = 100 * (close[i] - period_low) / (period_high - period_low)
            else:
                k_values[i] = 50  # Neutral when no range
        
        # Smooth %K if required
        if smooth_k > 1:
            k_values = calculate_sma(k_values, smooth_k)
        
        # Calculate %D (SMA of %K)
        d_values = calculate_sma(k_values, d_period)
        
        # Generate signals
        signals = self._generate_stochastic_signals(k_values, d_values)
        
        # Determine trend
        trend = self._determine_stochastic_trend(k_values, d_values)
        
        return IndicatorResult(
            values=k_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_stochastic_strength(k_values, d_values),
            confidence=self._calculate_stochastic_confidence(k_values, d_values),
            metadata={'d_values': d_values}
        )
    
    def _generate_stochastic_signals(self, k_values: np.ndarray, 
                                   d_values: np.ndarray) -> List[SignalType]:
        """Generate Stochastic signals"""
        signals = [SignalType.NEUTRAL] * len(k_values)
        
        for i in range(1, len(k_values)):
            if (np.isnan(k_values[i]) or np.isnan(d_values[i]) or 
                np.isnan(k_values[i-1]) or np.isnan(d_values[i-1])):
                continue
            
            k_current = k_values[i]
            d_current = d_values[i]
            k_prev = k_values[i-1]
            d_prev = d_values[i-1]
            
            # %K crosses above %D in oversold area
            if (k_current > d_current and k_prev <= d_prev and 
                k_current < 30 and d_current < 30):
                signals[i] = SignalType.STRONG_BUY
            # %K crosses above %D
            elif k_current > d_current and k_prev <= d_prev:
                signals[i] = SignalType.BUY
            # %K crosses below %D in overbought area
            elif (k_current < d_current and k_prev >= d_prev and 
                  k_current > 70 and d_current > 70):
                signals[i] = SignalType.STRONG_SELL
            # %K crosses below %D
            elif k_current < d_current and k_prev >= d_prev:
                signals[i] = SignalType.SELL
            # Oversold area
            elif k_current < 20 and d_current < 20:
                signals[i] = SignalType.BUY
            # Overbought area
            elif k_current > 80 and d_current > 80:
                signals[i] = SignalType.SELL
            # Trend continuation
            elif k_current > d_current:
                signals[i] = SignalType.BUY
            else:
                signals[i] = SignalType.SELL
        
        return signals
    
    def _determine_stochastic_trend(self, k_values: np.ndarray, 
                                  d_values: np.ndarray) -> TrendDirection:
        """Determine trend based on Stochastic position"""
        if len(k_values) < 3:
            return TrendDirection.UNKNOWN
        
        k_current = k_values[-1]
        d_current = d_values[-1]
        
        if np.isnan(k_current) or np.isnan(d_current):
            return TrendDirection.UNKNOWN
        
        # Trend based on position and relationship
        if k_current > d_current and k_current > 50:
            return TrendDirection.UPTREND
        elif k_current < d_current and k_current < 50:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_stochastic_strength(self, k_values: np.ndarray, 
                                     d_values: np.ndarray) -> float:
        """Calculate Stochastic strength"""
        if len(k_values) < 3:
            return 0.0
        
        k_current = k_values[-1]
        d_current = d_values[-1]
        
        if np.isnan(k_current) or np.isnan(d_current):
            return 0.0
        
        # Strength based on distance from 50 and line separation
        distance_from_neutral = abs(k_current - 50) / 50
        line_separation = abs(k_current - d_current) / 100
        
        strength = (distance_from_neutral + line_separation) / 2
        return min(strength, 1.0)
    
    def _calculate_stochastic_confidence(self, k_values: np.ndarray, 
                                       d_values: np.ndarray) -> float:
        """Calculate Stochastic confidence"""
        if len(k_values) < 3:
            return 0.5
        
        k_current = k_values[-1]
        d_current = d_values[-1]
        
        if np.isnan(k_current) or np.isnan(d_current):
            return 0.5
        
        # Higher confidence in extreme zones
        if (k_current < 20 and d_current < 20) or (k_current > 80 and d_current > 80):
            return 0.9
        elif 20 < k_current < 80 and 20 < d_current < 80:
            return 0.6
        else:
            return 0.75

class WilliamsR(BaseIndicator):
    """Williams %R Indicator
    
    Williams %R is a momentum indicator that measures overbought and oversold levels.
    It's similar to the Stochastic Oscillator but is plotted upside-down.
    """
    
    def __init__(self, period: int = 14, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Williams %R"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Williams %R requires OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        period = self.config.period
        
        williams_r = np.full_like(close, np.nan)
        
        for i in range(period - 1, len(close)):
            period_high = np.max(high[i - period + 1:i + 1])
            period_low = np.min(low[i - period + 1:i + 1])
            
            if period_high != period_low:
                williams_r[i] = -100 * (period_high - close[i]) / (period_high - period_low)
            else:
                williams_r[i] = -50  # Neutral when no range
        
        # Generate signals
        signals = self._generate_williams_signals(williams_r)
        
        # Determine trend
        trend = self._determine_williams_trend(williams_r)
        
        return IndicatorResult(
            values=williams_r,
            signals=signals,
            trend=trend,
            strength=self._calculate_williams_strength(williams_r),
            confidence=self._calculate_williams_confidence(williams_r)
        )
    
    def _generate_williams_signals(self, williams_r: np.ndarray) -> List[SignalType]:
        """Generate Williams %R signals"""
        signals = [SignalType.NEUTRAL] * len(williams_r)
        
        for i in range(1, len(williams_r)):
            if np.isnan(williams_r[i]) or np.isnan(williams_r[i-1]):
                continue
            
            current = williams_r[i]
            prev = williams_r[i-1]
            
            # Oversold to normal (buy signal)
            if prev <= -80 and current > -80:
                signals[i] = SignalType.BUY
            # Overbought to normal (sell signal)
            elif prev >= -20 and current < -20:
                signals[i] = SignalType.SELL
            # Strong oversold
            elif current <= -90:
                signals[i] = SignalType.STRONG_BUY
            # Strong overbought
            elif current >= -10:
                signals[i] = SignalType.STRONG_SELL
            # Normal ranges
            elif current < -80:
                signals[i] = SignalType.BUY
            elif current > -20:
                signals[i] = SignalType.SELL
            # Momentum in neutral zone
            elif -80 < current < -50:
                signals[i] = SignalType.BUY if current > prev else SignalType.HOLD
            elif -50 < current < -20:
                signals[i] = SignalType.SELL if current < prev else SignalType.HOLD
            else:
                signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_williams_trend(self, williams_r: np.ndarray) -> TrendDirection:
        """Determine trend based on Williams %R levels"""
        if len(williams_r) < 3:
            return TrendDirection.UNKNOWN
        
        recent_values = williams_r[-min(5, len(williams_r)):]
        valid_values = recent_values[~np.isnan(recent_values)]
        
        if len(valid_values) < 2:
            return TrendDirection.UNKNOWN
        
        current = valid_values[-1]
        avg = np.mean(valid_values)
        
        if current > -40 and avg > -45:
            return TrendDirection.UPTREND
        elif current < -60 and avg < -55:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_williams_strength(self, williams_r: np.ndarray) -> float:
        """Calculate Williams %R strength"""
        if len(williams_r) < 3:
            return 0.0
        
        current = williams_r[-1]
        if np.isnan(current):
            return 0.0
        
        # Strength based on distance from neutral (-50)
        distance_from_neutral = abs(current + 50) / 50
        
        # Bonus for extreme readings
        if current <= -90 or current >= -10:
            distance_from_neutral *= 1.5
        elif current <= -80 or current >= -20:
            distance_from_neutral *= 1.2
        
        return min(distance_from_neutral, 1.0)
    
    def _calculate_williams_confidence(self, williams_r: np.ndarray) -> float:
        """Calculate Williams %R confidence"""
        if len(williams_r) < 3:
            return 0.5
        
        current = williams_r[-1]
        if np.isnan(current):
            return 0.5
        
        # Higher confidence in extreme zones
        if current <= -80 or current >= -20:
            return 0.9
        elif -80 < current < -20:
            return 0.6
        else:
            return 0.75

class CCI(BaseIndicator):
    """Commodity Channel Index (CCI) Indicator
    
    CCI measures the variation of a security's price from its statistical mean.
    High values show that prices are unusually high compared to average prices.
    """
    
    def __init__(self, period: int = 20, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate CCI"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("CCI requires OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        period = self.config.period
        
        # Calculate Typical Price
        typical_price = (high + low + close) / 3
        
        # Calculate CCI
        cci_values = np.full_like(close, np.nan)
        
        for i in range(period - 1, len(close)):
            tp_period = typical_price[i - period + 1:i + 1]
            sma_tp = np.mean(tp_period)
            
            # Calculate Mean Deviation
            mean_deviation = np.mean(np.abs(tp_period - sma_tp))
            
            if mean_deviation != 0:
                cci_values[i] = (typical_price[i] - sma_tp) / (0.015 * mean_deviation)
            else:
                cci_values[i] = 0
        
        # Generate signals
        signals = self._generate_cci_signals(cci_values)
        
        # Determine trend
        trend = self._determine_cci_trend(cci_values)
        
        return IndicatorResult(
            values=cci_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_cci_strength(cci_values),
            confidence=self._calculate_cci_confidence(cci_values)
        )
    
    def _generate_cci_signals(self, cci_values: np.ndarray) -> List[SignalType]:
        """Generate CCI signals"""
        signals = [SignalType.NEUTRAL] * len(cci_values)
        
        for i in range(1, len(cci_values)):
            if np.isnan(cci_values[i]) or np.isnan(cci_values[i-1]):
                continue
            
            current = cci_values[i]
            prev = cci_values[i-1]
            
            # CCI crosses above -100 (buy signal)
            if prev <= -100 and current > -100:
                signals[i] = SignalType.BUY
            # CCI crosses below 100 (sell signal)
            elif prev >= 100 and current < 100:
                signals[i] = SignalType.SELL
            # Strong oversold
            elif current <= -200:
                signals[i] = SignalType.STRONG_BUY
            # Strong overbought
            elif current >= 200:
                signals[i] = SignalType.STRONG_SELL
            # Normal ranges
            elif current < -100:
                signals[i] = SignalType.BUY
            elif current > 100:
                signals[i] = SignalType.SELL
            # Trend continuation
            elif current > 0:
                signals[i] = SignalType.BUY if current > prev else SignalType.HOLD
            else:
                signals[i] = SignalType.SELL if current < prev else SignalType.HOLD
        
        return signals
    
    def _determine_cci_trend(self, cci_values: np.ndarray) -> TrendDirection:
        """Determine trend based on CCI levels"""
        if len(cci_values) < 3:
            return TrendDirection.UNKNOWN
        
        recent_values = cci_values[-min(5, len(cci_values)):]
        valid_values = recent_values[~np.isnan(recent_values)]
        
        if len(valid_values) < 2:
            return TrendDirection.UNKNOWN
        
        current = valid_values[-1]
        avg = np.mean(valid_values)
        
        if current > 50 and avg > 25:
            return TrendDirection.UPTREND
        elif current < -50 and avg < -25:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_cci_strength(self, cci_values: np.ndarray) -> float:
        """Calculate CCI strength"""
        if len(cci_values) < 3:
            return 0.0
        
        current = cci_values[-1]
        if np.isnan(current):
            return 0.0
        
        # Strength based on absolute value (distance from zero)
        strength = min(abs(current) / 200, 1.0)
        
        # Bonus for extreme readings
        if abs(current) >= 200:
            strength = 1.0
        elif abs(current) >= 100:
            strength *= 1.2
        
        return min(strength, 1.0)
    
    def _calculate_cci_confidence(self, cci_values: np.ndarray) -> float:
        """Calculate CCI confidence"""
        if len(cci_values) < 3:
            return 0.5
        
        current = cci_values[-1]
        if np.isnan(current):
            return 0.5
        
        # Higher confidence for extreme readings
        if abs(current) >= 100:
            return 0.9
        elif abs(current) >= 50:
            return 0.75
        else:
            return 0.6

# Additional momentum indicators can be added here:
# - ROC (Rate of Change)
# - MFI (Money Flow Index)
# - Ultimate Oscillator
# - Awesome Oscillator
# - TRIX
# etc.