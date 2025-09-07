"""Mathematical utilities for trading calculations.

This module provides mathematical functions commonly used in trading algorithms,
including statistical calculations, financial metrics, and optimization functions.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from scipy import stats, optimize
from scipy.stats import norm
import warnings
from functools import lru_cache
import math

# Type aliases
NumericType = Union[int, float, np.number]
ArrayLike = Union[List[NumericType], np.ndarray, pd.Series]

class MathError(Exception):
    """Mathematical calculation errors"""
    pass

@dataclass
class StatisticalSummary:
    """Statistical summary of a dataset"""
    mean: float
    median: float
    std: float
    variance: float
    skewness: float
    kurtosis: float
    min_value: float
    max_value: float
    q25: float
    q75: float
    count: int
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'mean': self.mean,
            'median': self.median,
            'std': self.std,
            'variance': self.variance,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis,
            'min': self.min_value,
            'max': self.max_value,
            'q25': self.q25,
            'q75': self.q75,
            'count': self.count
        }

@dataclass
class RiskMetrics:
    """Risk metrics for trading performance"""
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional Value at Risk (95%)
    beta: Optional[float] = None
    alpha: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Optional[float]]:
        """Convert to dictionary"""
        return {
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'beta': self.beta,
            'alpha': self.alpha
        }

class StatisticalCalculator:
    """Statistical calculations for trading data"""
    
    @staticmethod
    def calculate_summary(data: ArrayLike) -> StatisticalSummary:
        """Calculate comprehensive statistical summary"""
        if len(data) == 0:
            raise MathError("Cannot calculate statistics for empty dataset")
        
        data_array = np.array(data)
        
        # Remove NaN values
        clean_data = data_array[~np.isnan(data_array)]
        
        if len(clean_data) == 0:
            raise MathError("No valid data points after removing NaN values")
        
        return StatisticalSummary(
            mean=float(np.mean(clean_data)),
            median=float(np.median(clean_data)),
            std=float(np.std(clean_data, ddof=1)) if len(clean_data) > 1 else 0.0,
            variance=float(np.var(clean_data, ddof=1)) if len(clean_data) > 1 else 0.0,
            skewness=float(stats.skew(clean_data)) if len(clean_data) > 2 else 0.0,
            kurtosis=float(stats.kurtosis(clean_data)) if len(clean_data) > 3 else 0.0,
            min_value=float(np.min(clean_data)),
            max_value=float(np.max(clean_data)),
            q25=float(np.percentile(clean_data, 25)),
            q75=float(np.percentile(clean_data, 75)),
            count=len(clean_data)
        )
    
    @staticmethod
    def rolling_statistics(data: ArrayLike, window: int) -> Dict[str, np.ndarray]:
        """Calculate rolling statistics"""
        if window <= 0:
            raise MathError("Window size must be positive")
        
        series = pd.Series(data)
        
        return {
            'mean': series.rolling(window=window).mean().values,
            'std': series.rolling(window=window).std().values,
            'min': series.rolling(window=window).min().values,
            'max': series.rolling(window=window).max().values,
            'median': series.rolling(window=window).median().values
        }
    
    @staticmethod
    def correlation_matrix(data: Dict[str, ArrayLike]) -> pd.DataFrame:
        """Calculate correlation matrix for multiple series"""
        df = pd.DataFrame(data)
        return df.corr()
    
    @staticmethod
    def covariance_matrix(data: Dict[str, ArrayLike]) -> pd.DataFrame:
        """Calculate covariance matrix for multiple series"""
        df = pd.DataFrame(data)
        return df.cov()

class FinancialCalculator:
    """Financial calculations for trading"""
    
    @staticmethod
    def calculate_returns(prices: ArrayLike, method: str = 'simple') -> np.ndarray:
        """Calculate returns from price series"""
        prices_array = np.array(prices)
        
        if len(prices_array) < 2:
            raise MathError("Need at least 2 price points to calculate returns")
        
        if method == 'simple':
            returns = np.diff(prices_array) / prices_array[:-1]
        elif method == 'log':
            returns = np.diff(np.log(prices_array))
        else:
            raise MathError(f"Unknown return calculation method: {method}")
        
        return returns
    
    @staticmethod
    def calculate_cumulative_returns(returns: ArrayLike) -> np.ndarray:
        """Calculate cumulative returns"""
        returns_array = np.array(returns)
        return np.cumprod(1 + returns_array) - 1
    
    @staticmethod
    def calculate_drawdown(prices: ArrayLike) -> Tuple[np.ndarray, float]:
        """Calculate drawdown series and maximum drawdown"""
        prices_array = np.array(prices)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(prices_array)
        
        # Calculate drawdown
        drawdown = (prices_array - running_max) / running_max
        
        # Maximum drawdown
        max_drawdown = np.min(drawdown)
        
        return drawdown, abs(max_drawdown)
    
    @staticmethod
    def calculate_sharpe_ratio(returns: ArrayLike, risk_free_rate: float = 0.0, 
                             periods_per_year: int = 252) -> float:
        """Calculate Sharpe ratio"""
        returns_array = np.array(returns)
        
        if len(returns_array) == 0:
            return 0.0
        
        excess_returns = returns_array - risk_free_rate / periods_per_year
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.sqrt(periods_per_year) * np.mean(excess_returns) / np.std(excess_returns)
    
    @staticmethod
    def calculate_sortino_ratio(returns: ArrayLike, risk_free_rate: float = 0.0,
                              periods_per_year: int = 252) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        returns_array = np.array(returns)
        
        if len(returns_array) == 0:
            return 0.0
        
        excess_returns = returns_array - risk_free_rate / periods_per_year
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return float('inf') if np.mean(excess_returns) > 0 else 0.0
        
        downside_deviation = np.sqrt(np.mean(downside_returns ** 2))
        
        return np.sqrt(periods_per_year) * np.mean(excess_returns) / downside_deviation
    
    @staticmethod
    def calculate_var(returns: ArrayLike, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        returns_array = np.array(returns)
        
        if len(returns_array) == 0:
            return 0.0
        
        return np.percentile(returns_array, (1 - confidence_level) * 100)
    
    @staticmethod
    def calculate_cvar(returns: ArrayLike, confidence_level: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR)"""
        returns_array = np.array(returns)
        
        if len(returns_array) == 0:
            return 0.0
        
        var = FinancialCalculator.calculate_var(returns_array, confidence_level)
        tail_returns = returns_array[returns_array <= var]
        
        return np.mean(tail_returns) if len(tail_returns) > 0 else var
    
    @staticmethod
    def calculate_beta(asset_returns: ArrayLike, market_returns: ArrayLike) -> float:
        """Calculate beta coefficient"""
        asset_array = np.array(asset_returns)
        market_array = np.array(market_returns)
        
        if len(asset_array) != len(market_array):
            raise MathError("Asset and market returns must have same length")
        
        if len(asset_array) < 2:
            return 0.0
        
        covariance = np.cov(asset_array, market_array)[0, 1]
        market_variance = np.var(market_array)
        
        return covariance / market_variance if market_variance != 0 else 0.0
    
    @staticmethod
    def calculate_alpha(asset_returns: ArrayLike, market_returns: ArrayLike,
                      risk_free_rate: float = 0.0) -> float:
        """Calculate alpha coefficient"""
        asset_array = np.array(asset_returns)
        market_array = np.array(market_returns)
        
        if len(asset_array) != len(market_array):
            raise MathError("Asset and market returns must have same length")
        
        beta = FinancialCalculator.calculate_beta(asset_array, market_array)
        
        asset_mean = np.mean(asset_array)
        market_mean = np.mean(market_array)
        
        return asset_mean - (risk_free_rate + beta * (market_mean - risk_free_rate))

