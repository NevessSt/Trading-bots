"""Volatility Indicators Module

This module implements popular volatility-based technical indicators:
- Bollinger Bands
- ATR (Average True Range)
- Keltner Channels
- Donchian Channels
- Standard Deviation
- Volatility Index
- Price Channels
- Envelope Channels

All indicators follow the BaseIndicator interface for consistency.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Optional, Tuple
from dataclasses import dataclass

from .indicator_base import (
    BaseIndicator, 
    IndicatorResult, 
    IndicatorConfig, 
    SignalType, 
    TrendDirection,
    calculate_sma,
    calculate_ema,
    true_range
)

class BollingerBands(BaseIndicator):
    """Bollinger Bands Indicator
    
    Bollinger Bands consist of a middle band (SMA) and two outer bands
    that are standard deviations away from the middle band.
    They help identify overbought/oversold conditions and volatility.
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        config.custom_params['std_dev'] = std_dev
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Bollinger Bands"""
        if isinstance(data, pd.DataFrame):
            prices = data[self.config.source].values
        else:
            prices = data
        
        period = self.config.period
        std_dev = self.config.custom_params['std_dev']
        
        # Calculate middle band (SMA)
        middle_band = calculate_sma(prices, period)
        
        # Calculate standard deviation
        std_values = np.full_like(prices, np.nan)
        for i in range(period - 1, len(prices)):
            period_prices = prices[i - period + 1:i + 1]
            std_values[i] = np.std(period_prices, ddof=0)
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std_dev * std_values)
        lower_band = middle_band - (std_dev * std_values)
        
        # Calculate %B (position within bands)
        percent_b = np.full_like(prices, np.nan)
        band_width = upper_band - lower_band
        valid_width = band_width != 0
        percent_b[valid_width] = (prices[valid_width] - lower_band[valid_width]) / band_width[valid_width]
        
        # Generate signals
        signals = self._generate_bollinger_signals(prices, upper_band, lower_band, middle_band, percent_b)
        
        # Determine trend
        trend = self._determine_bollinger_trend(prices, middle_band, percent_b)
        
        return IndicatorResult(
            values=middle_band,
            signals=signals,
            trend=trend,
            strength=self._calculate_bollinger_strength(percent_b, band_width),
            confidence=self._calculate_bollinger_confidence(percent_b),
            metadata={
                'upper_band': upper_band,
                'lower_band': lower_band,
                'percent_b': percent_b,
                'band_width': band_width
            }
        )
    
    def _generate_bollinger_signals(self, prices: np.ndarray, upper_band: np.ndarray,
                                  lower_band: np.ndarray, middle_band: np.ndarray,
                                  percent_b: np.ndarray) -> List[SignalType]:
        """Generate Bollinger Bands signals"""
        signals = [SignalType.NEUTRAL] * len(prices)
        
        for i in range(1, len(prices)):
            if (np.isnan(upper_band[i]) or np.isnan(lower_band[i]) or 
                np.isnan(middle_band[i]) or np.isnan(percent_b[i])):
                continue
            
            current_price = prices[i]
            prev_price = prices[i-1]
            current_pb = percent_b[i]
            prev_pb = percent_b[i-1] if not np.isnan(percent_b[i-1]) else current_pb
            
            # Price touches or breaks lower band (oversold)
            if current_price <= lower_band[i] and prev_price > lower_band[i-1]:
                signals[i] = SignalType.STRONG_BUY
            # Price bounces off lower band
            elif (prev_price <= lower_band[i-1] and current_price > lower_band[i] and 
                  current_pb > prev_pb):
                signals[i] = SignalType.BUY
            
            # Price touches or breaks upper band (overbought)
            elif current_price >= upper_band[i] and prev_price < upper_band[i-1]:
                signals[i] = SignalType.STRONG_SELL
            # Price bounces off upper band
            elif (prev_price >= upper_band[i-1] and current_price < upper_band[i] and 
                  current_pb < prev_pb):
                signals[i] = SignalType.SELL
            
            # %B based signals
            elif current_pb <= 0.2:  # Near lower band
                signals[i] = SignalType.BUY
            elif current_pb >= 0.8:  # Near upper band
                signals[i] = SignalType.SELL
            
            # Middle band crossover
            elif (current_price > middle_band[i] and prev_price <= middle_band[i-1]):
                signals[i] = SignalType.BUY
            elif (current_price < middle_band[i] and prev_price >= middle_band[i-1]):
                signals[i] = SignalType.SELL
            
            # Trend continuation
            elif current_price > middle_band[i]:
                signals[i] = SignalType.BUY if current_pb > 0.5 else SignalType.HOLD
            else:
                signals[i] = SignalType.SELL if current_pb < 0.5 else SignalType.HOLD
        
        return signals
    
    def _determine_bollinger_trend(self, prices: np.ndarray, middle_band: np.ndarray,
                                 percent_b: np.ndarray) -> TrendDirection:
        """Determine trend based on Bollinger Bands position"""
        if len(prices) < 3:
            return TrendDirection.UNKNOWN
        
        current_price = prices[-1]
        current_middle = middle_band[-1]
        current_pb = percent_b[-1]
        
        if np.isnan(current_middle) or np.isnan(current_pb):
            return TrendDirection.UNKNOWN
        
        # Trend based on position relative to middle band and %B
        if current_price > current_middle and current_pb > 0.6:
            return TrendDirection.UPTREND
        elif current_price < current_middle and current_pb < 0.4:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_bollinger_strength(self, percent_b: np.ndarray, 
                                    band_width: np.ndarray) -> float:
        """Calculate Bollinger Bands strength"""
        if len(percent_b) < 3:
            return 0.0
        
        current_pb = percent_b[-1]
        current_width = band_width[-1]
        
        if np.isnan(current_pb) or np.isnan(current_width):
            return 0.0
        
        # Strength based on %B position and band width
        pb_strength = abs(current_pb - 0.5) * 2  # Distance from center
        
        # Normalize band width (higher width = higher volatility = higher strength)
        recent_widths = band_width[-min(20, len(band_width)):]
        valid_widths = recent_widths[~np.isnan(recent_widths)]
        
        if len(valid_widths) > 1:
            avg_width = np.mean(valid_widths)
            width_strength = min(current_width / avg_width, 2.0) / 2.0
        else:
            width_strength = 0.5
        
        combined_strength = (pb_strength + width_strength) / 2
        return min(combined_strength, 1.0)
    
    def _calculate_bollinger_confidence(self, percent_b: np.ndarray) -> float:
        """Calculate Bollinger Bands confidence"""
        if len(percent_b) < 3:
            return 0.5
        
        current_pb = percent_b[-1]
        if np.isnan(current_pb):
            return 0.5
        
        # Higher confidence at extremes
        if current_pb <= 0.1 or current_pb >= 0.9:
            return 0.95
        elif current_pb <= 0.2 or current_pb >= 0.8:
            return 0.85
        elif current_pb <= 0.3 or current_pb >= 0.7:
            return 0.75
        else:
            return 0.6

class ATR(BaseIndicator):
    """Average True Range (ATR) Indicator
    
    ATR measures market volatility by calculating the average of true ranges
    over a specified period. Higher ATR indicates higher volatility.
    """
    
    def __init__(self, period: int = 14, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate ATR"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("ATR requires OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        period = self.config.period
        
        # Calculate True Range
        tr = true_range(high, low, close)
        
        # Calculate ATR using Wilder's smoothing
        atr_values = np.full_like(close, np.nan)
        
        if len(tr) >= period:
            # Initial ATR (simple average)
            atr_values[period - 1] = np.mean(tr[:period])
            
            # Subsequent ATR values (Wilder's smoothing)
            for i in range(period, len(close)):
                atr_values[i] = (atr_values[i-1] * (period - 1) + tr[i]) / period
        
        # Generate signals (ATR is primarily used for volatility, not direct signals)
        signals = self._generate_atr_signals(atr_values, close)
        
        # Determine trend (based on volatility patterns)
        trend = self._determine_atr_trend(atr_values)
        
        return IndicatorResult(
            values=atr_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_atr_strength(atr_values),
            confidence=0.7,  # ATR is more about volatility than directional signals
            metadata={'true_range': tr}
        )
    
    def _generate_atr_signals(self, atr_values: np.ndarray, close: np.ndarray) -> List[SignalType]:
        """Generate ATR-based signals (volatility breakout)"""
        signals = [SignalType.NEUTRAL] * len(atr_values)
        
        for i in range(1, len(atr_values)):
            if np.isnan(atr_values[i]) or np.isnan(atr_values[i-1]):
                continue
            
            current_atr = atr_values[i]
            prev_atr = atr_values[i-1]
            
            # Calculate recent ATR average for comparison
            recent_atr = atr_values[max(0, i-10):i+1]
            valid_atr = recent_atr[~np.isnan(recent_atr)]
            
            if len(valid_atr) < 3:
                continue
            
            avg_atr = np.mean(valid_atr)
            
            # Volatility expansion (potential breakout)
            if current_atr > avg_atr * 1.5:
                # Use price direction to determine signal
                if len(close) > i and i > 0:
                    if close[i] > close[i-1]:
                        signals[i] = SignalType.BUY
                    else:
                        signals[i] = SignalType.SELL
            
            # Volatility contraction (potential consolidation end)
            elif current_atr < avg_atr * 0.7:
                signals[i] = SignalType.HOLD  # Wait for breakout
            
            else:
                signals[i] = SignalType.NEUTRAL
        
        return signals
    
    def _determine_atr_trend(self, atr_values: np.ndarray) -> TrendDirection:
        """Determine volatility trend"""
        if len(atr_values) < 5:
            return TrendDirection.UNKNOWN
        
        recent_atr = atr_values[-5:]
        valid_atr = recent_atr[~np.isnan(recent_atr)]
        
        if len(valid_atr) < 3:
            return TrendDirection.UNKNOWN
        
        # Trend based on volatility direction
        if valid_atr[-1] > valid_atr[0]:
            return TrendDirection.UPTREND  # Increasing volatility
        elif valid_atr[-1] < valid_atr[0]:
            return TrendDirection.DOWNTREND  # Decreasing volatility
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_atr_strength(self, atr_values: np.ndarray) -> float:
        """Calculate ATR strength based on current vs historical volatility"""
        if len(atr_values) < 10:
            return 0.0
        
        current_atr = atr_values[-1]
        if np.isnan(current_atr):
            return 0.0
        
        # Compare current ATR to recent average
        recent_atr = atr_values[-20:] if len(atr_values) >= 20 else atr_values
        valid_atr = recent_atr[~np.isnan(recent_atr)]
        
        if len(valid_atr) < 2:
            return 0.0
        
        avg_atr = np.mean(valid_atr)
        if avg_atr == 0:
            return 0.0
        
        # Strength based on relative volatility
        relative_volatility = current_atr / avg_atr
        strength = min(relative_volatility, 2.0) / 2.0
        
        return min(strength, 1.0)

class KeltnerChannels(BaseIndicator):
    """Keltner Channels Indicator
    
    Keltner Channels use ATR to set channel distance from an EMA centerline.
    They help identify trend direction and potential breakouts.
    """
    
    def __init__(self, period: int = 20, atr_period: int = 10, multiplier: float = 2.0, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        config.custom_params.update({
            'atr_period': atr_period,
            'multiplier': multiplier
        })
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Keltner Channels"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Keltner Channels require OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        period = self.config.period
        atr_period = self.config.custom_params['atr_period']
        multiplier = self.config.custom_params['multiplier']
        
        # Calculate centerline (EMA)
        centerline = calculate_ema(close, period)
        
        # Calculate ATR
        tr = true_range(high, low, close)
        atr = calculate_sma(tr, atr_period)  # Using SMA for ATR
        
        # Calculate upper and lower channels
        upper_channel = centerline + (multiplier * atr)
        lower_channel = centerline - (multiplier * atr)
        
        # Generate signals
        signals = self._generate_keltner_signals(close, upper_channel, lower_channel, centerline)
        
        # Determine trend
        trend = self._determine_keltner_trend(close, centerline)
        
        return IndicatorResult(
            values=centerline,
            signals=signals,
            trend=trend,
            strength=self._calculate_keltner_strength(close, upper_channel, lower_channel),
            confidence=self._calculate_keltner_confidence(close, upper_channel, lower_channel),
            metadata={
                'upper_channel': upper_channel,
                'lower_channel': lower_channel,
                'atr': atr
            }
        )
    
    def _generate_keltner_signals(self, close: np.ndarray, upper_channel: np.ndarray,
                                lower_channel: np.ndarray, centerline: np.ndarray) -> List[SignalType]:
        """Generate Keltner Channels signals"""
        signals = [SignalType.NEUTRAL] * len(close)
        
        for i in range(1, len(close)):
            if (np.isnan(upper_channel[i]) or np.isnan(lower_channel[i]) or 
                np.isnan(centerline[i])):
                continue
            
            current_price = close[i]
            prev_price = close[i-1]
            
            # Breakout above upper channel
            if current_price > upper_channel[i] and prev_price <= upper_channel[i-1]:
                signals[i] = SignalType.STRONG_BUY
            # Breakout below lower channel
            elif current_price < lower_channel[i] and prev_price >= lower_channel[i-1]:
                signals[i] = SignalType.STRONG_SELL
            
            # Price returns to channel from outside
            elif (prev_price > upper_channel[i-1] and current_price <= upper_channel[i]):
                signals[i] = SignalType.SELL
            elif (prev_price < lower_channel[i-1] and current_price >= lower_channel[i]):
                signals[i] = SignalType.BUY
            
            # Centerline crossover
            elif (current_price > centerline[i] and prev_price <= centerline[i-1]):
                signals[i] = SignalType.BUY
            elif (current_price < centerline[i] and prev_price >= centerline[i-1]):
                signals[i] = SignalType.SELL
            
            # Trend continuation
            elif current_price > centerline[i]:
                signals[i] = SignalType.BUY
            else:
                signals[i] = SignalType.SELL
        
        return signals
    
    def _determine_keltner_trend(self, close: np.ndarray, centerline: np.ndarray) -> TrendDirection:
        """Determine trend based on price position relative to centerline"""
        if len(close) < 3:
            return TrendDirection.UNKNOWN
        
        current_price = close[-1]
        current_center = centerline[-1]
        
        if np.isnan(current_center):
            return TrendDirection.UNKNOWN
        
        # Check recent price position
        recent_close = close[-min(5, len(close)):]
        recent_center = centerline[-min(5, len(centerline)):]
        
        above_center = np.sum(recent_close > recent_center)
        below_center = np.sum(recent_close < recent_center)
        
        if above_center > below_center:
            return TrendDirection.UPTREND
        elif below_center > above_center:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_keltner_strength(self, close: np.ndarray, upper_channel: np.ndarray,
                                  lower_channel: np.ndarray) -> float:
        """Calculate Keltner strength based on channel position"""
        if len(close) == 0:
            return 0.0
        
        current_price = close[-1]
        current_upper = upper_channel[-1]
        current_lower = lower_channel[-1]
        
        if np.isnan(current_upper) or np.isnan(current_lower):
            return 0.0
        
        # Calculate position within channel (0 = lower, 1 = upper)
        channel_width = current_upper - current_lower
        if channel_width == 0:
            return 0.0
        
        position = (current_price - current_lower) / channel_width
        
        # Strength based on distance from center
        strength = abs(position - 0.5) * 2
        return min(strength, 1.0)
    
    def _calculate_keltner_confidence(self, close: np.ndarray, upper_channel: np.ndarray,
                                    lower_channel: np.ndarray) -> float:
        """Calculate Keltner confidence"""
        if len(close) == 0:
            return 0.5
        
        current_price = close[-1]
        current_upper = upper_channel[-1]
        current_lower = lower_channel[-1]
        
        if np.isnan(current_upper) or np.isnan(current_lower):
            return 0.5
        
        # Higher confidence for breakouts
        if current_price > current_upper or current_price < current_lower:
            return 0.9
        # Medium confidence within channels
        else:
            return 0.7

class DonchianChannels(BaseIndicator):
    """Donchian Channels Indicator
    
    Donchian Channels are formed by the highest high and lowest low
    over a specified period, with an optional middle line.
    """
    
    def __init__(self, period: int = 20, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Donchian Channels"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Donchian Channels require OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        period = self.config.period
        
        # Calculate upper and lower channels
        upper_channel = np.full_like(close, np.nan)
        lower_channel = np.full_like(close, np.nan)
        
        for i in range(period - 1, len(close)):
            upper_channel[i] = np.max(high[i - period + 1:i + 1])
            lower_channel[i] = np.min(low[i - period + 1:i + 1])
        
        # Calculate middle line
        middle_line = (upper_channel + lower_channel) / 2
        
        # Generate signals
        signals = self._generate_donchian_signals(close, upper_channel, lower_channel, middle_line)
        
        # Determine trend
        trend = self._determine_donchian_trend(close, middle_line)
        
        return IndicatorResult(
            values=middle_line,
            signals=signals,
            trend=trend,
            strength=self._calculate_donchian_strength(close, upper_channel, lower_channel),
            confidence=self._calculate_donchian_confidence(close, upper_channel, lower_channel),
            metadata={
                'upper_channel': upper_channel,
                'lower_channel': lower_channel
            }
        )
    
    def _generate_donchian_signals(self, close: np.ndarray, upper_channel: np.ndarray,
                                 lower_channel: np.ndarray, middle_line: np.ndarray) -> List[SignalType]:
        """Generate Donchian Channels signals"""
        signals = [SignalType.NEUTRAL] * len(close)
        
        for i in range(1, len(close)):
            if (np.isnan(upper_channel[i]) or np.isnan(lower_channel[i]) or 
                np.isnan(middle_line[i])):
                continue
            
            current_price = close[i]
            prev_price = close[i-1]
            
            # Breakout to new high
            if current_price >= upper_channel[i] and prev_price < upper_channel[i-1]:
                signals[i] = SignalType.STRONG_BUY
            # Breakout to new low
            elif current_price <= lower_channel[i] and prev_price > lower_channel[i-1]:
                signals[i] = SignalType.STRONG_SELL
            
            # Middle line crossover
            elif (current_price > middle_line[i] and prev_price <= middle_line[i-1]):
                signals[i] = SignalType.BUY
            elif (current_price < middle_line[i] and prev_price >= middle_line[i-1]):
                signals[i] = SignalType.SELL
            
            # Trend continuation
            elif current_price > middle_line[i]:
                signals[i] = SignalType.BUY
            else:
                signals[i] = SignalType.SELL
        
        return signals
    
    def _determine_donchian_trend(self, close: np.ndarray, middle_line: np.ndarray) -> TrendDirection:
        """Determine trend based on Donchian middle line"""
        if len(close) < 3:
            return TrendDirection.UNKNOWN
        
        current_price = close[-1]
        current_middle = middle_line[-1]
        
        if np.isnan(current_middle):
            return TrendDirection.UNKNOWN
        
        # Simple trend based on price vs middle line
        recent_close = close[-min(5, len(close)):]
        recent_middle = middle_line[-min(5, len(middle_line)):]
        
        above_count = np.sum(recent_close > recent_middle)
        below_count = np.sum(recent_close < recent_middle)
        
        if above_count > below_count:
            return TrendDirection.UPTREND
        elif below_count > above_count:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_donchian_strength(self, close: np.ndarray, upper_channel: np.ndarray,
                                   lower_channel: np.ndarray) -> float:
        """Calculate Donchian strength"""
        if len(close) == 0:
            return 0.0
        
        current_price = close[-1]
        current_upper = upper_channel[-1]
        current_lower = lower_channel[-1]
        
        if np.isnan(current_upper) or np.isnan(current_lower):
            return 0.0
        
        # Strength based on channel position
        channel_width = current_upper - current_lower
        if channel_width == 0:
            return 0.0
        
        position = (current_price - current_lower) / channel_width
        strength = abs(position - 0.5) * 2
        
        return min(strength, 1.0)
    
    def _calculate_donchian_confidence(self, close: np.ndarray, upper_channel: np.ndarray,
                                     lower_channel: np.ndarray) -> float:
        """Calculate Donchian confidence"""
        if len(close) == 0:
            return 0.5
        
        current_price = close[-1]
        current_upper = upper_channel[-1]
        current_lower = lower_channel[-1]
        
        if np.isnan(current_upper) or np.isnan(current_lower):
            return 0.5
        
        # High confidence for breakouts
        if current_price >= current_upper or current_price <= current_lower:
            return 0.95
        else:
            return 0.7

# Additional volatility indicators can be added here:
# - Standard Deviation Channels
# - Volatility Index
# - Price Channels
# - Envelope Channels
# etc.