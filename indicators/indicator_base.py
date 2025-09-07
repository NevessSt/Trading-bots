"""Base Indicator Classes

This module provides the foundation classes for all technical indicators:
- BaseIndicator: Abstract base class for all indicators
- IndicatorResult: Standardized result format
- IndicatorConfig: Configuration management
- Data validation and error handling
- Performance optimization utilities
"""

import logging
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Union, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Types of trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"
    NEUTRAL = "NEUTRAL"

class TrendDirection(Enum):
    """Market trend directions"""
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    SIDEWAYS = "SIDEWAYS"
    UNKNOWN = "UNKNOWN"

@dataclass
class IndicatorConfig:
    """Configuration for indicators"""
    period: int = 14
    source: str = 'close'  # 'open', 'high', 'low', 'close', 'volume'
    smoothing: Optional[str] = None  # 'sma', 'ema', 'wma'
    smoothing_period: int = 3
    min_periods: Optional[int] = None
    fill_method: str = 'forward'  # 'forward', 'backward', 'interpolate'
    normalize: bool = False
    scale_factor: float = 1.0
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IndicatorResult:
    """Standardized result format for all indicators"""
    values: Union[np.ndarray, pd.Series, List[float]]
    signals: Optional[List[SignalType]] = None
    trend: Optional[TrendDirection] = None
    strength: Optional[float] = None  # Signal strength 0-1
    confidence: Optional[float] = None  # Confidence level 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate and process result data"""
        if isinstance(self.values, list):
            self.values = np.array(self.values)
        elif isinstance(self.values, pd.Series):
            self.values = self.values.values
    
    def get_latest_value(self) -> Optional[float]:
        """Get the most recent indicator value"""
        if len(self.values) > 0 and not np.isnan(self.values[-1]):
            return float(self.values[-1])
        return None
    
    def get_latest_signal(self) -> Optional[SignalType]:
        """Get the most recent signal"""
        if self.signals and len(self.signals) > 0:
            return self.signals[-1]
        return None
    
    def is_bullish(self) -> bool:
        """Check if latest signal is bullish"""
        latest_signal = self.get_latest_signal()
        return latest_signal in [SignalType.BUY, SignalType.STRONG_BUY]
    
    def is_bearish(self) -> bool:
        """Check if latest signal is bearish"""
        latest_signal = self.get_latest_signal()
        return latest_signal in [SignalType.SELL, SignalType.STRONG_SELL]

