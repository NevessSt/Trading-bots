"""Trend Indicators Module

This module implements popular trend-following technical indicators:
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- MACD (Moving Average Convergence Divergence)
- Parabolic SAR
- Ichimoku Cloud
- SuperTrend
- Weighted Moving Average (WMA)
- Hull Moving Average (HMA)

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

class SimpleMovingAverage(BaseIndicator):
    """Simple Moving Average (SMA) Indicator
    
    The SMA is the average price over a specified number of periods.
    It's a lagging indicator that smooths price data to identify trend direction.
    """
    
    def __init__(self, period: int = 20, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Simple Moving Average"""
        if isinstance(data, pd.DataFrame):
            prices = data[self.config.source].values
        else:
            prices = data
        
        sma_values = calculate_sma(prices, self.config.period)
        
        # Generate signals based on price vs SMA
        signals = self._generate_sma_signals(prices, sma_values)
        
        # Determine trend
        trend = self._determine_sma_trend(sma_values)
        
        return IndicatorResult(
            values=sma_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_trend_strength(sma_values),
            confidence=self._calculate_confidence(prices, sma_values)
        )
    
    def _generate_sma_signals(self, prices: np.ndarray, sma_values: np.ndarray) -> List[SignalType]:
        """Generate trading signals based on price vs SMA crossover"""
        signals = [SignalType.NEUTRAL] * len(prices)
        
        for i in range(1, len(prices)):
            if np.isnan(sma_values[i]) or np.isnan(sma_values[i-1]):
                continue
            
            # Price crosses above SMA
            if prices[i] > sma_values[i] and prices[i-1] <= sma_values[i-1]:
                signals[i] = SignalType.BUY
            # Price crosses below SMA
            elif prices[i] < sma_values[i] and prices[i-1] >= sma_values[i-1]:
                signals[i] = SignalType.SELL
            # Price above SMA (bullish)
            elif prices[i] > sma_values[i]:
                signals[i] = SignalType.BUY if signals[i-1] != SignalType.SELL else SignalType.HOLD
            # Price below SMA (bearish)
            elif prices[i] < sma_values[i]:
                signals[i] = SignalType.SELL if signals[i-1] != SignalType.BUY else SignalType.HOLD
            else:
                signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_sma_trend(self, sma_values: np.ndarray) -> TrendDirection:
        """Determine trend based on SMA slope"""
        if len(sma_values) < 3:
            return TrendDirection.UNKNOWN
        
        # Use last few values
        recent_values = sma_values[-min(5, len(sma_values)):]
        valid_values = recent_values[~np.isnan(recent_values)]
        
        if len(valid_values) < 2:
            return TrendDirection.UNKNOWN
        
        # Calculate slope
        x = np.arange(len(valid_values))
        slope = np.polyfit(x, valid_values, 1)[0]
        
        if slope > 0:
            return TrendDirection.UPTREND
        elif slope < 0:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_trend_strength(self, sma_values: np.ndarray) -> float:
        """Calculate trend strength based on SMA consistency"""
        if len(sma_values) < 5:
            return 0.0
        
        recent_values = sma_values[-5:]
        valid_values = recent_values[~np.isnan(recent_values)]
        
        if len(valid_values) < 2:
            return 0.0
        
        # Calculate consistency of direction
        changes = np.diff(valid_values)
        if len(changes) == 0:
            return 0.0
        
        positive_changes = np.sum(changes > 0)
        negative_changes = np.sum(changes < 0)
        total_changes = len(changes)
        
        # Strength is the consistency of direction
        strength = max(positive_changes, negative_changes) / total_changes
        return min(strength, 1.0)
    
    def _calculate_confidence(self, prices: np.ndarray, sma_values: np.ndarray) -> float:
        """Calculate confidence based on price distance from SMA"""
        if len(prices) == 0 or np.isnan(sma_values[-1]):
            return 0.0
        
        # Calculate relative distance
        distance = abs(prices[-1] - sma_values[-1]) / sma_values[-1]
        
        # Convert to confidence (closer = higher confidence)
        confidence = 1.0 / (1.0 + distance * 10)
        return min(confidence, 1.0)