class RiskCalculator:
    """Risk calculation utilities"""
    
    @staticmethod
    def calculate_risk_metrics(returns: ArrayLike, market_returns: Optional[ArrayLike] = None,
                             risk_free_rate: float = 0.0) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        returns_array = np.array(returns)
        
        if len(returns_array) == 0:
            raise MathError("Cannot calculate risk metrics for empty returns")
        
        # Basic metrics
        volatility = np.std(returns_array) * np.sqrt(252)  # Annualized
        sharpe = FinancialCalculator.calculate_sharpe_ratio(returns_array, risk_free_rate)
        sortino = FinancialCalculator.calculate_sortino_ratio(returns_array, risk_free_rate)
        
        # Drawdown (need prices for proper calculation, using cumulative returns as proxy)
        cum_returns = FinancialCalculator.calculate_cumulative_returns(returns_array)
        _, max_dd = FinancialCalculator.calculate_drawdown(cum_returns + 1)
        
        # VaR and CVaR
        var_95 = FinancialCalculator.calculate_var(returns_array, 0.95)
        cvar_95 = FinancialCalculator.calculate_cvar(returns_array, 0.95)
        
        # Beta and Alpha (if market returns provided)
        beta = None
        alpha = None
        if market_returns is not None:
            beta = FinancialCalculator.calculate_beta(returns_array, market_returns)
            alpha = FinancialCalculator.calculate_alpha(returns_array, market_returns, risk_free_rate)
        
        return RiskMetrics(
            volatility=volatility,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            var_95=var_95,
            cvar_95=cvar_95,
            beta=beta,
            alpha=alpha
        )
    
    @staticmethod
    def calculate_portfolio_var(weights: ArrayLike, returns_matrix: np.ndarray,
                              confidence_level: float = 0.95) -> float:
        """Calculate portfolio Value at Risk"""
        weights_array = np.array(weights)
        
        if len(weights_array) != returns_matrix.shape[1]:
            raise MathError("Number of weights must match number of assets")
        
        # Portfolio returns
        portfolio_returns = np.dot(returns_matrix, weights_array)
        
        return FinancialCalculator.calculate_var(portfolio_returns, confidence_level)
    
    @staticmethod
    def calculate_portfolio_volatility(weights: ArrayLike, cov_matrix: np.ndarray) -> float:
        """Calculate portfolio volatility"""
        weights_array = np.array(weights)
        
        if len(weights_array) != cov_matrix.shape[0]:
            raise MathError("Number of weights must match covariance matrix dimensions")
        
        portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
        return np.sqrt(portfolio_variance)

