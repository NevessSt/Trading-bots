"""Volume Indicators Module

This module implements popular volume-based technical indicators:
- OBV (On-Balance Volume)
- Volume Profile
- VWAP (Volume Weighted Average Price)
- Accumulation/Distribution Line
- Chaikin Money Flow
- Volume Rate of Change
- Price Volume Trend
- Ease of Movement

All indicators follow the BaseIndicator interface for consistency.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Optional, Dict
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

class OBV(BaseIndicator):
    """On-Balance Volume (OBV) Indicator
    
    OBV measures buying and selling pressure by adding volume on up days
    and subtracting volume on down days. It helps confirm price trends.
    """
    
    def __init__(self, **kwargs):
        config = IndicatorConfig(**kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate OBV"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("OBV requires OHLC and volume data")
        
        close = data['close'].values
        volume = data['volume'].values
        
        # Calculate OBV
        obv_values = np.zeros_like(close)
        obv_values[0] = volume[0]
        
        for i in range(1, len(close)):
            if close[i] > close[i-1]:
                obv_values[i] = obv_values[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv_values[i] = obv_values[i-1] - volume[i]
            else:
                obv_values[i] = obv_values[i-1]
        
        # Generate signals
        signals = self._generate_obv_signals(obv_values, close)
        
        # Determine trend
        trend = self._determine_obv_trend(obv_values)
        
        return IndicatorResult(
            values=obv_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_obv_strength(obv_values, close),
            confidence=self._calculate_obv_confidence(obv_values, close)
        )
    
    def _generate_obv_signals(self, obv_values: np.ndarray, close: np.ndarray) -> List[SignalType]:
        """Generate OBV signals based on divergences and trend"""
        signals = [SignalType.NEUTRAL] * len(obv_values)
        
        # Calculate OBV moving average for trend
        obv_ma = calculate_sma(obv_values, 10)
        
        for i in range(10, len(obv_values)):
            if np.isnan(obv_ma[i]) or np.isnan(obv_ma[i-1]):
                continue
            
            current_obv = obv_values[i]
            prev_obv = obv_values[i-1]
            current_price = close[i]
            prev_price = close[i-1]
            
            # OBV trend signals
            if current_obv > obv_ma[i] and prev_obv <= obv_ma[i-1]:
                signals[i] = SignalType.BUY
            elif current_obv < obv_ma[i] and prev_obv >= obv_ma[i-1]:
                signals[i] = SignalType.SELL
            
            # Divergence detection (simplified)
            elif i >= 20:
                # Look for bullish divergence: price down, OBV up
                recent_price_trend = close[i] - close[i-10]
                recent_obv_trend = obv_values[i] - obv_values[i-10]
                
                if recent_price_trend < 0 and recent_obv_trend > 0:
                    signals[i] = SignalType.STRONG_BUY  # Bullish divergence
                elif recent_price_trend > 0 and recent_obv_trend < 0:
                    signals[i] = SignalType.STRONG_SELL  # Bearish divergence
            
            # Trend continuation
            elif current_obv > obv_ma[i]:
                signals[i] = SignalType.BUY
            else:
                signals[i] = SignalType.SELL
        
        return signals
    
    def _determine_obv_trend(self, obv_values: np.ndarray) -> TrendDirection:
        """Determine trend based on OBV direction"""
        if len(obv_values) < 10:
            return TrendDirection.UNKNOWN
        
        # Calculate trend using linear regression
        recent_obv = obv_values[-10:]
        x = np.arange(len(recent_obv))
        
        try:
            slope = np.polyfit(x, recent_obv, 1)[0]
            
            if slope > 0:
                return TrendDirection.UPTREND
            elif slope < 0:
                return TrendDirection.DOWNTREND
            else:
                return TrendDirection.SIDEWAYS
        except:
            return TrendDirection.UNKNOWN
    
    def _calculate_obv_strength(self, obv_values: np.ndarray, close: np.ndarray) -> float:
        """Calculate OBV strength based on trend consistency"""
        if len(obv_values) < 10:
            return 0.0
        
        # Calculate correlation between OBV and price trends
        recent_obv = obv_values[-10:]
        recent_close = close[-10:]
        
        obv_changes = np.diff(recent_obv)
        price_changes = np.diff(recent_close)
        
        if len(obv_changes) == 0 or len(price_changes) == 0:
            return 0.0
        
        # Count agreements between OBV and price direction
        agreements = np.sum((obv_changes > 0) == (price_changes > 0))
        total = len(obv_changes)
        
        strength = agreements / total if total > 0 else 0.0
        return min(strength, 1.0)
    
    def _calculate_obv_confidence(self, obv_values: np.ndarray, close: np.ndarray) -> float:
        """Calculate OBV confidence based on volume consistency"""
        if len(obv_values) < 5:
            return 0.5
        
        # Check for consistent OBV trend
        recent_obv = obv_values[-5:]
        obv_changes = np.diff(recent_obv)
        
        if len(obv_changes) == 0:
            return 0.5
        
        # Consistency of direction
        positive_changes = np.sum(obv_changes > 0)
        negative_changes = np.sum(obv_changes < 0)
        total_changes = len(obv_changes)
        
        consistency = max(positive_changes, negative_changes) / total_changes
        return min(consistency, 1.0)

class VWAP(BaseIndicator):
    """Volume Weighted Average Price (VWAP) Indicator
    
    VWAP gives the average price weighted by volume, providing a benchmark
    for intraday trading and institutional order execution.
    """
    
    def __init__(self, **kwargs):
        config = IndicatorConfig(**kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate VWAP"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("VWAP requires OHLC and volume data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        volume = data['volume'].values
        
        # Calculate typical price
        typical_price = (high + low + close) / 3
        
        # Calculate VWAP
        vwap_values = np.full_like(close, np.nan)
        cumulative_volume = 0
        cumulative_pv = 0
        
        for i in range(len(close)):
            if volume[i] > 0:  # Only include periods with volume
                cumulative_pv += typical_price[i] * volume[i]
                cumulative_volume += volume[i]
                
                if cumulative_volume > 0:
                    vwap_values[i] = cumulative_pv / cumulative_volume
        
        # Generate signals
        signals = self._generate_vwap_signals(close, vwap_values, volume)
        
        # Determine trend
        trend = self._determine_vwap_trend(close, vwap_values)
        
        return IndicatorResult(
            values=vwap_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_vwap_strength(close, vwap_values, volume),
            confidence=self._calculate_vwap_confidence(close, vwap_values),
            metadata={'typical_price': typical_price}
        )
    
    def _generate_vwap_signals(self, close: np.ndarray, vwap_values: np.ndarray, 
                              volume: np.ndarray) -> List[SignalType]:
        """Generate VWAP signals"""
        signals = [SignalType.NEUTRAL] * len(close)
        
        for i in range(1, len(close)):
            if np.isnan(vwap_values[i]) or np.isnan(vwap_values[i-1]):
                continue
            
            current_price = close[i]
            prev_price = close[i-1]
            current_vwap = vwap_values[i]
            prev_vwap = vwap_values[i-1]
            current_volume = volume[i]
            
            # Price crosses above VWAP with volume
            if (current_price > current_vwap and prev_price <= prev_vwap):
                if current_volume > np.mean(volume[max(0, i-10):i+1]):
                    signals[i] = SignalType.STRONG_BUY
                else:
                    signals[i] = SignalType.BUY
            
            # Price crosses below VWAP with volume
            elif (current_price < current_vwap and prev_price >= prev_vwap):
                if current_volume > np.mean(volume[max(0, i-10):i+1]):
                    signals[i] = SignalType.STRONG_SELL
                else:
                    signals[i] = SignalType.SELL
            
            # Price above VWAP (bullish)
            elif current_price > current_vwap:
                signals[i] = SignalType.BUY
            
            # Price below VWAP (bearish)
            elif current_price < current_vwap:
                signals[i] = SignalType.SELL
            
            else:
                signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_vwap_trend(self, close: np.ndarray, vwap_values: np.ndarray) -> TrendDirection:
        """Determine trend based on price vs VWAP"""
        if len(close) < 5:
            return TrendDirection.UNKNOWN
        
        recent_close = close[-5:]
        recent_vwap = vwap_values[-5:]
        
        # Remove NaN values
        valid_indices = ~(np.isnan(recent_close) | np.isnan(recent_vwap))
        if np.sum(valid_indices) < 3:
            return TrendDirection.UNKNOWN
        
        valid_close = recent_close[valid_indices]
        valid_vwap = recent_vwap[valid_indices]
        
        above_count = np.sum(valid_close > valid_vwap)
        below_count = np.sum(valid_close < valid_vwap)
        
        if above_count > below_count:
            return TrendDirection.UPTREND
        elif below_count > above_count:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_vwap_strength(self, close: np.ndarray, vwap_values: np.ndarray, 
                               volume: np.ndarray) -> float:
        """Calculate VWAP strength based on price distance and volume"""
        if len(close) == 0 or np.isnan(vwap_values[-1]):
            return 0.0
        
        current_price = close[-1]
        current_vwap = vwap_values[-1]
        current_volume = volume[-1]
        
        # Distance from VWAP
        distance = abs(current_price - current_vwap) / current_vwap
        
        # Volume factor
        avg_volume = np.mean(volume[-min(20, len(volume)):]) if len(volume) >= 20 else np.mean(volume)
        volume_factor = min(current_volume / avg_volume, 2.0) / 2.0 if avg_volume > 0 else 0.5
        
        # Combined strength
        strength = (distance * 10 + volume_factor) / 2
        return min(strength, 1.0)
    
    def _calculate_vwap_confidence(self, close: np.ndarray, vwap_values: np.ndarray) -> float:
        """Calculate VWAP confidence"""
        if len(close) < 5 or np.isnan(vwap_values[-1]):
            return 0.5
        
        # Confidence based on consistency of price vs VWAP relationship
        recent_close = close[-5:]
        recent_vwap = vwap_values[-5:]
        
        valid_indices = ~(np.isnan(recent_close) | np.isnan(recent_vwap))
        if np.sum(valid_indices) < 3:
            return 0.5
        
        valid_close = recent_close[valid_indices]
        valid_vwap = recent_vwap[valid_indices]
        
        # Check consistency of relationship
        above_vwap = valid_close > valid_vwap
        consistency = max(np.sum(above_vwap), np.sum(~above_vwap)) / len(above_vwap)
        
        return min(consistency, 1.0)

class AccumulationDistribution(BaseIndicator):
    """Accumulation/Distribution Line Indicator
    
    The A/D Line measures the cumulative flow of money into and out of a security.
    It uses price and volume to assess whether a stock is being accumulated or distributed.
    """
    
    def __init__(self, **kwargs):
        config = IndicatorConfig(**kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Accumulation/Distribution Line"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("A/D Line requires OHLC and volume data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        volume = data['volume'].values
        
        # Calculate Money Flow Multiplier
        mfm = np.full_like(close, 0.0)
        for i in range(len(close)):
            if high[i] != low[i]:
                mfm[i] = ((close[i] - low[i]) - (high[i] - close[i])) / (high[i] - low[i])
        
        # Calculate Money Flow Volume
        mfv = mfm * volume
        
        # Calculate A/D Line (cumulative)
        ad_line = np.cumsum(mfv)
        
        # Generate signals
        signals = self._generate_ad_signals(ad_line, close)
        
        # Determine trend
        trend = self._determine_ad_trend(ad_line)
        
        return IndicatorResult(
            values=ad_line,
            signals=signals,
            trend=trend,
            strength=self._calculate_ad_strength(ad_line, close),
            confidence=self._calculate_ad_confidence(ad_line, close),
            metadata={'mfm': mfm, 'mfv': mfv}
        )
    
    def _generate_ad_signals(self, ad_line: np.ndarray, close: np.ndarray) -> List[SignalType]:
        """Generate A/D Line signals"""
        signals = [SignalType.NEUTRAL] * len(ad_line)
        
        # Calculate A/D Line moving average
        ad_ma = calculate_sma(ad_line, 10)
        
        for i in range(10, len(ad_line)):
            if np.isnan(ad_ma[i]) or np.isnan(ad_ma[i-1]):
                continue
            
            current_ad = ad_line[i]
            prev_ad = ad_line[i-1]
            current_price = close[i]
            prev_price = close[i-1]
            
            # A/D Line trend signals
            if current_ad > ad_ma[i] and prev_ad <= ad_ma[i-1]:
                signals[i] = SignalType.BUY
            elif current_ad < ad_ma[i] and prev_ad >= ad_ma[i-1]:
                signals[i] = SignalType.SELL
            
            # Divergence detection
            elif i >= 20:
                recent_price_trend = close[i] - close[i-10]
                recent_ad_trend = ad_line[i] - ad_line[i-10]
                
                # Bullish divergence: price down, A/D up
                if recent_price_trend < 0 and recent_ad_trend > 0:
                    signals[i] = SignalType.STRONG_BUY
                # Bearish divergence: price up, A/D down
                elif recent_price_trend > 0 and recent_ad_trend < 0:
                    signals[i] = SignalType.STRONG_SELL
            
            # Trend continuation
            elif current_ad > ad_ma[i]:
                signals[i] = SignalType.BUY
            else:
                signals[i] = SignalType.SELL
        
        return signals
    
    def _determine_ad_trend(self, ad_line: np.ndarray) -> TrendDirection:
        """Determine trend based on A/D Line direction"""
        if len(ad_line) < 10:
            return TrendDirection.UNKNOWN
        
        # Calculate trend using recent values
        recent_ad = ad_line[-10:]
        x = np.arange(len(recent_ad))
        
        try:
            slope = np.polyfit(x, recent_ad, 1)[0]
            
            if slope > 0:
                return TrendDirection.UPTREND
            elif slope < 0:
                return TrendDirection.DOWNTREND
            else:
                return TrendDirection.SIDEWAYS
        except:
            return TrendDirection.UNKNOWN
    
    def _calculate_ad_strength(self, ad_line: np.ndarray, close: np.ndarray) -> float:
        """Calculate A/D Line strength"""
        if len(ad_line) < 10:
            return 0.0
        
        # Calculate correlation between A/D and price trends
        recent_ad = ad_line[-10:]
        recent_close = close[-10:]
        
        ad_changes = np.diff(recent_ad)
        price_changes = np.diff(recent_close)
        
        if len(ad_changes) == 0 or len(price_changes) == 0:
            return 0.0
        
        # Count agreements
        agreements = np.sum((ad_changes > 0) == (price_changes > 0))
        total = len(ad_changes)
        
        strength = agreements / total if total > 0 else 0.0
        return min(strength, 1.0)
    
    def _calculate_ad_confidence(self, ad_line: np.ndarray, close: np.ndarray) -> float:
        """Calculate A/D Line confidence"""
        if len(ad_line) < 5:
            return 0.5
        
        # Check trend consistency
        recent_ad = ad_line[-5:]
        ad_changes = np.diff(recent_ad)
        
        if len(ad_changes) == 0:
            return 0.5
        
        positive_changes = np.sum(ad_changes > 0)
        negative_changes = np.sum(ad_changes < 0)
        total_changes = len(ad_changes)
        
        consistency = max(positive_changes, negative_changes) / total_changes
        return min(consistency, 1.0)

class ChaikinMoneyFlow(BaseIndicator):
    """Chaikin Money Flow (CMF) Indicator
    
    CMF measures the amount of Money Flow Volume over a specific period.
    It oscillates between -1 and +1, with values above 0 indicating buying pressure.
    """
    
    def __init__(self, period: int = 20, **kwargs):
        config = IndicatorConfig(period=period, **kwargs)
        super().__init__(config)
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Chaikin Money Flow"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("CMF requires OHLC and volume data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        volume = data['volume'].values
        period = self.config.period
        
        # Calculate Money Flow Multiplier
        mfm = np.full_like(close, 0.0)
        for i in range(len(close)):
            if high[i] != low[i]:
                mfm[i] = ((close[i] - low[i]) - (high[i] - close[i])) / (high[i] - low[i])
        
        # Calculate Money Flow Volume
        mfv = mfm * volume
        
        # Calculate CMF
        cmf_values = np.full_like(close, np.nan)
        
        for i in range(period - 1, len(close)):
            period_mfv = np.sum(mfv[i - period + 1:i + 1])
            period_volume = np.sum(volume[i - period + 1:i + 1])
            
            if period_volume != 0:
                cmf_values[i] = period_mfv / period_volume
        
        # Generate signals
        signals = self._generate_cmf_signals(cmf_values)
        
        # Determine trend
        trend = self._determine_cmf_trend(cmf_values)
        
        return IndicatorResult(
            values=cmf_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_cmf_strength(cmf_values),
            confidence=self._calculate_cmf_confidence(cmf_values)
        )
    
    def _generate_cmf_signals(self, cmf_values: np.ndarray) -> List[SignalType]:
        """Generate CMF signals"""
        signals = [SignalType.NEUTRAL] * len(cmf_values)
        
        for i in range(1, len(cmf_values)):
            if np.isnan(cmf_values[i]) or np.isnan(cmf_values[i-1]):
                continue
            
            current_cmf = cmf_values[i]
            prev_cmf = cmf_values[i-1]
            
            # CMF crosses above zero
            if current_cmf > 0 and prev_cmf <= 0:
                signals[i] = SignalType.BUY
            # CMF crosses below zero
            elif current_cmf < 0 and prev_cmf >= 0:
                signals[i] = SignalType.SELL
            
            # Strong buying pressure
            elif current_cmf > 0.25:
                signals[i] = SignalType.STRONG_BUY
            # Strong selling pressure
            elif current_cmf < -0.25:
                signals[i] = SignalType.STRONG_SELL
            
            # Moderate signals
            elif current_cmf > 0:
                signals[i] = SignalType.BUY
            elif current_cmf < 0:
                signals[i] = SignalType.SELL
            else:
                signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_cmf_trend(self, cmf_values: np.ndarray) -> TrendDirection:
        """Determine trend based on CMF values"""
        if len(cmf_values) < 5:
            return TrendDirection.UNKNOWN
        
        recent_cmf = cmf_values[-5:]
        valid_cmf = recent_cmf[~np.isnan(recent_cmf)]
        
        if len(valid_cmf) < 3:
            return TrendDirection.UNKNOWN
        
        avg_cmf = np.mean(valid_cmf)
        current_cmf = valid_cmf[-1]
        
        if current_cmf > 0.1 and avg_cmf > 0.05:
            return TrendDirection.UPTREND
        elif current_cmf < -0.1 and avg_cmf < -0.05:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_cmf_strength(self, cmf_values: np.ndarray) -> float:
        """Calculate CMF strength"""
        if len(cmf_values) < 3:
            return 0.0
        
        current_cmf = cmf_values[-1]
        if np.isnan(current_cmf):
            return 0.0
        
        # Strength based on absolute CMF value
        strength = abs(current_cmf)
        return min(strength, 1.0)
    
    def _calculate_cmf_confidence(self, cmf_values: np.ndarray) -> float:
        """Calculate CMF confidence"""
        if len(cmf_values) < 5:
            return 0.5
        
        recent_cmf = cmf_values[-5:]
        valid_cmf = recent_cmf[~np.isnan(recent_cmf)]
        
        if len(valid_cmf) < 3:
            return 0.5
        
        # Confidence based on consistency of sign
        positive_count = np.sum(valid_cmf > 0)
        negative_count = np.sum(valid_cmf < 0)
        total_count = len(valid_cmf)
        
        consistency = max(positive_count, negative_count) / total_count
        return min(consistency, 1.0)

# Additional volume indicators can be added here:
# - Volume Rate of Change
# - Price Volume Trend
# - Ease of Movement
# - Volume Oscillator
# - Klinger Oscillator
# etc.