class BaseIndicator(ABC):
    """Abstract base class for all technical indicators
    
    This class provides the foundation for implementing technical indicators
    with standardized interfaces, data validation, and performance optimization.
    """
    
    def __init__(self, config: Optional[IndicatorConfig] = None, **kwargs):
        """
        Initialize the indicator
        
        Args:
            config: Indicator configuration
            **kwargs: Additional parameters that override config
        """
        self.config = config or IndicatorConfig()
        
        # Override config with kwargs
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                self.config.custom_params[key] = value
        
        # Indicator metadata
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.last_calculation = None
        self.calculation_count = 0
        
        # Performance tracking
        self.calculation_times = []
        self.cache = {}
        self.cache_enabled = True
        
        # Validation
        self._validate_config()
        
        logger.debug(f"Initialized {self.name} indicator")
    
    def _validate_config(self):
        """Validate indicator configuration"""
        if self.config.period <= 0:
            raise ValueError(f"Period must be positive, got {self.config.period}")
        
        if self.config.source not in ['open', 'high', 'low', 'close', 'volume']:
            raise ValueError(f"Invalid source: {self.config.source}")
        
        if self.config.smoothing and self.config.smoothing not in ['sma', 'ema', 'wma']:
            raise ValueError(f"Invalid smoothing method: {self.config.smoothing}")
    
    @abstractmethod
    def _calculate(self, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Calculate the indicator values
        
        This method must be implemented by all indicator subclasses.
        
        Args:
            data: Price/volume data
            
        Returns:
            IndicatorResult with calculated values
        """
        pass
    
    def calculate(self, data: Union[np.ndarray, pd.DataFrame, List[float]]) -> IndicatorResult:
        """Public interface for calculating indicator
        
        Args:
            data: Price/volume data
            
        Returns:
            IndicatorResult with calculated values and signals
        """
        start_time = datetime.utcnow()
        
        try:
            # Data preprocessing
            processed_data = self._preprocess_data(data)
            
            # Check cache
            cache_key = self._get_cache_key(processed_data)
            if self.cache_enabled and cache_key in self.cache:
                logger.debug(f"{self.name}: Using cached result")
                return self.cache[cache_key]
            
            # Validate data
            self._validate_data(processed_data)
            
            # Calculate indicator
            result = self._calculate(processed_data)
            
            # Post-process result
            result = self._postprocess_result(result, processed_data)
            
            # Cache result
            if self.cache_enabled:
                self.cache[cache_key] = result
                # Limit cache size
                if len(self.cache) > 100:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
            
            # Update metadata
            self.last_calculation = datetime.utcnow()
            self.calculation_count += 1
            
            # Track performance
            calculation_time = (datetime.utcnow() - start_time).total_seconds()
            self.calculation_times.append(calculation_time)
            if len(self.calculation_times) > 100:
                self.calculation_times = self.calculation_times[-100:]
            
            logger.debug(f"{self.name}: Calculation completed in {calculation_time:.4f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise
    
    def _preprocess_data(self, data: Union[np.ndarray, pd.DataFrame, List[float]]) -> Union[np.ndarray, pd.DataFrame]:
        """Preprocess input data
        
        Args:
            data: Raw input data
            
        Returns:
            Processed data ready for calculation
        """
        # Convert to appropriate format
        if isinstance(data, list):
            data = np.array(data)
        elif isinstance(data, pd.Series):
            data = data.to_frame() if len(data.shape) == 1 else data
        
        # Handle DataFrame
        if isinstance(data, pd.DataFrame):
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close']
            if not all(col in data.columns for col in required_columns):
                if len(data.columns) == 1:
                    # Single column data, assume it's close price
                    data = data.iloc[:, 0].values
                else:
                    raise ValueError(f"DataFrame must contain columns: {required_columns}")
        
        # Handle missing values
        if isinstance(data, np.ndarray):
            if np.any(np.isnan(data)):
                if self.config.fill_method == 'forward':
                    data = pd.Series(data).fillna(method='ffill').values
                elif self.config.fill_method == 'backward':
                    data = pd.Series(data).fillna(method='bfill').values
                elif self.config.fill_method == 'interpolate':
                    data = pd.Series(data).interpolate().values
        
        return data
    
    def _validate_data(self, data: Union[np.ndarray, pd.DataFrame]):
        """Validate input data
        
        Args:
            data: Preprocessed data
        """
        if isinstance(data, np.ndarray):
            if len(data) == 0:
                raise ValueError("Data array is empty")
            
            min_periods = self.config.min_periods or self.config.period
            if len(data) < min_periods:
                raise ValueError(f"Insufficient data: need at least {min_periods} periods, got {len(data)}")
        
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                raise ValueError("DataFrame is empty")
            
            min_periods = self.config.min_periods or self.config.period
            if len(data) < min_periods:
                raise ValueError(f"Insufficient data: need at least {min_periods} periods, got {len(data)}")
    
    def _postprocess_result(self, result: IndicatorResult, data: Union[np.ndarray, pd.DataFrame]) -> IndicatorResult:
        """Post-process calculation result
        
        Args:
            result: Raw calculation result
            data: Original input data
            
        Returns:
            Post-processed result
        """
        # Apply smoothing if configured
        if self.config.smoothing and len(result.values) > self.config.smoothing_period:
            if self.config.smoothing == 'sma':
                result.values = self._apply_sma_smoothing(result.values)
            elif self.config.smoothing == 'ema':
                result.values = self._apply_ema_smoothing(result.values)
            elif self.config.smoothing == 'wma':
                result.values = self._apply_wma_smoothing(result.values)
        
        # Apply normalization if configured
        if self.config.normalize:
            result.values = self._normalize_values(result.values)
        
        # Apply scale factor
        if self.config.scale_factor != 1.0:
            result.values = result.values * self.config.scale_factor
        
        # Generate signals if not already present
        if result.signals is None:
            result.signals = self._generate_signals(result.values, data)
        
        # Calculate trend if not already present
        if result.trend is None:
            result.trend = self._determine_trend(result.values)
        
        # Add metadata
        result.metadata.update({
            'indicator_name': self.name,
            'config': self.config.__dict__,
            'data_length': len(data) if isinstance(data, (np.ndarray, pd.DataFrame)) else 0,
            'calculation_time': self.calculation_times[-1] if self.calculation_times else 0
        })
        
        return result
    
    def _apply_sma_smoothing(self, values: np.ndarray) -> np.ndarray:
        """Apply Simple Moving Average smoothing"""
        period = self.config.smoothing_period
        smoothed = np.full_like(values, np.nan)
        
        for i in range(period - 1, len(values)):
            smoothed[i] = np.mean(values[i - period + 1:i + 1])
        
        return smoothed
    
    def _apply_ema_smoothing(self, values: np.ndarray) -> np.ndarray:
        """Apply Exponential Moving Average smoothing"""
        period = self.config.smoothing_period
        alpha = 2.0 / (period + 1)
        smoothed = np.full_like(values, np.nan)
        
        # Initialize with first valid value
        first_valid_idx = np.where(~np.isnan(values))[0]
        if len(first_valid_idx) == 0:
            return smoothed
        
        smoothed[first_valid_idx[0]] = values[first_valid_idx[0]]
        
        for i in range(first_valid_idx[0] + 1, len(values)):
            if not np.isnan(values[i]):
                if np.isnan(smoothed[i - 1]):
                    smoothed[i] = values[i]
                else:
                    smoothed[i] = alpha * values[i] + (1 - alpha) * smoothed[i - 1]
        
        return smoothed
    
    def _apply_wma_smoothing(self, values: np.ndarray) -> np.ndarray:
        """Apply Weighted Moving Average smoothing"""
        period = self.config.smoothing_period
        weights = np.arange(1, period + 1)
        weights = weights / weights.sum()
        
        smoothed = np.full_like(values, np.nan)
        
        for i in range(period - 1, len(values)):
            smoothed[i] = np.sum(values[i - period + 1:i + 1] * weights)
        
        return smoothed
    
    def _normalize_values(self, values: np.ndarray) -> np.ndarray:
        """Normalize values to 0-1 range"""
        valid_values = values[~np.isnan(values)]
        if len(valid_values) == 0:
            return values
        
        min_val = np.min(valid_values)
        max_val = np.max(valid_values)
        
        if max_val == min_val:
            return np.full_like(values, 0.5)
        
        return (values - min_val) / (max_val - min_val)
    
    def _generate_signals(self, values: np.ndarray, data: Union[np.ndarray, pd.DataFrame]) -> List[SignalType]:
        """Generate basic trading signals
        
        This is a default implementation that can be overridden by subclasses.
        
        Args:
            values: Indicator values
            data: Original price data
            
        Returns:
            List of trading signals
        """
        signals = [SignalType.NEUTRAL] * len(values)
        
        # Simple momentum-based signals
        for i in range(1, len(values)):
            if not np.isnan(values[i]) and not np.isnan(values[i-1]):
                if values[i] > values[i-1]:
                    signals[i] = SignalType.BUY
                elif values[i] < values[i-1]:
                    signals[i] = SignalType.SELL
                else:
                    signals[i] = SignalType.HOLD
        
        return signals
    
    def _determine_trend(self, values: np.ndarray) -> TrendDirection:
        """Determine overall trend direction
        
        Args:
            values: Indicator values
            
        Returns:
            Trend direction
        """
        if len(values) < 3:
            return TrendDirection.UNKNOWN
        
        # Use last few values to determine trend
        recent_values = values[-min(10, len(values)):]
        valid_values = recent_values[~np.isnan(recent_values)]
        
        if len(valid_values) < 2:
            return TrendDirection.UNKNOWN
        
        # Simple linear trend
        x = np.arange(len(valid_values))
        slope = np.polyfit(x, valid_values, 1)[0]
        
        if slope > 0.001:  # Threshold for uptrend
            return TrendDirection.UPTREND
        elif slope < -0.001:  # Threshold for downtrend
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _get_cache_key(self, data: Union[np.ndarray, pd.DataFrame]) -> str:
        """Generate cache key for data
        
        Args:
            data: Input data
            
        Returns:
            Cache key string
        """
        if isinstance(data, np.ndarray):
            data_hash = hash(data.tobytes()) if len(data) > 0 else 0
        else:
            data_hash = hash(str(data.values.tobytes())) if not data.empty else 0
        
        config_hash = hash(str(sorted(self.config.__dict__.items())))
        
        return f"{self.name}_{data_hash}_{config_hash}"
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.calculation_times:
            return {}
        
        return {
            'calculation_count': self.calculation_count,
            'avg_calculation_time': np.mean(self.calculation_times),
            'min_calculation_time': np.min(self.calculation_times),
            'max_calculation_time': np.max(self.calculation_times),
            'last_calculation': self.last_calculation,
            'cache_size': len(self.cache)
        }
    
    def reset_cache(self):
        """Clear the calculation cache"""
        self.cache.clear()
        logger.debug(f"{self.name}: Cache cleared")
    
    def __str__(self) -> str:
        return f"{self.name}(period={self.config.period}, source={self.config.source})"
    
    def __repr__(self) -> str:
        return self.__str__()

# Utility functions for common calculations
def calculate_sma(data: np.ndarray, period: int) -> np.ndarray:
    """Calculate Simple Moving Average"""
    result = np.full_like(data, np.nan, dtype=float)
    for i in range(period - 1, len(data)):
        result[i] = np.mean(data[i - period + 1:i + 1])
    return result

def calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
    """Calculate Exponential Moving Average"""
    alpha = 2.0 / (period + 1)
    result = np.full_like(data, np.nan, dtype=float)
    
    # Initialize with first value
    result[0] = data[0]
    
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    
    return result

def calculate_std(data: np.ndarray, period: int) -> np.ndarray:
    """Calculate rolling standard deviation"""
    result = np.full_like(data, np.nan, dtype=float)
    for i in range(period - 1, len(data)):
        result[i] = np.std(data[i - period + 1:i + 1], ddof=1)
    return result

def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Calculate True Range"""
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    
    # Set first value
    tr2[0] = tr1[0]
    tr3[0] = tr1[0]
    
    return np.maximum(tr1, np.maximum(tr2, tr3))