"""Custom Indicators Module

This module implements custom and composite technical indicators:
- Multi-Timeframe Indicators
- Composite Momentum Oscillator
- Trend Strength Index
- Market Regime Detector
- Volatility Breakout Indicator
- Support/Resistance Levels
- Pattern Recognition Indicators

All indicators follow the BaseIndicator interface for consistency.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Optional, Dict, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.signal import find_peaks

from .indicator_base import (
    BaseIndicator, 
    IndicatorResult, 
    IndicatorConfig, 
    SignalType, 
    TrendDirection,
    calculate_sma,
    calculate_ema
)

class CompositeMomentumOscillator(BaseIndicator):
    """Composite Momentum Oscillator (CMO)
    
    Combines multiple momentum indicators (RSI, Stochastic, Williams %R)
    to create a more robust momentum signal.
    """
    
    def __init__(self, rsi_period: int = 14, stoch_period: int = 14, 
                 williams_period: int = 14, **kwargs):
        config = IndicatorConfig(
            period=rsi_period,
            **kwargs
        )
        super().__init__(config)
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.williams_period = williams_period
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Composite Momentum Oscillator"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("CMO requires OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        # Calculate individual momentum indicators
        rsi_values = self._calculate_rsi(close, self.rsi_period)
        stoch_values = self._calculate_stochastic(high, low, close, self.stoch_period)
        williams_values = self._calculate_williams_r(high, low, close, self.williams_period)
        
        # Normalize Williams %R to 0-100 scale (from -100 to 0)
        williams_normalized = (williams_values + 100)
        
        # Calculate composite momentum (weighted average)
        cmo_values = np.full_like(close, np.nan)
        
        for i in range(len(close)):
            if (not np.isnan(rsi_values[i]) and 
                not np.isnan(stoch_values[i]) and 
                not np.isnan(williams_normalized[i])):
                
                # Weighted average (RSI gets higher weight)
                cmo_values[i] = (0.4 * rsi_values[i] + 
                               0.3 * stoch_values[i] + 
                               0.3 * williams_normalized[i])
        
        # Generate signals
        signals = self._generate_cmo_signals(cmo_values)
        
        # Determine trend
        trend = self._determine_cmo_trend(cmo_values)
        
        return IndicatorResult(
            values=cmo_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_cmo_strength(cmo_values),
            confidence=self._calculate_cmo_confidence(cmo_values),
            metadata={
                'rsi': rsi_values,
                'stochastic': stoch_values,
                'williams_r': williams_values
            }
        )
    
    def _calculate_rsi(self, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate RSI"""
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.full_like(close, np.nan)
        avg_loss = np.full_like(close, np.nan)
        
        # Initial averages
        if len(gain) >= period:
            avg_gain[period] = np.mean(gain[:period])
            avg_loss[period] = np.mean(loss[:period])
            
            # Smoothed averages
            for i in range(period + 1, len(close)):
                avg_gain[i] = (avg_gain[i-1] * (period - 1) + gain[i-1]) / period
                avg_loss[i] = (avg_loss[i-1] * (period - 1) + loss[i-1]) / period
        
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 0)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_stochastic(self, high: np.ndarray, low: np.ndarray, 
                            close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Stochastic %K"""
        stoch_values = np.full_like(close, np.nan)
        
        for i in range(period - 1, len(close)):
            highest_high = np.max(high[i - period + 1:i + 1])
            lowest_low = np.min(low[i - period + 1:i + 1])
            
            if highest_high != lowest_low:
                stoch_values[i] = ((close[i] - lowest_low) / 
                                 (highest_high - lowest_low)) * 100
        
        return stoch_values
    
    def _calculate_williams_r(self, high: np.ndarray, low: np.ndarray, 
                            close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Williams %R"""
        williams_values = np.full_like(close, np.nan)
        
        for i in range(period - 1, len(close)):
            highest_high = np.max(high[i - period + 1:i + 1])
            lowest_low = np.min(low[i - period + 1:i + 1])
            
            if highest_high != lowest_low:
                williams_values[i] = ((highest_high - close[i]) / 
                                    (highest_high - lowest_low)) * -100
        
        return williams_values
    
    def _generate_cmo_signals(self, cmo_values: np.ndarray) -> List[SignalType]:
        """Generate CMO signals"""
        signals = [SignalType.NEUTRAL] * len(cmo_values)
        
        for i in range(1, len(cmo_values)):
            if np.isnan(cmo_values[i]) or np.isnan(cmo_values[i-1]):
                continue
            
            current_cmo = cmo_values[i]
            prev_cmo = cmo_values[i-1]
            
            # Oversold/Overbought levels
            if current_cmo < 20:
                signals[i] = SignalType.STRONG_BUY  # Oversold
            elif current_cmo > 80:
                signals[i] = SignalType.STRONG_SELL  # Overbought
            
            # Crossover signals
            elif current_cmo > 50 and prev_cmo <= 50:
                signals[i] = SignalType.BUY
            elif current_cmo < 50 and prev_cmo >= 50:
                signals[i] = SignalType.SELL
            
            # Trend continuation
            elif current_cmo > 50:
                signals[i] = SignalType.BUY
            elif current_cmo < 50:
                signals[i] = SignalType.SELL
            else:
                signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_cmo_trend(self, cmo_values: np.ndarray) -> TrendDirection:
        """Determine trend based on CMO values"""
        if len(cmo_values) < 5:
            return TrendDirection.UNKNOWN
        
        recent_cmo = cmo_values[-5:]
        valid_cmo = recent_cmo[~np.isnan(recent_cmo)]
        
        if len(valid_cmo) < 3:
            return TrendDirection.UNKNOWN
        
        avg_cmo = np.mean(valid_cmo)
        
        if avg_cmo > 60:
            return TrendDirection.UPTREND
        elif avg_cmo < 40:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_cmo_strength(self, cmo_values: np.ndarray) -> float:
        """Calculate CMO strength"""
        if len(cmo_values) < 3:
            return 0.0
        
        current_cmo = cmo_values[-1]
        if np.isnan(current_cmo):
            return 0.0
        
        # Strength based on distance from neutral (50)
        strength = abs(current_cmo - 50) / 50
        return min(strength, 1.0)
    
    def _calculate_cmo_confidence(self, cmo_values: np.ndarray) -> float:
        """Calculate CMO confidence"""
        if len(cmo_values) < 5:
            return 0.5
        
        recent_cmo = cmo_values[-5:]
        valid_cmo = recent_cmo[~np.isnan(recent_cmo)]
        
        if len(valid_cmo) < 3:
            return 0.5
        
        # Confidence based on trend consistency
        trend_direction = np.diff(valid_cmo)
        if len(trend_direction) == 0:
            return 0.5
        
        positive_trends = np.sum(trend_direction > 0)
        negative_trends = np.sum(trend_direction < 0)
        total_trends = len(trend_direction)
        
        consistency = max(positive_trends, negative_trends) / total_trends
        return min(consistency, 1.0)

class TrendStrengthIndex(BaseIndicator):
    """Trend Strength Index (TSI)
    
    Measures the strength of the current trend by analyzing
    price momentum and volatility.
    """
    
    def __init__(self, momentum_period: int = 14, volatility_period: int = 20, **kwargs):
        config = IndicatorConfig(period=momentum_period, **kwargs)
        super().__init__(config)
        self.momentum_period = momentum_period
        self.volatility_period = volatility_period
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Trend Strength Index"""
        if isinstance(data, pd.DataFrame):
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
        else:
            close = data
            high = low = close  # Fallback for price-only data
        
        # Calculate momentum component
        momentum = self._calculate_momentum_strength(close)
        
        # Calculate volatility component
        volatility = self._calculate_volatility_strength(high, low, close)
        
        # Calculate trend persistence
        persistence = self._calculate_trend_persistence(close)
        
        # Combine components into TSI
        tsi_values = np.full_like(close, np.nan)
        
        for i in range(max(self.momentum_period, self.volatility_period), len(close)):
            if (not np.isnan(momentum[i]) and 
                not np.isnan(volatility[i]) and 
                not np.isnan(persistence[i])):
                
                # Weighted combination
                tsi_values[i] = (0.4 * momentum[i] + 
                               0.3 * volatility[i] + 
                               0.3 * persistence[i])
        
        # Generate signals
        signals = self._generate_tsi_signals(tsi_values)
        
        # Determine trend
        trend = self._determine_tsi_trend(tsi_values)
        
        return IndicatorResult(
            values=tsi_values,
            signals=signals,
            trend=trend,
            strength=self._calculate_tsi_strength(tsi_values),
            confidence=self._calculate_tsi_confidence(tsi_values),
            metadata={
                'momentum': momentum,
                'volatility': volatility,
                'persistence': persistence
            }
        )
    
    def _calculate_momentum_strength(self, close: np.ndarray) -> np.ndarray:
        """Calculate momentum strength component"""
        momentum = np.full_like(close, np.nan)
        
        for i in range(self.momentum_period, len(close)):
            # Rate of change
            roc = (close[i] - close[i - self.momentum_period]) / close[i - self.momentum_period]
            
            # Normalize to 0-100 scale
            momentum[i] = min(max((roc * 100) + 50, 0), 100)
        
        return momentum
    
    def _calculate_volatility_strength(self, high: np.ndarray, low: np.ndarray, 
                                     close: np.ndarray) -> np.ndarray:
        """Calculate volatility strength component"""
        volatility = np.full_like(close, np.nan)
        
        # Calculate True Range
        tr = np.full_like(close, np.nan)
        for i in range(1, len(close)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
        
        # Calculate ATR
        atr = calculate_sma(tr, self.volatility_period)
        
        for i in range(self.volatility_period, len(close)):
            if not np.isnan(atr[i]) and close[i] != 0:
                # Volatility as percentage of price
                vol_pct = (atr[i] / close[i]) * 100
                
                # Normalize (higher volatility = lower strength for trending)
                volatility[i] = max(0, 100 - (vol_pct * 10))
        
        return volatility
    
    def _calculate_trend_persistence(self, close: np.ndarray) -> np.ndarray:
        """Calculate trend persistence component"""
        persistence = np.full_like(close, np.nan)
        
        for i in range(20, len(close)):
            # Look at recent price changes
            recent_changes = np.diff(close[i-19:i+1])
            
            if len(recent_changes) > 0:
                # Count consistent direction changes
                positive_changes = np.sum(recent_changes > 0)
                negative_changes = np.sum(recent_changes < 0)
                total_changes = len(recent_changes)
                
                # Persistence score
                max_consistent = max(positive_changes, negative_changes)
                persistence[i] = (max_consistent / total_changes) * 100
        
        return persistence
    
    def _generate_tsi_signals(self, tsi_values: np.ndarray) -> List[SignalType]:
        """Generate TSI signals"""
        signals = [SignalType.NEUTRAL] * len(tsi_values)
        
        for i in range(1, len(tsi_values)):
            if np.isnan(tsi_values[i]) or np.isnan(tsi_values[i-1]):
                continue
            
            current_tsi = tsi_values[i]
            prev_tsi = tsi_values[i-1]
            
            # Strong trend signals
            if current_tsi > 75:
                signals[i] = SignalType.STRONG_BUY
            elif current_tsi < 25:
                signals[i] = SignalType.STRONG_SELL
            
            # Trend change signals
            elif current_tsi > 50 and prev_tsi <= 50:
                signals[i] = SignalType.BUY
            elif current_tsi < 50 and prev_tsi >= 50:
                signals[i] = SignalType.SELL
            
            # Trend continuation
            elif current_tsi > 50:
                signals[i] = SignalType.BUY
            elif current_tsi < 50:
                signals[i] = SignalType.SELL
            else:
                signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_tsi_trend(self, tsi_values: np.ndarray) -> TrendDirection:
        """Determine trend based on TSI values"""
        if len(tsi_values) < 5:
            return TrendDirection.UNKNOWN
        
        recent_tsi = tsi_values[-5:]
        valid_tsi = recent_tsi[~np.isnan(recent_tsi)]
        
        if len(valid_tsi) < 3:
            return TrendDirection.UNKNOWN
        
        avg_tsi = np.mean(valid_tsi)
        
        if avg_tsi > 60:
            return TrendDirection.UPTREND
        elif avg_tsi < 40:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_tsi_strength(self, tsi_values: np.ndarray) -> float:
        """Calculate TSI strength"""
        if len(tsi_values) < 3:
            return 0.0
        
        current_tsi = tsi_values[-1]
        if np.isnan(current_tsi):
            return 0.0
        
        # Strength based on distance from neutral (50)
        strength = abs(current_tsi - 50) / 50
        return min(strength, 1.0)
    
    def _calculate_tsi_confidence(self, tsi_values: np.ndarray) -> float:
        """Calculate TSI confidence"""
        if len(tsi_values) < 5:
            return 0.5
        
        recent_tsi = tsi_values[-5:]
        valid_tsi = recent_tsi[~np.isnan(recent_tsi)]
        
        if len(valid_tsi) < 3:
            return 0.5
        
        # Confidence based on consistency
        std_dev = np.std(valid_tsi)
        mean_val = np.mean(valid_tsi)
        
        if mean_val == 0:
            return 0.5
        
        # Lower standard deviation = higher confidence
        cv = std_dev / abs(mean_val)  # Coefficient of variation
        confidence = max(0, 1 - cv)
        
        return min(confidence, 1.0)

class SupportResistanceLevels(BaseIndicator):
    """Support and Resistance Levels Detector
    
    Identifies key support and resistance levels using pivot points
    and price action analysis.
    """
    
    def __init__(self, lookback_period: int = 20, min_touches: int = 2, 
                 tolerance_pct: float = 0.5, **kwargs):
        config = IndicatorConfig(period=lookback_period, **kwargs)
        super().__init__(config)
        self.lookback_period = lookback_period
        self.min_touches = min_touches
        self.tolerance_pct = tolerance_pct / 100  # Convert to decimal
    
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate Support and Resistance Levels"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("S/R Levels require OHLC data")
        
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        # Find pivot points
        pivot_highs = self._find_pivot_highs(high)
        pivot_lows = self._find_pivot_lows(low)
        
        # Identify support and resistance levels
        support_levels = self._identify_support_levels(pivot_lows, low)
        resistance_levels = self._identify_resistance_levels(pivot_highs, high)
        
        # Calculate level strength
        level_strength = self._calculate_level_strength(close, support_levels, resistance_levels)
        
        # Generate signals
        signals = self._generate_sr_signals(close, support_levels, resistance_levels)
        
        # Determine trend
        trend = self._determine_sr_trend(close, support_levels, resistance_levels)
        
        return IndicatorResult(
            values=level_strength,
            signals=signals,
            trend=trend,
            strength=self._calculate_sr_strength(close, support_levels, resistance_levels),
            confidence=self._calculate_sr_confidence(support_levels, resistance_levels),
            metadata={
                'support_levels': support_levels,
                'resistance_levels': resistance_levels,
                'pivot_highs': pivot_highs,
                'pivot_lows': pivot_lows
            }
        )
    
    def _find_pivot_highs(self, high: np.ndarray) -> List[Tuple[int, float]]:
        """Find pivot high points"""
        pivot_highs = []
        
        for i in range(self.lookback_period, len(high) - self.lookback_period):
            is_pivot = True
            current_high = high[i]
            
            # Check if current point is higher than surrounding points
            for j in range(i - self.lookback_period, i + self.lookback_period + 1):
                if j != i and high[j] >= current_high:
                    is_pivot = False
                    break
            
            if is_pivot:
                pivot_highs.append((i, current_high))
        
        return pivot_highs
    
    def _find_pivot_lows(self, low: np.ndarray) -> List[Tuple[int, float]]:
        """Find pivot low points"""
        pivot_lows = []
        
        for i in range(self.lookback_period, len(low) - self.lookback_period):
            is_pivot = True
            current_low = low[i]
            
            # Check if current point is lower than surrounding points
            for j in range(i - self.lookback_period, i + self.lookback_period + 1):
                if j != i and low[j] <= current_low:
                    is_pivot = False
                    break
            
            if is_pivot:
                pivot_lows.append((i, current_low))
        
        return pivot_lows
    
    def _identify_support_levels(self, pivot_lows: List[Tuple[int, float]], 
                               low: np.ndarray) -> List[Dict]:
        """Identify support levels from pivot lows"""
        if not pivot_lows:
            return []
        
        support_levels = []
        
        # Group similar price levels
        for i, (idx1, price1) in enumerate(pivot_lows):
            touches = [(idx1, price1)]
            
            for j, (idx2, price2) in enumerate(pivot_lows[i+1:], i+1):
                # Check if prices are within tolerance
                if abs(price2 - price1) / price1 <= self.tolerance_pct:
                    touches.append((idx2, price2))
            
            # Only consider levels with minimum touches
            if len(touches) >= self.min_touches:
                avg_price = np.mean([price for _, price in touches])
                support_levels.append({
                    'price': avg_price,
                    'touches': len(touches),
                    'indices': [idx for idx, _ in touches],
                    'type': 'support'
                })
        
        # Remove duplicate levels
        support_levels = self._remove_duplicate_levels(support_levels)
        
        return support_levels
    
    def _identify_resistance_levels(self, pivot_highs: List[Tuple[int, float]], 
                                  high: np.ndarray) -> List[Dict]:
        """Identify resistance levels from pivot highs"""
        if not pivot_highs:
            return []
        
        resistance_levels = []
        
        # Group similar price levels
        for i, (idx1, price1) in enumerate(pivot_highs):
            touches = [(idx1, price1)]
            
            for j, (idx2, price2) in enumerate(pivot_highs[i+1:], i+1):
                # Check if prices are within tolerance
                if abs(price2 - price1) / price1 <= self.tolerance_pct:
                    touches.append((idx2, price2))
            
            # Only consider levels with minimum touches
            if len(touches) >= self.min_touches:
                avg_price = np.mean([price for _, price in touches])
                resistance_levels.append({
                    'price': avg_price,
                    'touches': len(touches),
                    'indices': [idx for idx, _ in touches],
                    'type': 'resistance'
                })
        
        # Remove duplicate levels
        resistance_levels = self._remove_duplicate_levels(resistance_levels)
        
        return resistance_levels
    
    def _remove_duplicate_levels(self, levels: List[Dict]) -> List[Dict]:
        """Remove duplicate levels that are too close to each other"""
        if not levels:
            return levels
        
        # Sort by price
        levels.sort(key=lambda x: x['price'])
        
        unique_levels = [levels[0]]
        
        for level in levels[1:]:
            # Check if this level is too close to any existing level
            is_duplicate = False
            for existing_level in unique_levels:
                price_diff = abs(level['price'] - existing_level['price'])
                if price_diff / existing_level['price'] <= self.tolerance_pct:
                    # Keep the level with more touches
                    if level['touches'] > existing_level['touches']:
                        unique_levels.remove(existing_level)
                        unique_levels.append(level)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_levels.append(level)
        
        return unique_levels
    
    def _calculate_level_strength(self, close: np.ndarray, support_levels: List[Dict], 
                                resistance_levels: List[Dict]) -> np.ndarray:
        """Calculate strength of current price relative to S/R levels"""
        strength = np.full_like(close, 50.0)  # Neutral = 50
        
        for i, price in enumerate(close):
            if np.isnan(price):
                continue
            
            # Find nearest support and resistance
            nearest_support = None
            nearest_resistance = None
            
            for level in support_levels:
                if level['price'] < price:
                    if nearest_support is None or level['price'] > nearest_support['price']:
                        nearest_support = level
            
            for level in resistance_levels:
                if level['price'] > price:
                    if nearest_resistance is None or level['price'] < nearest_resistance['price']:
                        nearest_resistance = level
            
            # Calculate strength based on position between levels
            if nearest_support and nearest_resistance:
                support_price = nearest_support['price']
                resistance_price = nearest_resistance['price']
                
                # Position within the range (0-100)
                range_position = ((price - support_price) / 
                                (resistance_price - support_price)) * 100
                strength[i] = max(0, min(100, range_position))
            
            elif nearest_support:
                # Above all resistance levels
                distance_from_support = (price - nearest_support['price']) / nearest_support['price']
                strength[i] = min(100, 50 + (distance_from_support * 100))
            
            elif nearest_resistance:
                # Below all support levels
                distance_from_resistance = (nearest_resistance['price'] - price) / nearest_resistance['price']
                strength[i] = max(0, 50 - (distance_from_resistance * 100))
        
        return strength
    
    def _generate_sr_signals(self, close: np.ndarray, support_levels: List[Dict], 
                           resistance_levels: List[Dict]) -> List[SignalType]:
        """Generate signals based on S/R levels"""
        signals = [SignalType.NEUTRAL] * len(close)
        
        for i in range(1, len(close)):
            if np.isnan(close[i]) or np.isnan(close[i-1]):
                continue
            
            current_price = close[i]
            prev_price = close[i-1]
            
            # Check for bounces off support
            for level in support_levels:
                support_price = level['price']
                tolerance = support_price * self.tolerance_pct
                
                # Bounce off support
                if (prev_price <= support_price + tolerance and 
                    current_price > support_price + tolerance):
                    signals[i] = SignalType.BUY
                    break
                
                # Break below support
                elif (prev_price >= support_price - tolerance and 
                      current_price < support_price - tolerance):
                    signals[i] = SignalType.SELL
                    break
            
            # Check for bounces off resistance
            for level in resistance_levels:
                resistance_price = level['price']
                tolerance = resistance_price * self.tolerance_pct
                
                # Bounce off resistance
                if (prev_price >= resistance_price - tolerance and 
                    current_price < resistance_price - tolerance):
                    signals[i] = SignalType.SELL
                    break
                
                # Break above resistance
                elif (prev_price <= resistance_price + tolerance and 
                      current_price > resistance_price + tolerance):
                    signals[i] = SignalType.BUY
                    break
        
        return signals
    
    def _determine_sr_trend(self, close: np.ndarray, support_levels: List[Dict], 
                          resistance_levels: List[Dict]) -> TrendDirection:
        """Determine trend based on S/R level breaks"""
        if len(close) < 10:
            return TrendDirection.UNKNOWN
        
        recent_close = close[-10:]
        current_price = close[-1]
        
        # Count recent breaks
        support_breaks = 0
        resistance_breaks = 0
        
        for level in support_levels:
            if current_price < level['price'] * (1 - self.tolerance_pct):
                support_breaks += level['touches']
        
        for level in resistance_levels:
            if current_price > level['price'] * (1 + self.tolerance_pct):
                resistance_breaks += level['touches']
        
        if resistance_breaks > support_breaks:
            return TrendDirection.UPTREND
        elif support_breaks > resistance_breaks:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_sr_strength(self, close: np.ndarray, support_levels: List[Dict], 
                             resistance_levels: List[Dict]) -> float:
        """Calculate S/R strength"""
        if len(close) == 0:
            return 0.0
        
        current_price = close[-1]
        total_levels = len(support_levels) + len(resistance_levels)
        
        if total_levels == 0:
            return 0.0
        
        # Strength based on number of nearby levels
        nearby_levels = 0
        for level in support_levels + resistance_levels:
            distance = abs(current_price - level['price']) / current_price
            if distance <= self.tolerance_pct * 2:  # Within 2x tolerance
                nearby_levels += level['touches']
        
        strength = min(nearby_levels / 10, 1.0)  # Normalize
        return strength
    
    def _calculate_sr_confidence(self, support_levels: List[Dict], 
                               resistance_levels: List[Dict]) -> float:
        """Calculate S/R confidence"""
        total_levels = len(support_levels) + len(resistance_levels)
        
        if total_levels == 0:
            return 0.0
        
        # Confidence based on average touches per level
        total_touches = sum(level['touches'] for level in support_levels + resistance_levels)
        avg_touches = total_touches / total_levels
        
        # Higher average touches = higher confidence
        confidence = min(avg_touches / 5, 1.0)  # Normalize to max 5 touches
        return confidence

# Factory function for easy indicator creation
def create_custom_indicator(indicator_type: str, **kwargs) -> BaseIndicator:
    """Factory function to create custom indicators"""
    indicators = {
        'cmo': CompositeMomentumOscillator,
        'tsi': TrendStrengthIndex,
        'sr_levels': SupportResistanceLevels,
    }
    
    if indicator_type.lower() not in indicators:
        raise ValueError(f"Unknown indicator type: {indicator_type}")
    
    return indicators[indicator_type.lower()](**kwargs)