class OptimizationUtils:
    """Optimization utilities for portfolio and trading strategies"""
    
    @staticmethod
    def optimize_portfolio_weights(expected_returns: ArrayLike, cov_matrix: np.ndarray,
                                 risk_aversion: float = 1.0,
                                 constraints: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Optimize portfolio weights using mean-variance optimization"""
        n_assets = len(expected_returns)
        
        if cov_matrix.shape != (n_assets, n_assets):
            raise MathError("Covariance matrix dimensions don't match number of assets")
        
        # Objective function (negative utility to minimize)
        def objective(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            return -(portfolio_return - 0.5 * risk_aversion * portfolio_variance)
        
        # Constraints
        constraints_list = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]  # Weights sum to 1
        
        if constraints:
            if 'long_only' in constraints and constraints['long_only']:
                bounds = [(0, 1) for _ in range(n_assets)]
            else:
                bounds = [(-1, 1) for _ in range(n_assets)]
            
            if 'max_weight' in constraints:
                max_weight = constraints['max_weight']
                bounds = [(0, max_weight) for _ in range(n_assets)]
        else:
            bounds = [(0, 1) for _ in range(n_assets)]
        
        # Initial guess (equal weights)
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = optimize.minimize(objective, x0, method='SLSQP',
                                 bounds=bounds, constraints=constraints_list)
        
        if not result.success:
            warnings.warn(f"Optimization failed: {result.message}")
        
        return result.x
    
    @staticmethod
    def find_efficient_frontier(expected_returns: ArrayLike, cov_matrix: np.ndarray,
                              num_points: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        """Calculate efficient frontier points"""
        n_assets = len(expected_returns)
        
        # Range of target returns
        min_return = np.min(expected_returns)
        max_return = np.max(expected_returns)
        target_returns = np.linspace(min_return, max_return, num_points)
        
        efficient_risks = []
        efficient_returns = []
        
        for target_return in target_returns:
            try:
                # Minimize risk for target return
                def objective(weights):
                    return np.dot(weights.T, np.dot(cov_matrix, weights))
                
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
                    {'type': 'eq', 'fun': lambda x: np.dot(x, expected_returns) - target_return}  # Target return
                ]
                
                bounds = [(0, 1) for _ in range(n_assets)]
                x0 = np.ones(n_assets) / n_assets
                
                result = optimize.minimize(objective, x0, method='SLSQP',
                                         bounds=bounds, constraints=constraints)
                
                if result.success:
                    risk = np.sqrt(result.fun)
                    efficient_risks.append(risk)
                    efficient_returns.append(target_return)
                    
            except Exception:
                continue
        
        return np.array(efficient_returns), np.array(efficient_risks)

class TechnicalMath:
    """Mathematical functions for technical analysis"""
    
    @staticmethod
    @lru_cache(maxsize=128)
    def sma(data: tuple, period: int) -> float:
        """Simple Moving Average (cached)"""
        if len(data) < period:
            return np.nan
        return np.mean(data[-period:])
    
    @staticmethod
    def ema(data: ArrayLike, period: int, alpha: Optional[float] = None) -> np.ndarray:
        """Exponential Moving Average"""
        data_array = np.array(data)
        
        if alpha is None:
            alpha = 2.0 / (period + 1)
        
        ema_values = np.zeros_like(data_array)
        ema_values[0] = data_array[0]
        
        for i in range(1, len(data_array)):
            ema_values[i] = alpha * data_array[i] + (1 - alpha) * ema_values[i-1]
        
        return ema_values
    
    @staticmethod
    def rsi(prices: ArrayLike, period: int = 14) -> np.ndarray:
        """Relative Strength Index"""
        prices_array = np.array(prices)
        deltas = np.diff(prices_array)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = pd.Series(gains).rolling(window=period).mean().values
        avg_losses = pd.Series(losses).rolling(window=period).mean().values
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return np.concatenate([[np.nan], rsi])
    
    @staticmethod
    def bollinger_bands(prices: ArrayLike, period: int = 20, 
                       std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands"""
        prices_series = pd.Series(prices)
        
        middle_band = prices_series.rolling(window=period).mean().values
        std = prices_series.rolling(window=period).std().values
        
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def macd(prices: ArrayLike, fast_period: int = 12, slow_period: int = 26,
            signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """MACD (Moving Average Convergence Divergence)"""
        prices_array = np.array(prices)
        
        ema_fast = TechnicalMath.ema(prices_array, fast_period)
        ema_slow = TechnicalMath.ema(prices_array, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalMath.ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram

# Utility functions for quick access
def calculate_returns(prices: ArrayLike, method: str = 'simple') -> np.ndarray:
    """Quick function to calculate returns"""
    return FinancialCalculator.calculate_returns(prices, method)

def calculate_sharpe_ratio(returns: ArrayLike, risk_free_rate: float = 0.0) -> float:
    """Quick function to calculate Sharpe ratio"""
    return FinancialCalculator.calculate_sharpe_ratio(returns, risk_free_rate)

def calculate_max_drawdown(prices: ArrayLike) -> float:
    """Quick function to calculate maximum drawdown"""
    _, max_dd = FinancialCalculator.calculate_drawdown(prices)
    return max_dd

def calculate_volatility(returns: ArrayLike, annualize: bool = True) -> float:
    """Quick function to calculate volatility"""
    vol = np.std(returns)
    return vol * np.sqrt(252) if annualize else vol

def normalize_data(data: ArrayLike, method: str = 'zscore') -> np.ndarray:
    """Normalize data using various methods"""
    data_array = np.array(data)
    
    if method == 'zscore':
        return (data_array - np.mean(data_array)) / np.std(data_array)
    elif method == 'minmax':
        min_val, max_val = np.min(data_array), np.max(data_array)
        return (data_array - min_val) / (max_val - min_val)
    elif method == 'robust':
        median = np.median(data_array)
        mad = np.median(np.abs(data_array - median))
        return (data_array - median) / mad
    else:
        raise MathError(f"Unknown normalization method: {method}")

def detect_outliers(data: ArrayLike, method: str = 'iqr', threshold: float = 1.5) -> np.ndarray:
    """Detect outliers in data"""
    data_array = np.array(data)
    
    if method == 'iqr':
        q25, q75 = np.percentile(data_array, [25, 75])
        iqr = q75 - q25
        lower_bound = q25 - threshold * iqr
        upper_bound = q75 + threshold * iqr
        return (data_array < lower_bound) | (data_array > upper_bound)
    
    elif method == 'zscore':
        z_scores = np.abs(stats.zscore(data_array))
        return z_scores > threshold
    
    elif method == 'modified_zscore':
        median = np.median(data_array)
        mad = np.median(np.abs(data_array - median))
        modified_z_scores = 0.6745 * (data_array - median) / mad
        return np.abs(modified_z_scores) > threshold
    
    else:
        raise MathError(f"Unknown outlier detection method: {method}")

# Constants
TRADING_DAYS_PER_YEAR = 252
HOURS_PER_TRADING_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60

# Mathematical constants
GOLDEN_RATIO = (1 + np.sqrt(5)) / 2
EULER_NUMBER = np.e
PI = np.pi