class ExponentialMovingAverage(BaseIndicator):
    """Exponential Moving Average (EMA) Indicator
    
    The EMA gives more weight to recent prices, making it more responsive
    to new information compared to the SMA.
    """
    
    def __init__(self, period: int = 20, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Exponential Moving Average"""
        if isinstance(data, pd.DataFrame):
            prices = data[self.config.source].values
        else:
            prices = data
        
        ema_values = calculate_ema(prices, self.config.period)
        
        # Generate signals (similar to SMA but more responsive)
        signals = self._generate_ema_signals(prices, ema_values)
        
        # Determine trend
        trend = self._determine_sma_trend(ema_values)  # Reuse SMA trend logic
        
        return IndicatorResult(
            values=ema_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_trend_strength(ema_values),
            confidence=self._calculate_confidence(prices, ema_values)
        )
    
    def _generate_ema_signals(self, prices: np.ndarray, ema_values: np.ndarray) -> List[SignalType]:
        """Generate trading signals based on price vs EMA"""
        signals = [SignalType.NEUTRAL] * len(prices)
        
        for i in range(1, len(prices)):
            if np.isnan(ema_values[i]) or np.isnan(ema_values[i-1]):
                continue
            
            # More sensitive crossover detection for EMA
            price_above = prices[i] > ema_values[i]
            price_above_prev = prices[i-1] > ema_values[i-1]
            
            if price_above and not price_above_prev:
                signals[i] = SignalType.BUY
            elif not price_above and price_above_prev:
                signals[i] = SignalType.SELL
            elif price_above:
                signals[i] = SignalType.BUY if signals[i-1] != SignalType.SELL else SignalType.HOLD
            else:
                signals[i] = SignalType.SELL if signals[i-1] != SignalType.BUY else SignalType.HOLD
        
        return signals

class MACD(BaseIndicator):
    """MACD (Moving Average Convergence Divergence) Indicator
    
    MACD is a trend-following momentum indicator that shows the relationship
    between two moving averages of a security's price.
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs):
        config = IndicatorConfig(period=slow_period, **kwargs)
        config.custom_params.update({
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period
        })
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate MACD"""
        if isinstance(data, pd.DataFrame):
            prices = data[self.config.source].values
        else:
            prices = data
        
        fast_period = self.config.custom_params['fast_period']
        slow_period = self.config.custom_params['slow_period']
        signal_period = self.config.custom_params['signal_period']
        
        # Calculate EMAs
        fast_ema = calculate_ema(prices, fast_period)
        slow_ema = calculate_ema(prices, slow_period)
        
        # MACD line
        macd_line = fast_ema - slow_ema
        
        # Signal line (EMA of MACD line)
        signal_line = calculate_ema(macd_line, signal_period)
        
        # Histogram
        histogram = macd_line - signal_line
        
        # Generate signals
        signals = self._generate_macd_signals(macd_line, signal_line, histogram)
        
        # Determine trend
        trend = self._determine_macd_trend(macd_line, signal_line)
        
        return IndicatorResult(
            values=macd_line,
            signals=signals,
            trend=trend,
            strength=self._calculate_macd_strength(histogram),
            confidence=self._calculate_macd_confidence(macd_line, signal_line),
            metadata={
                'signal_line': signal_line,
                'histogram': histogram,
                'fast_ema': fast_ema,
                'slow_ema': slow_ema
            }
        )
    
    def _generate_macd_signals(self, macd_line: np.ndarray, signal_line: np.ndarray, 
                              histogram: np.ndarray) -> List[SignalType]:
        """Generate MACD trading signals"""
        signals = [SignalType.NEUTRAL] * len(macd_line)
        
        for i in range(1, len(macd_line)):
            if (np.isnan(macd_line[i]) or np.isnan(signal_line[i]) or 
                np.isnan(macd_line[i-1]) or np.isnan(signal_line[i-1])):
                continue
            
            # MACD crosses above signal line
            if macd_line[i] > signal_line[i] and macd_line[i-1] <= signal_line[i-1]:
                if macd_line[i] < 0:  # Below zero line - stronger signal
                    signals[i] = SignalType.STRONG_BUY
                else:
                    signals[i] = SignalType.BUY
            
            # MACD crosses below signal line
            elif macd_line[i] < signal_line[i] and macd_line[i-1] >= signal_line[i-1]:
                if macd_line[i] > 0:  # Above zero line - stronger signal
                    signals[i] = SignalType.STRONG_SELL
                else:
                    signals[i] = SignalType.SELL
            
            # Histogram analysis for additional signals
            elif len(histogram) > i and not np.isnan(histogram[i]):
                if histogram[i] > 0 and macd_line[i] > signal_line[i]:
                    signals[i] = SignalType.BUY
                elif histogram[i] < 0 and macd_line[i] < signal_line[i]:
                    signals[i] = SignalType.SELL
                else:
                    signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_macd_trend(self, macd_line: np.ndarray, signal_line: np.ndarray) -> TrendDirection:
        """Determine trend based on MACD position"""
        if len(macd_line) < 3:
            return TrendDirection.UNKNOWN
        
        latest_macd = macd_line[-1]
        latest_signal = signal_line[-1]
        
        if np.isnan(latest_macd) or np.isnan(latest_signal):
            return TrendDirection.UNKNOWN
        
        # Trend based on MACD vs signal line and zero line
        if latest_macd > latest_signal:
            if latest_macd > 0:
                return TrendDirection.UPTREND
            else:
                return TrendDirection.SIDEWAYS  # Bullish but below zero
        else:
            if latest_macd < 0:
                return TrendDirection.DOWNTREND
            else:
                return TrendDirection.SIDEWAYS  # Bearish but above zero
    
    def _calculate_macd_strength(self, histogram: np.ndarray) -> float:
        """Calculate MACD strength based on histogram"""
        if len(histogram) < 3:
            return 0.0
        
        recent_hist = histogram[-3:]
        valid_hist = recent_hist[~np.isnan(recent_hist)]
        
        if len(valid_hist) == 0:
            return 0.0
        
        # Strength based on histogram magnitude and consistency
        avg_magnitude = np.mean(np.abs(valid_hist))
        max_magnitude = np.max(np.abs(valid_hist))
        
        if max_magnitude == 0:
            return 0.0
        
        consistency = avg_magnitude / max_magnitude
        return min(consistency, 1.0)
    
    def _calculate_macd_confidence(self, macd_line: np.ndarray, signal_line: np.ndarray) -> float:
        """Calculate MACD confidence based on line separation"""
        if len(macd_line) == 0 or np.isnan(macd_line[-1]) or np.isnan(signal_line[-1]):
            return 0.0
        
        # Confidence based on separation between MACD and signal line
        separation = abs(macd_line[-1] - signal_line[-1])
        
        # Normalize by recent volatility
        recent_values = macd_line[-min(20, len(macd_line)):]
        valid_values = recent_values[~np.isnan(recent_values)]
        
        if len(valid_values) < 2:
            return 0.5
        
        volatility = np.std(valid_values)
        if volatility == 0:
            return 0.5
        
        normalized_separation = separation / volatility
        confidence = min(normalized_separation / 2.0, 1.0)
        
        return confidence

class ParabolicSAR(BaseIndicator):
    """Parabolic SAR (Stop and Reverse) Indicator
    
    The Parabolic SAR is a trend-following indicator that provides
    potential reversal points in the price direction.
    """
    
    def __init__(self, acceleration: float = 0.02, maximum: float = 0.2, **kwargs):
        config = IndicatorConfig(**kwargs)
        config.custom_params.update({
            'acceleration': acceleration,
            'maximum': maximum
        })
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Parabolic SAR"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Parabolic SAR requires OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        acceleration = self.config.custom_params['acceleration']
        maximum = self.config.custom_params['maximum']
        
        sar_values = np.full_like(close, np.nan)
        af = acceleration
        trend = 1  # 1 for uptrend, -1 for downtrend
        ep = high[0]  # Extreme point
        sar = low[0]  # Initial SAR
        
        sar_values[0] = sar
        
        for i in range(1, len(close)):
            # Calculate SAR
            sar = sar + af * (ep - sar)
            
            if trend == 1:  # Uptrend
                # Check for trend reversal
                if low[i] <= sar:
                    trend = -1
                    sar = ep
                    ep = low[i]
                    af = acceleration
                else:
                    # Update extreme point and acceleration factor
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + acceleration, maximum)
                    
                    # Ensure SAR doesn't go above previous lows
                    sar = min(sar, low[i-1])
                    if i > 1:
                        sar = min(sar, low[i-2])
            
            else:  # Downtrend
                # Check for trend reversal
                if high[i] >= sar:
                    trend = 1
                    sar = ep
                    ep = high[i]
                    af = acceleration
                else:
                    # Update extreme point and acceleration factor
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + acceleration, maximum)
                    
                    # Ensure SAR doesn't go below previous highs
                    sar = max(sar, high[i-1])
                    if i > 1:
                        sar = max(sar, high[i-2])
            
            sar_values[i] = sar
        
        # Generate signals
        signals = self._generate_sar_signals(close, sar_values)
        
        # Determine trend
        trend_direction = self._determine_sar_trend(close, sar_values)
        
        return IndicatorResult(
            values=sar_values,
            signals=signals,
            trend=trend_direction,
            strength=self._calculate_sar_strength(close, sar_values),
            confidence=0.8  # SAR generally has high confidence
        )
    
    def _generate_sar_signals(self, close: np.ndarray, sar_values: np.ndarray) -> List[SignalType]:
        """Generate Parabolic SAR signals"""
        signals = [SignalType.NEUTRAL] * len(close)
        
        for i in range(1, len(close)):
            if np.isnan(sar_values[i]) or np.isnan(sar_values[i-1]):
                continue
            
            # SAR below price = uptrend
            if sar_values[i] < close[i] and sar_values[i-1] >= close[i-1]:
                signals[i] = SignalType.BUY
            # SAR above price = downtrend
            elif sar_values[i] > close[i] and sar_values[i-1] <= close[i-1]:
                signals[i] = SignalType.SELL
            # Continue trend
            elif sar_values[i] < close[i]:
                signals[i] = SignalType.BUY
            else:
                signals[i] = SignalType.SELL
        
        return signals
    
    def _determine_sar_trend(self, close: np.ndarray, sar_values: np.ndarray) -> TrendDirection:
        """Determine trend based on SAR position"""
        if len(close) == 0 or np.isnan(sar_values[-1]):
            return TrendDirection.UNKNOWN
        
        if sar_values[-1] < close[-1]:
            return TrendDirection.UPTREND
        else:
            return TrendDirection.DOWNTREND
    
    def _calculate_sar_strength(self, close: np.ndarray, sar_values: np.ndarray) -> float:
        """Calculate SAR trend strength"""
        if len(close) < 5:
            return 0.0
        
        # Count consecutive periods in same trend
        recent_close = close[-5:]
        recent_sar = sar_values[-5:]
        
        same_trend_count = 0
        for i in range(len(recent_close)):
            if not np.isnan(recent_sar[i]):
                if (recent_sar[i] < recent_close[i] and 
                    (i == 0 or recent_sar[i-1] < recent_close[i-1])):
                    same_trend_count += 1
                elif (recent_sar[i] > recent_close[i] and 
                      (i == 0 or recent_sar[i-1] > recent_close[i-1])):
                    same_trend_count += 1
        
        return min(same_trend_count / 5.0, 1.0)

class SuperTrend(BaseIndicator):
    """SuperTrend Indicator
    
    SuperTrend is a trend-following indicator that uses Average True Range (ATR)
    to calculate dynamic support and resistance levels.
    """
    
    def __init__(self, period: int = 10, multiplier: float = 3.0, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        config.custom_params['multiplier'] = multiplier
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate SuperTrend"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("SuperTrend requires OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        period = self.config.period
        multiplier = self.config.custom_params['multiplier']
        
        # Calculate ATR
        from .indicator_base import true_range
        tr = true_range(high, low, close)
        atr = calculate_sma(tr, period)
        
        # Calculate basic bands
        hl2 = (high + low) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # Calculate SuperTrend
        supertrend = np.full_like(close, np.nan)
        trend = np.ones_like(close)  # 1 for uptrend, -1 for downtrend
        
        for i in range(1, len(close)):
            if np.isnan(atr[i]):
                continue
            
            # Calculate final bands
            if upper_band[i] < upper_band[i-1] or close[i-1] > upper_band[i-1]:
                final_upper = upper_band[i]
            else:
                final_upper = upper_band[i-1]
            
            if lower_band[i] > lower_band[i-1] or close[i-1] < lower_band[i-1]:
                final_lower = lower_band[i]
            else:
                final_lower = lower_band[i-1]
            
            # Determine trend
            if close[i] <= final_lower:
                trend[i] = -1
                supertrend[i] = final_upper
            elif close[i] >= final_upper:
                trend[i] = 1
                supertrend[i] = final_lower
            else:
                trend[i] = trend[i-1]
                if trend[i] == 1:
                    supertrend[i] = final_lower
                else:
                    supertrend[i] = final_upper
        
        # Generate signals
        signals = self._generate_supertrend_signals(close, supertrend, trend)
        
        # Determine trend direction
        trend_direction = TrendDirection.UPTREND if trend[-1] == 1 else TrendDirection.DOWNTREND
        
        return IndicatorResult(
            values=supertrend,
            signals=signals,
            trend=trend_direction,
            strength=self._calculate_supertrend_strength(trend),
            confidence=0.85,  # SuperTrend generally has high confidence
            metadata={'trend_values': trend, 'atr': atr}
        )
    
    def _generate_supertrend_signals(self, close: np.ndarray, supertrend: np.ndarray, 
                                   trend: np.ndarray) -> List[SignalType]:
        """Generate SuperTrend signals"""
        signals = [SignalType.NEUTRAL] * len(close)
        
        for i in range(1, len(close)):
            if np.isnan(supertrend[i]):
                continue
            
            # Trend change from down to up
            if trend[i] == 1 and trend[i-1] == -1:
                signals[i] = SignalType.BUY
            # Trend change from up to down
            elif trend[i] == -1 and trend[i-1] == 1:
                signals[i] = SignalType.SELL
            # Continue existing trend
            elif trend[i] == 1:
                signals[i] = SignalType.BUY
            else:
                signals[i] = SignalType.SELL
        
        return signals
    
    def _calculate_supertrend_strength(self, trend: np.ndarray) -> float:
        """Calculate SuperTrend strength based on trend consistency"""
        if len(trend) < 5:
            return 0.0
        
        # Count consecutive periods in same trend
        recent_trend = trend[-5:]
        current_trend = recent_trend[-1]
        
        consecutive_count = 0
        for i in range(len(recent_trend) - 1, -1, -1):
            if recent_trend[i] == current_trend:
                consecutive_count += 1
            else:
                break
        
        return min(consecutive_count / 5.0, 1.0)

# Additional trend indicators can be added here:
# - Ichimoku Cloud
# - Hull Moving Average
# - Weighted Moving Average
# - Adaptive Moving Average
# etc.