#!/usr/bin/env python3
"""
Advanced Strategy Engine
Multiple algorithms, machine learning integration, and dynamic optimization
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import pickle
import threading
import time
from datetime import datetime, timedelta
from collections import deque, defaultdict
import asyncio
import concurrent.futures
import statistics
import math
import warnings

# Suppress sklearn warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.svm import SVR
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, GridSearchCV
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. ML features will be limited.")

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: TA-Lib not available. Using basic technical indicators.")

class StrategyType(Enum):
    """Types of trading strategies"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"
    CUSTOM = "custom"

class SignalType(Enum):
    """Types of trading signals"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"

class OptimizationMethod(Enum):
    """Optimization methods"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    GENETIC_ALGORITHM = "genetic_algorithm"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    PARTICLE_SWARM = "particle_swarm"

@dataclass
class TradingSignal:
    """Trading signal with confidence and metadata"""
    symbol: str
    signal_type: SignalType
    confidence: float  # 0.0 to 1.0
    price: float
    quantity: float
    timestamp: datetime
    strategy_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    expiry: Optional[datetime] = None

@dataclass
class MarketData:
    """Market data point"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StrategyParameters:
    """Strategy parameters for optimization"""
    name: str
    parameters: Dict[str, Any]
    bounds: Dict[str, Tuple[float, float]]  # parameter bounds for optimization
    constraints: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceMetrics:
    """Strategy performance metrics"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float
    volatility: float
    alpha: float
    beta: float
    information_ratio: float
    calmar_ratio: float
    sortino_ratio: float
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional Value at Risk 95%

class TechnicalIndicators:
    """Technical indicators calculator"""
    
    @staticmethod
    def sma(data: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average"""
        if TALIB_AVAILABLE:
            return talib.SMA(data, timeperiod=period)
        else:
            return pd.Series(data).rolling(window=period).mean().values
    
    @staticmethod
    def ema(data: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average"""
        if TALIB_AVAILABLE:
            return talib.EMA(data, timeperiod=period)
        else:
            return pd.Series(data).ewm(span=period).mean().values
    
    @staticmethod
    def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index"""
        if TALIB_AVAILABLE:
            return talib.RSI(data, timeperiod=period)
        else:
            delta = pd.Series(data).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return (100 - (100 / (1 + rs))).values
    
    @staticmethod
    def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD indicator"""
        if TALIB_AVAILABLE:
            macd_line, signal_line, histogram = talib.MACD(data, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            return macd_line, signal_line, histogram
        else:
            ema_fast = pd.Series(data).ewm(span=fast).mean()
            ema_slow = pd.Series(data).ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            return macd_line.values, signal_line.values, histogram.values
    
    @staticmethod
    def bollinger_bands(data: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands"""
        if TALIB_AVAILABLE:
            upper, middle, lower = talib.BBANDS(data, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
            return upper, middle, lower
        else:
            sma = pd.Series(data).rolling(window=period).mean()
            std = pd.Series(data).rolling(window=period).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            return upper.values, sma.values, lower.values
    
    @staticmethod
    def stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Stochastic Oscillator"""
        if TALIB_AVAILABLE:
            k_percent, d_percent = talib.STOCH(high, low, close, fastk_period=k_period, slowk_period=d_period, slowd_period=d_period)
            return k_percent, d_percent
        else:
            lowest_low = pd.Series(low).rolling(window=k_period).min()
            highest_high = pd.Series(high).rolling(window=k_period).max()
            k_percent = 100 * ((pd.Series(close) - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=d_period).mean()
            return k_percent.values, d_percent.values
    
    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Average True Range"""
        if TALIB_AVAILABLE:
            return talib.ATR(high, low, close, timeperiod=period)
        else:
            high_low = pd.Series(high) - pd.Series(low)
            high_close = np.abs(pd.Series(high) - pd.Series(close).shift())
            low_close = np.abs(pd.Series(low) - pd.Series(close).shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return true_range.rolling(window=period).mean().values
    
    @staticmethod
    def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Average Directional Index"""
        if TALIB_AVAILABLE:
            return talib.ADX(high, low, close, timeperiod=period)
        else:
            # Simplified ADX calculation
            plus_dm = pd.Series(high).diff()
            minus_dm = -pd.Series(low).diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            tr = TechnicalIndicators.atr(high, low, close, 1)
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / pd.Series(tr).rolling(window=period).mean())
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / pd.Series(tr).rolling(window=period).mean())
            
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            return adx.values

class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.performance_metrics = {}
        self.last_signal = None
        self.position = 0.0  # Current position size
        self.entry_price = 0.0
        self.trades = []
        self.enabled = True
    
    @abstractmethod
    def generate_signal(self, market_data: List[MarketData], current_price: float) -> Optional[TradingSignal]:
        """Generate trading signal based on market data"""
        pass
    
    @abstractmethod
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Get parameter bounds for optimization"""
        pass
    
    def update_parameters(self, new_parameters: Dict[str, Any]):
        """Update strategy parameters"""
        self.parameters.update(new_parameters)
        self.logger.info(f"Updated parameters for {self.name}: {new_parameters}")
    
    def calculate_position_size(self, signal: TradingSignal, account_balance: float, risk_per_trade: float = 0.02) -> float:
        """Calculate position size based on risk management"""
        try:
            if signal.stop_loss:
                risk_amount = account_balance * risk_per_trade
                price_risk = abs(signal.price - signal.stop_loss)
                if price_risk > 0:
                    return min(signal.quantity, risk_amount / price_risk)
            return signal.quantity
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def record_trade(self, signal: TradingSignal, execution_price: float, execution_time: datetime):
        """Record executed trade"""
        trade = {
            'signal': signal,
            'execution_price': execution_price,
            'execution_time': execution_time,
            'pnl': 0.0  # Will be calculated when position is closed
        }
        self.trades.append(trade)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get strategy performance summary"""
        if not self.trades:
            return {'total_trades': 0, 'total_pnl': 0.0, 'win_rate': 0.0}
        
        total_pnl = sum(trade.get('pnl', 0.0) for trade in self.trades)
        winning_trades = sum(1 for trade in self.trades if trade.get('pnl', 0.0) > 0)
        win_rate = winning_trades / len(self.trades) if self.trades else 0.0
        
        return {
            'total_trades': len(self.trades),
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'avg_pnl_per_trade': total_pnl / len(self.trades) if self.trades else 0.0
        }

class MovingAverageCrossoverStrategy(BaseStrategy):
    """Moving Average Crossover Strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'fast_period': 10,
            'slow_period': 20,
            'min_confidence': 0.6
        }
        if parameters:
            default_params.update(parameters)
        super().__init__("MovingAverageCrossover", default_params)
    
    def generate_signal(self, market_data: List[MarketData], current_price: float) -> Optional[TradingSignal]:
        """Generate signal based on moving average crossover"""
        try:
            if len(market_data) < self.parameters['slow_period']:
                return None
            
            closes = np.array([data.close for data in market_data])
            
            fast_ma = TechnicalIndicators.sma(closes, self.parameters['fast_period'])
            slow_ma = TechnicalIndicators.sma(closes, self.parameters['slow_period'])
            
            if len(fast_ma) < 2 or len(slow_ma) < 2:
                return None
            
            # Check for crossover
            current_fast = fast_ma[-1]
            current_slow = slow_ma[-1]
            prev_fast = fast_ma[-2]
            prev_slow = slow_ma[-2]
            
            signal_type = SignalType.HOLD
            confidence = 0.0
            
            # Bullish crossover
            if prev_fast <= prev_slow and current_fast > current_slow:
                signal_type = SignalType.BUY
                confidence = min(0.8, abs(current_fast - current_slow) / current_slow)
            
            # Bearish crossover
            elif prev_fast >= prev_slow and current_fast < current_slow:
                signal_type = SignalType.SELL
                confidence = min(0.8, abs(current_fast - current_slow) / current_slow)
            
            if confidence >= self.parameters['min_confidence'] and signal_type != SignalType.HOLD:
                return TradingSignal(
                    symbol=market_data[-1].symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=current_price,
                    quantity=1.0,  # Will be adjusted by position sizing
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata={
                        'fast_ma': current_fast,
                        'slow_ma': current_slow,
                        'crossover_strength': abs(current_fast - current_slow)
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating MA crossover signal: {e}")
            return None
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'fast_period': (5, 50),
            'slow_period': (10, 100),
            'min_confidence': (0.1, 0.9)
        }

class RSIMeanReversionStrategy(BaseStrategy):
    """RSI Mean Reversion Strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'min_confidence': 0.5
        }
        if parameters:
            default_params.update(parameters)
        super().__init__("RSIMeanReversion", default_params)
    
    def generate_signal(self, market_data: List[MarketData], current_price: float) -> Optional[TradingSignal]:
        """Generate signal based on RSI mean reversion"""
        try:
            if len(market_data) < self.parameters['rsi_period'] + 1:
                return None
            
            closes = np.array([data.close for data in market_data])
            rsi = TechnicalIndicators.rsi(closes, self.parameters['rsi_period'])
            
            if len(rsi) < 1 or np.isnan(rsi[-1]):
                return None
            
            current_rsi = rsi[-1]
            signal_type = SignalType.HOLD
            confidence = 0.0
            
            # Oversold condition (buy signal)
            if current_rsi <= self.parameters['oversold_threshold']:
                signal_type = SignalType.BUY
                confidence = (self.parameters['oversold_threshold'] - current_rsi) / self.parameters['oversold_threshold']
            
            # Overbought condition (sell signal)
            elif current_rsi >= self.parameters['overbought_threshold']:
                signal_type = SignalType.SELL
                confidence = (current_rsi - self.parameters['overbought_threshold']) / (100 - self.parameters['overbought_threshold'])
            
            confidence = min(1.0, max(0.0, confidence))
            
            if confidence >= self.parameters['min_confidence'] and signal_type != SignalType.HOLD:
                return TradingSignal(
                    symbol=market_data[-1].symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=current_price,
                    quantity=1.0,
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata={
                        'rsi': current_rsi,
                        'threshold': self.parameters['oversold_threshold'] if signal_type == SignalType.BUY else self.parameters['overbought_threshold']
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating RSI signal: {e}")
            return None
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'rsi_period': (5, 30),
            'oversold_threshold': (10, 40),
            'overbought_threshold': (60, 90),
            'min_confidence': (0.1, 0.9)
        }

class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands Strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'period': 20,
            'std_dev': 2.0,
            'min_confidence': 0.5
        }
        if parameters:
            default_params.update(parameters)
        super().__init__("BollingerBands", default_params)
    
    def generate_signal(self, market_data: List[MarketData], current_price: float) -> Optional[TradingSignal]:
        """Generate signal based on Bollinger Bands"""
        try:
            if len(market_data) < self.parameters['period']:
                return None
            
            closes = np.array([data.close for data in market_data])
            upper, middle, lower = TechnicalIndicators.bollinger_bands(
                closes, self.parameters['period'], self.parameters['std_dev']
            )
            
            if len(upper) < 1 or np.isnan(upper[-1]):
                return None
            
            current_upper = upper[-1]
            current_middle = middle[-1]
            current_lower = lower[-1]
            
            signal_type = SignalType.HOLD
            confidence = 0.0
            
            # Price touches lower band (buy signal)
            if current_price <= current_lower:
                signal_type = SignalType.BUY
                confidence = min(0.9, (current_lower - current_price) / (current_middle - current_lower))
            
            # Price touches upper band (sell signal)
            elif current_price >= current_upper:
                signal_type = SignalType.SELL
                confidence = min(0.9, (current_price - current_upper) / (current_upper - current_middle))
            
            confidence = max(0.0, confidence)
            
            if confidence >= self.parameters['min_confidence'] and signal_type != SignalType.HOLD:
                return TradingSignal(
                    symbol=market_data[-1].symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=current_price,
                    quantity=1.0,
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata={
                        'upper_band': current_upper,
                        'middle_band': current_middle,
                        'lower_band': current_lower,
                        'band_width': current_upper - current_lower
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating Bollinger Bands signal: {e}")
            return None
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'period': (10, 50),
            'std_dev': (1.0, 3.0),
            'min_confidence': (0.1, 0.9)
        }

class MACDMomentumStrategy(BaseStrategy):
    """MACD Momentum Strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'min_confidence': 0.5
        }
        if parameters:
            default_params.update(parameters)
        super().__init__("MACDMomentum", default_params)
    
    def generate_signal(self, market_data: List[MarketData], current_price: float) -> Optional[TradingSignal]:
        """Generate signal based on MACD"""
        try:
            if len(market_data) < self.parameters['slow_period'] + self.parameters['signal_period']:
                return None
            
            closes = np.array([data.close for data in market_data])
            macd_line, signal_line, histogram = TechnicalIndicators.macd(
                closes, 
                self.parameters['fast_period'],
                self.parameters['slow_period'],
                self.parameters['signal_period']
            )
            
            if len(macd_line) < 2 or np.isnan(macd_line[-1]):
                return None
            
            current_macd = macd_line[-1]
            current_signal = signal_line[-1]
            prev_macd = macd_line[-2]
            prev_signal = signal_line[-2]
            
            signal_type = SignalType.HOLD
            confidence = 0.0
            
            # Bullish crossover
            if prev_macd <= prev_signal and current_macd > current_signal:
                signal_type = SignalType.BUY
                confidence = min(0.8, abs(current_macd - current_signal) / abs(current_signal) if current_signal != 0 else 0.5)
            
            # Bearish crossover
            elif prev_macd >= prev_signal and current_macd < current_signal:
                signal_type = SignalType.SELL
                confidence = min(0.8, abs(current_macd - current_signal) / abs(current_signal) if current_signal != 0 else 0.5)
            
            if confidence >= self.parameters['min_confidence'] and signal_type != SignalType.HOLD:
                return TradingSignal(
                    symbol=market_data[-1].symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=current_price,
                    quantity=1.0,
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata={
                        'macd': current_macd,
                        'signal': current_signal,
                        'histogram': histogram[-1] if len(histogram) > 0 else 0.0
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating MACD signal: {e}")
            return None
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'fast_period': (5, 20),
            'slow_period': (15, 40),
            'signal_period': (5, 15),
            'min_confidence': (0.1, 0.9)
        }

class MLPredictionStrategy(BaseStrategy):
    """Machine Learning Prediction Strategy"""
    
    def __init__(self, parameters: Dict[str, Any] = None):
        default_params = {
            'lookback_period': 50,
            'prediction_horizon': 1,
            'model_type': 'random_forest',
            'retrain_frequency': 100,  # Retrain every N data points
            'min_confidence': 0.6
        }
        if parameters:
            default_params.update(parameters)
        super().__init__("MLPrediction", default_params)
        
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.feature_columns = []
        self.data_points_since_training = 0
        self.training_data = deque(maxlen=1000)  # Keep last 1000 data points
    
    def _extract_features(self, market_data: List[MarketData]) -> Optional[np.ndarray]:
        """Extract features from market data"""
        try:
            if len(market_data) < self.parameters['lookback_period']:
                return None
            
            closes = np.array([data.close for data in market_data])
            highs = np.array([data.high for data in market_data])
            lows = np.array([data.low for data in market_data])
            volumes = np.array([data.volume for data in market_data])
            
            features = []
            
            # Price-based features
            features.extend([
                closes[-1],  # Current price
                (closes[-1] - closes[-2]) / closes[-2] if len(closes) > 1 else 0,  # Price change
                np.std(closes[-10:]) if len(closes) >= 10 else 0,  # Recent volatility
                (closes[-1] - np.min(closes[-20:])) / (np.max(closes[-20:]) - np.min(closes[-20:])) if len(closes) >= 20 else 0.5  # Price position in recent range
            ])
            
            # Technical indicators
            if len(closes) >= 20:
                sma_20 = TechnicalIndicators.sma(closes, 20)
                features.append((closes[-1] - sma_20[-1]) / sma_20[-1] if not np.isnan(sma_20[-1]) else 0)
            else:
                features.append(0)
            
            if len(closes) >= 14:
                rsi = TechnicalIndicators.rsi(closes, 14)
                features.append(rsi[-1] / 100.0 if not np.isnan(rsi[-1]) else 0.5)
            else:
                features.append(0.5)
            
            # Volume features
            features.extend([
                volumes[-1] if len(volumes) > 0 else 0,
                np.mean(volumes[-5:]) if len(volumes) >= 5 else 0
            ])
            
            # Time-based features
            current_time = market_data[-1].timestamp
            features.extend([
                current_time.hour / 24.0,
                current_time.weekday() / 6.0
            ])
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return None
    
    def _prepare_training_data(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare training data from historical market data"""
        try:
            if len(self.training_data) < self.parameters['lookback_period'] + self.parameters['prediction_horizon']:
                return None, None
            
            X, y = [], []
            
            for i in range(len(self.training_data) - self.parameters['prediction_horizon']):
                if i + self.parameters['lookback_period'] >= len(self.training_data):
                    break
                
                # Extract features for current window
                window_data = list(self.training_data)[i:i + self.parameters['lookback_period']]
                features = self._extract_features(window_data)
                
                if features is not None:
                    # Target: future price change
                    current_price = window_data[-1].close
                    future_price = list(self.training_data)[i + self.parameters['lookback_period'] + self.parameters['prediction_horizon'] - 1].close
                    price_change = (future_price - current_price) / current_price
                    
                    X.append(features.flatten())
                    y.append(price_change)
            
            if len(X) < 10:  # Need minimum samples for training
                return None, None
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            return None, None
    
    def _train_model(self, X: np.ndarray, y: np.ndarray) -> bool:
        """Train the ML model"""
        try:
            if not SKLEARN_AVAILABLE:
                self.logger.warning("Scikit-learn not available, cannot train ML model")
                return False
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Select model based on parameters
            model_type = self.parameters.get('model_type', 'random_forest')
            
            if model_type == 'random_forest':
                self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            elif model_type == 'gradient_boosting':
                self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            elif model_type == 'linear':
                self.model = LinearRegression()
            elif model_type == 'ridge':
                self.model = Ridge(alpha=1.0)
            elif model_type == 'svr':
                self.model = SVR(kernel='rbf')
            elif model_type == 'mlp':
                self.model = MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42, max_iter=500)
            else:
                self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # Train model
            self.model.fit(X_scaled, y)
            
            # Evaluate model
            y_pred = self.model.predict(X_scaled)
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            self.logger.info(f"Model trained - MSE: {mse:.6f}, R²: {r2:.4f}")
            
            self.data_points_since_training = 0
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return False
    
    def generate_signal(self, market_data: List[MarketData], current_price: float) -> Optional[TradingSignal]:
        """Generate signal based on ML prediction"""
        try:
            if not SKLEARN_AVAILABLE or len(market_data) < self.parameters['lookback_period']:
                return None
            
            # Add current data to training set
            self.training_data.extend(market_data[-1:])
            self.data_points_since_training += 1
            
            # Retrain model if needed
            if (self.model is None or 
                self.data_points_since_training >= self.parameters['retrain_frequency']):
                
                X, y = self._prepare_training_data()
                if X is not None and y is not None:
                    self._train_model(X, y)
            
            # Generate prediction
            if self.model is None or self.scaler is None:
                return None
            
            features = self._extract_features(market_data)
            if features is None:
                return None
            
            # Make prediction
            features_scaled = self.scaler.transform(features)
            predicted_change = self.model.predict(features_scaled)[0]
            
            # Convert prediction to signal
            signal_type = SignalType.HOLD
            confidence = 0.0
            
            # Determine signal based on predicted price change
            if predicted_change > 0.01:  # Predict >1% increase
                signal_type = SignalType.BUY
                confidence = min(0.9, abs(predicted_change) * 10)  # Scale confidence
            elif predicted_change < -0.01:  # Predict >1% decrease
                signal_type = SignalType.SELL
                confidence = min(0.9, abs(predicted_change) * 10)
            
            if confidence >= self.parameters['min_confidence'] and signal_type != SignalType.HOLD:
                return TradingSignal(
                    symbol=market_data[-1].symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=current_price,
                    quantity=1.0,
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata={
                        'predicted_change': predicted_change,
                        'model_type': self.parameters['model_type'],
                        'training_samples': len(self.training_data)
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating ML signal: {e}")
            return None
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'lookback_period': (20, 100),
            'prediction_horizon': (1, 10),
            'retrain_frequency': (50, 500),
            'min_confidence': (0.1, 0.9)
        }

class HybridStrategy(BaseStrategy):
    """Hybrid strategy combining multiple strategies"""
    
    def __init__(self, strategies: List[BaseStrategy], parameters: Dict[str, Any] = None):
        default_params = {
            'min_consensus': 0.6,  # Minimum consensus required
            'weight_method': 'equal',  # 'equal', 'performance', 'confidence'
            'min_confidence': 0.5
        }
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Hybrid", default_params)
        self.strategies = strategies
        self.strategy_weights = {strategy.name: 1.0 for strategy in strategies}
        self.strategy_performance = {strategy.name: 0.0 for strategy in strategies}
    
    def update_strategy_weights(self):
        """Update strategy weights based on performance"""
        try:
            if self.parameters['weight_method'] == 'performance':
                total_performance = sum(max(0.1, perf) for perf in self.strategy_performance.values())
                if total_performance > 0:
                    for strategy_name in self.strategy_weights:
                        self.strategy_weights[strategy_name] = max(0.1, self.strategy_performance[strategy_name]) / total_performance
            elif self.parameters['weight_method'] == 'equal':
                weight = 1.0 / len(self.strategies)
                for strategy_name in self.strategy_weights:
                    self.strategy_weights[strategy_name] = weight
        except Exception as e:
            self.logger.error(f"Error updating strategy weights: {e}")
    
    def generate_signal(self, market_data: List[MarketData], current_price: float) -> Optional[TradingSignal]:
        """Generate consensus signal from multiple strategies"""
        try:
            signals = []
            
            # Get signals from all strategies
            for strategy in self.strategies:
                if strategy.enabled:
                    signal = strategy.generate_signal(market_data, current_price)
                    if signal:
                        signals.append((signal, self.strategy_weights.get(strategy.name, 1.0)))
            
            if not signals:
                return None
            
            # Calculate weighted consensus
            buy_weight = 0.0
            sell_weight = 0.0
            total_weight = 0.0
            
            signal_details = []
            
            for signal, weight in signals:
                adjusted_weight = weight * signal.confidence
                total_weight += weight
                
                if signal.signal_type == SignalType.BUY:
                    buy_weight += adjusted_weight
                elif signal.signal_type == SignalType.SELL:
                    sell_weight += adjusted_weight
                
                signal_details.append({
                    'strategy': signal.strategy_name,
                    'signal': signal.signal_type.value,
                    'confidence': signal.confidence,
                    'weight': weight
                })
            
            if total_weight == 0:
                return None
            
            # Determine consensus signal
            buy_consensus = buy_weight / total_weight
            sell_consensus = sell_weight / total_weight
            
            signal_type = SignalType.HOLD
            confidence = 0.0
            
            if buy_consensus >= self.parameters['min_consensus']:
                signal_type = SignalType.BUY
                confidence = buy_consensus
            elif sell_consensus >= self.parameters['min_consensus']:
                signal_type = SignalType.SELL
                confidence = sell_consensus
            
            if confidence >= self.parameters['min_confidence'] and signal_type != SignalType.HOLD:
                return TradingSignal(
                    symbol=market_data[-1].symbol,
                    signal_type=signal_type,
                    confidence=confidence,
                    price=current_price,
                    quantity=1.0,
                    timestamp=datetime.now(),
                    strategy_name=self.name,
                    metadata={
                        'buy_consensus': buy_consensus,
                        'sell_consensus': sell_consensus,
                        'contributing_signals': signal_details,
                        'total_strategies': len(self.strategies)
                    }
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating hybrid signal: {e}")
            return None
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'min_consensus': (0.3, 0.9),
            'min_confidence': (0.1, 0.9)
        }
    
    def update_strategy_performance(self, strategy_name: str, performance: float):
        """Update individual strategy performance"""
        if strategy_name in self.strategy_performance:
            self.strategy_performance[strategy_name] = performance
            self.update_strategy_weights()

class StrategyOptimizer:
    """Strategy parameter optimizer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize_strategy(self, strategy: BaseStrategy, historical_data: List[MarketData], 
                        method: OptimizationMethod = OptimizationMethod.GRID_SEARCH,
                        optimization_metric: str = 'sharpe_ratio') -> Dict[str, Any]:
        """Optimize strategy parameters"""
        try:
            parameter_bounds = strategy.get_parameter_bounds()
            
            if method == OptimizationMethod.GRID_SEARCH:
                return self._grid_search_optimization(strategy, historical_data, parameter_bounds, optimization_metric)
            elif method == OptimizationMethod.RANDOM_SEARCH:
                return self._random_search_optimization(strategy, historical_data, parameter_bounds, optimization_metric)
            else:
                self.logger.warning(f"Optimization method {method} not implemented, using grid search")
                return self._grid_search_optimization(strategy, historical_data, parameter_bounds, optimization_metric)
                
        except Exception as e:
            self.logger.error(f"Error optimizing strategy: {e}")
            return {}
    
    def _grid_search_optimization(self, strategy: BaseStrategy, historical_data: List[MarketData],
                                parameter_bounds: Dict[str, Tuple[float, float]], 
                                optimization_metric: str) -> Dict[str, Any]:
        """Grid search optimization"""
        try:
            best_params = strategy.parameters.copy()
            best_score = float('-inf')
            results = []
            
            # Generate parameter grid (simplified for performance)
            param_grids = {}
            for param, (min_val, max_val) in parameter_bounds.items():
                if isinstance(strategy.parameters.get(param, min_val), int):
                    param_grids[param] = list(range(int(min_val), int(max_val) + 1, max(1, int((max_val - min_val) / 5))))
                else:
                    param_grids[param] = [min_val + i * (max_val - min_val) / 4 for i in range(5)]
            
            # Test parameter combinations
            param_names = list(param_grids.keys())
            
            def generate_combinations(params, index=0, current_combo=None):
                if current_combo is None:
                    current_combo = {}
                
                if index == len(params):
                    yield current_combo.copy()
                    return
                
                param_name = params[index]
                for value in param_grids[param_name]:
                    current_combo[param_name] = value
                    yield from generate_combinations(params, index + 1, current_combo)
            
            for param_combo in generate_combinations(param_names):
                # Test this parameter combination
                test_strategy = type(strategy)(param_combo)
                performance = self._evaluate_strategy_performance(test_strategy, historical_data)
                
                score = performance.get(optimization_metric, 0.0)
                results.append({
                    'parameters': param_combo.copy(),
                    'score': score,
                    'performance': performance
                })
                
                if score > best_score:
                    best_score = score
                    best_params = param_combo.copy()
            
            return {
                'best_parameters': best_params,
                'best_score': best_score,
                'optimization_results': results
            }
            
        except Exception as e:
            self.logger.error(f"Error in grid search optimization: {e}")
            return {}
    
    def _random_search_optimization(self, strategy: BaseStrategy, historical_data: List[MarketData],
                                  parameter_bounds: Dict[str, Tuple[float, float]], 
                                  optimization_metric: str, n_iterations: int = 50) -> Dict[str, Any]:
        """Random search optimization"""
        try:
            best_params = strategy.parameters.copy()
            best_score = float('-inf')
            results = []
            
            for _ in range(n_iterations):
                # Generate random parameters
                random_params = {}
                for param, (min_val, max_val) in parameter_bounds.items():
                    if isinstance(strategy.parameters.get(param, min_val), int):
                        random_params[param] = np.random.randint(int(min_val), int(max_val) + 1)
                    else:
                        random_params[param] = np.random.uniform(min_val, max_val)
                
                # Test this parameter combination
                test_strategy = type(strategy)(random_params)
                performance = self._evaluate_strategy_performance(test_strategy, historical_data)
                
                score = performance.get(optimization_metric, 0.0)
                results.append({
                    'parameters': random_params.copy(),
                    'score': score,
                    'performance': performance
                })
                
                if score > best_score:
                    best_score = score
                    best_params = random_params.copy()
            
            return {
                'best_parameters': best_params,
                'best_score': best_score,
                'optimization_results': results
            }
            
        except Exception as e:
            self.logger.error(f"Error in random search optimization: {e}")
            return {}
    
    def _evaluate_strategy_performance(self, strategy: BaseStrategy, historical_data: List[MarketData]) -> Dict[str, float]:
        """Evaluate strategy performance on historical data"""
        try:
            if len(historical_data) < 50:  # Need minimum data for evaluation
                return {'sharpe_ratio': 0.0, 'total_return': 0.0, 'max_drawdown': 0.0}
            
            returns = []
            positions = []
            current_position = 0.0
            entry_price = 0.0
            
            # Simulate trading
            for i in range(50, len(historical_data)):
                window_data = historical_data[i-50:i]
                current_price = historical_data[i].close
                
                signal = strategy.generate_signal(window_data, current_price)
                
                if signal:
                    if signal.signal_type == SignalType.BUY and current_position <= 0:
                        if current_position < 0:  # Close short position
                            trade_return = (entry_price - current_price) / entry_price
                            returns.append(trade_return)
                        
                        current_position = 1.0
                        entry_price = current_price
                    
                    elif signal.signal_type == SignalType.SELL and current_position >= 0:
                        if current_position > 0:  # Close long position
                            trade_return = (current_price - entry_price) / entry_price
                            returns.append(trade_return)
                        
                        current_position = -1.0
                        entry_price = current_price
                
                positions.append(current_position)
            
            # Calculate performance metrics
            if not returns:
                return {'sharpe_ratio': 0.0, 'total_return': 0.0, 'max_drawdown': 0.0}
            
            total_return = sum(returns)
            avg_return = statistics.mean(returns)
            return_std = statistics.stdev(returns) if len(returns) > 1 else 0.0
            
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0.0
            
            # Calculate max drawdown
            cumulative_returns = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = cumulative_returns - running_max
            max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0.0
            
            return {
                'sharpe_ratio': sharpe_ratio,
                'total_return': total_return,
                'max_drawdown': abs(max_drawdown),
                'win_rate': sum(1 for r in returns if r > 0) / len(returns),
                'avg_return': avg_return,
                'return_std': return_std,
                'total_trades': len(returns)
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating strategy performance: {e}")
            return {'sharpe_ratio': 0.0, 'total_return': 0.0, 'max_drawdown': 0.0}

class AdvancedStrategyEngine:
    """Advanced Strategy Engine coordinating multiple strategies"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        self.strategies = {}
        self.strategy_optimizer = StrategyOptimizer()
        self.market_data_buffer = defaultdict(lambda: deque(maxlen=1000))
        
        self.running = False
        self.optimization_thread = None
        self.signal_generation_thread = None
        
        self.signal_callbacks = []
        self.performance_tracker = defaultdict(list)
        
        self.lock = threading.Lock()
    
    def add_strategy(self, strategy: BaseStrategy):
        """Add strategy to engine"""
        with self.lock:
            self.strategies[strategy.name] = strategy
            self.logger.info(f"Added strategy: {strategy.name}")
    
    def remove_strategy(self, strategy_name: str):
        """Remove strategy from engine"""
        with self.lock:
            if strategy_name in self.strategies:
                del self.strategies[strategy_name]
                self.logger.info(f"Removed strategy: {strategy_name}")
    
    def add_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """Add callback for generated signals"""
        self.signal_callbacks.append(callback)
    
    def update_market_data(self, symbol: str, market_data: MarketData):
        """Update market data for symbol"""
        try:
            self.market_data_buffer[symbol].append(market_data)
            
            # Trigger signal generation for this symbol
            if self.running:
                self._generate_signals_for_symbol(symbol)
                
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
    
    def _generate_signals_for_symbol(self, symbol: str):
        """Generate signals for a specific symbol"""
        try:
            if symbol not in self.market_data_buffer or len(self.market_data_buffer[symbol]) == 0:
                return
            
            market_data = list(self.market_data_buffer[symbol])
            current_price = market_data[-1].close
            
            with self.lock:
                for strategy_name, strategy in self.strategies.items():
                    if not strategy.enabled:
                        continue
                    
                    try:
                        signal = strategy.generate_signal(market_data, current_price)
                        
                        if signal:
                            # Execute signal callbacks
                            for callback in self.signal_callbacks:
                                try:
                                    callback(signal)
                                except Exception as e:
                                    self.logger.error(f"Error in signal callback: {e}")
                            
                            self.logger.info(f"Generated signal: {strategy_name} - {signal.signal_type.value} {signal.symbol} @ {signal.price} (confidence: {signal.confidence:.2f})")
                    
                    except Exception as e:
                        self.logger.error(f"Error generating signal for strategy {strategy_name}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error generating signals for symbol {symbol}: {e}")
    
    def optimize_strategies(self, symbols: List[str] = None, lookback_days: int = 30):
        """Optimize all strategies"""
        try:
            symbols_to_optimize = symbols or list(self.market_data_buffer.keys())
            
            with self.lock:
                strategies_to_optimize = list(self.strategies.items())
            
            for strategy_name, strategy in strategies_to_optimize:
                try:
                    self.logger.info(f"Optimizing strategy: {strategy_name}")
                    
                    # Get historical data for optimization
                    optimization_data = []
                    for symbol in symbols_to_optimize:
                        if symbol in self.market_data_buffer:
                            symbol_data = list(self.market_data_buffer[symbol])
                            # Use last N days of data
                            cutoff_time = datetime.now() - timedelta(days=lookback_days)
                            recent_data = [d for d in symbol_data if d.timestamp >= cutoff_time]
                            optimization_data.extend(recent_data)
                    
                    if len(optimization_data) < 100:  # Need minimum data
                        self.logger.warning(f"Insufficient data for optimizing {strategy_name}")
                        continue
                    
                    # Optimize strategy
                    optimization_result = self.strategy_optimizer.optimize_strategy(
                        strategy, optimization_data
                    )
                    
                    if optimization_result and 'best_parameters' in optimization_result:
                        # Update strategy parameters
                        strategy.update_parameters(optimization_result['best_parameters'])
                        
                        self.logger.info(f"Optimized {strategy_name}: score={optimization_result.get('best_score', 0):.4f}")
                    
                except Exception as e:
                    self.logger.error(f"Error optimizing strategy {strategy_name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in strategy optimization: {e}")
    
    def _optimization_loop(self):
        """Periodic optimization loop"""
        while self.running:
            try:
                # Optimize strategies every hour
                self.optimize_strategies()
                time.sleep(3600)  # 1 hour
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                time.sleep(3600)
    
    def start(self):
        """Start strategy engine"""
        if self.running:
            return
        
        try:
            self.running = True
            
            # Start optimization thread
            self.optimization_thread = threading.Thread(
                target=self._optimization_loop,
                daemon=True
            )
            self.optimization_thread.start()
            
            self.logger.info("Advanced Strategy Engine started")
            
        except Exception as e:
            self.logger.error(f"Failed to start strategy engine: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop strategy engine"""
        if not self.running:
            return
        
        try:
            self.running = False
            
            self.logger.info("Advanced Strategy Engine stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping strategy engine: {e}")
    
    def get_strategy_performance(self, strategy_name: str = None) -> Dict[str, Any]:
        """Get strategy performance metrics"""
        try:
            with self.lock:
                if strategy_name:
                    if strategy_name in self.strategies:
                        return self.strategies[strategy_name].get_performance_summary()
                    else:
                        return {}
                else:
                    performance = {}
                    for name, strategy in self.strategies.items():
                        performance[name] = strategy.get_performance_summary()
                    return performance
                    
        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {e}")
            return {}
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status and statistics"""
        try:
            with self.lock:
                strategy_status = {}
                for name, strategy in self.strategies.items():
                    strategy_status[name] = {
                        'enabled': strategy.enabled,
                        'parameters': strategy.parameters,
                        'performance': strategy.get_performance_summary()
                    }
                
                return {
                    'running': self.running,
                    'total_strategies': len(self.strategies),
                    'active_strategies': sum(1 for s in self.strategies.values() if s.enabled),
                    'symbols_tracked': len(self.market_data_buffer),
                    'strategies': strategy_status,
                    'optimization_thread_alive': self.optimization_thread.is_alive() if self.optimization_thread else False
                }
                
        except Exception as e:
            self.logger.error(f"Error getting engine status: {e}")
            return {}
    
    def create_default_strategies(self) -> List[BaseStrategy]:
        """Create default strategy set"""
        try:
            strategies = [
                MovingAverageCrossoverStrategy(),
                RSIMeanReversionStrategy(),
                BollingerBandsStrategy(),
                MACDMomentumStrategy()
            ]
            
            # Add ML strategy if sklearn is available
            if SKLEARN_AVAILABLE:
                strategies.append(MLPredictionStrategy())
            
            # Create hybrid strategy
            hybrid_strategy = HybridStrategy(strategies.copy())
            strategies.append(hybrid_strategy)
            
            return strategies
            
        except Exception as e:
            self.logger.error(f"Error creating default strategies: {e}")
            return []
    
    def save_strategies(self, filepath: str):
        """Save strategy configurations to file"""
        try:
            strategy_configs = {}
            
            with self.lock:
                for name, strategy in self.strategies.items():
                    strategy_configs[name] = {
                        'class_name': strategy.__class__.__name__,
                        'parameters': strategy.parameters,
                        'enabled': strategy.enabled,
                        'performance': strategy.get_performance_summary()
                    }
            
            with open(filepath, 'w') as f:
                json.dump(strategy_configs, f, indent=2, default=str)
            
            self.logger.info(f"Saved strategy configurations to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving strategies: {e}")
    
    def load_strategies(self, filepath: str):
        """Load strategy configurations from file"""
        try:
            with open(filepath, 'r') as f:
                strategy_configs = json.load(f)
            
            # Strategy class mapping
            strategy_classes = {
                'MovingAverageCrossoverStrategy': MovingAverageCrossoverStrategy,
                'RSIMeanReversionStrategy': RSIMeanReversionStrategy,
                'BollingerBandsStrategy': BollingerBandsStrategy,
                'MACDMomentumStrategy': MACDMomentumStrategy,
                'MLPredictionStrategy': MLPredictionStrategy
            }
            
            with self.lock:
                self.strategies.clear()
                
                for name, config in strategy_configs.items():
                    class_name = config.get('class_name')
                    if class_name in strategy_classes:
                        strategy_class = strategy_classes[class_name]
                        strategy = strategy_class(config.get('parameters', {}))
                        strategy.enabled = config.get('enabled', True)
                        self.strategies[name] = strategy
            
            self.logger.info(f"Loaded {len(self.strategies)} strategies from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error loading strategies: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create strategy engine
    engine = AdvancedStrategyEngine()
    
    # Create and add default strategies
    default_strategies = engine.create_default_strategies()
    for strategy in default_strategies:
        engine.add_strategy(strategy)
    
    # Example signal callback
    def signal_handler(signal: TradingSignal):
        print(f"Signal received: {signal.strategy_name} - {signal.signal_type.value} {signal.symbol} @ {signal.price} (confidence: {signal.confidence:.2f})")
    
    engine.add_signal_callback(signal_handler)
    
    # Generate sample market data
    sample_data = []
    base_price = 100.0
    
    for i in range(100):
        # Simulate price movement
        price_change = np.random.normal(0, 0.02)  # 2% daily volatility
        base_price *= (1 + price_change)
        
        market_data = MarketData(
            symbol="BTCUSD",
            timestamp=datetime.now() - timedelta(minutes=100-i),
            open=base_price * 0.999,
            high=base_price * 1.001,
            low=base_price * 0.998,
            close=base_price,
            volume=1000 + np.random.randint(-200, 200)
        )
        
        sample_data.append(market_data)
    
    # Start engine
    engine.start()
    
    try:
        # Feed sample data
        for data in sample_data:
            engine.update_market_data("BTCUSD", data)
            time.sleep(0.1)  # Small delay to simulate real-time data
        
        # Wait a bit for processing
        time.sleep(2)
        
        # Get performance summary
        performance = engine.get_strategy_performance()
        print("\nStrategy Performance Summary:")
        for strategy_name, perf in performance.items():
            print(f"{strategy_name}: {perf}")
        
        # Get engine status
        status = engine.get_engine_status()
        print(f"\nEngine Status: {status}")
        
    finally:
        # Stop engine
        engine.stop()
    
    print("\nAdvanced Strategy Engine demonstration completed.")