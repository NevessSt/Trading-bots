"""Technical Indicators Module

This module provides a comprehensive collection of technical indicators for trading analysis:
- Trend indicators (SMA, EMA, MACD, etc.)
- Momentum indicators (RSI, Stochastic, etc.)
- Volatility indicators (Bollinger Bands, ATR, etc.)
- Volume indicators (OBV, VWAP, etc.)
- Custom composite indicators

All indicators are optimized for real-time trading and backtesting.
"""

from .trend_indicators import (
    SimpleMovingAverage,
    ExponentialMovingAverage,
    MACD,
    ParabolicSAR,
    IchimokuCloud,
    SuperTrend
)

from .momentum_indicators import (
    RSI,
    StochasticOscillator,
    WilliamsR,
    CommodityChannelIndex,
    MoneyFlowIndex,
    UltimateOscillator
)

from .volatility_indicators import (
    BollingerBands,
    AverageTrueRange,
    KeltnerChannels,
    DonchianChannels,
    StandardDeviation,
    VolatilityRatio
)

from .volume_indicators import (
    OnBalanceVolume,
    VWAP,
    AccumulationDistribution,
    ChaikinMoneyFlow,
    VolumeWeightedRSI,
    VolumePriceConfirmation
)

from .custom_indicators import (
    TradingSignalComposite,
    MarketRegimeDetector,
    VolatilityBreakout,
    MeanReversionSignal,
    TrendStrengthIndicator,
    RiskAdjustedMomentum
)

from .indicator_base import (
    BaseIndicator,
    IndicatorResult,
    IndicatorConfig
)

# Version info
__version__ = "1.0.0"
__author__ = "Trading Bot Team"

# Export all indicators
__all__ = [
    # Base classes
    'BaseIndicator',
    'IndicatorResult', 
    'IndicatorConfig',
    
    # Trend indicators
    'SimpleMovingAverage',
    'ExponentialMovingAverage',
    'MACD',
    'ParabolicSAR',
    'IchimokuCloud',
    'SuperTrend',
    
    # Momentum indicators
    'RSI',
    'StochasticOscillator',
    'WilliamsR',
    'CommodityChannelIndex',
    'MoneyFlowIndex',
    'UltimateOscillator',
    
    # Volatility indicators
    'BollingerBands',
    'AverageTrueRange',
    'KeltnerChannels',
    'DonchianChannels',
    'StandardDeviation',
    'VolatilityRatio',
    
    # Volume indicators
    'OnBalanceVolume',
    'VWAP',
    'AccumulationDistribution',
    'ChaikinMoneyFlow',
    'VolumeWeightedRSI',
    'VolumePriceConfirmation',
    
    # Custom indicators
    'TradingSignalComposite',
    'MarketRegimeDetector',
    'VolatilityBreakout',
    'MeanReversionSignal',
    'TrendStrengthIndicator',
    'RiskAdjustedMomentum'
]

# Quick access functions for common indicators
def get_sma(data, period=20):
    """Quick SMA calculation"""
    return SimpleMovingAverage(period=period).calculate(data)

def get_ema(data, period=20):
    """Quick EMA calculation"""
    return ExponentialMovingAverage(period=period).calculate(data)

def get_rsi(data, period=14):
    """Quick RSI calculation"""
    return RSI(period=period).calculate(data)

def get_macd(data, fast=12, slow=26, signal=9):
    """Quick MACD calculation"""
    return MACD(fast_period=fast, slow_period=slow, signal_period=signal).calculate(data)

def get_bollinger_bands(data, period=20, std_dev=2):
    """Quick Bollinger Bands calculation"""
    return BollingerBands(period=period, std_dev=std_dev).calculate(data)

# Indicator factory function
def create_indicator(indicator_type: str, **kwargs):
    """
    Factory function to create indicators by name
    
    Args:
        indicator_type: Name of the indicator
        **kwargs: Indicator parameters
        
    Returns:
        Indicator instance
    """
    indicator_map = {
        'sma': SimpleMovingAverage,
        'ema': ExponentialMovingAverage,
        'macd': MACD,
        'rsi': RSI,
        'stochastic': StochasticOscillator,
        'bollinger': BollingerBands,
        'atr': AverageTrueRange,
        'obv': OnBalanceVolume,
        'vwap': VWAP,
        'parabolic_sar': ParabolicSAR,
        'ichimoku': IchimokuCloud,
        'supertrend': SuperTrend,
        'williams_r': WilliamsR,
        'cci': CommodityChannelIndex,
        'mfi': MoneyFlowIndex,
        'keltner': KeltnerChannels,
        'donchian': DonchianChannels
    }
    
    indicator_class = indicator_map.get(indicator_type.lower())
    if not indicator_class:
        raise ValueError(f"Unknown indicator type: {indicator_type}")
    
    return indicator_class(**kwargs)

# Batch indicator calculation
def calculate_multiple_indicators(data, indicators_config):
    """
    Calculate multiple indicators at once
    
    Args:
        data: Price data
        indicators_config: Dictionary of indicator_name -> config
        
    Returns:
        Dictionary of indicator_name -> results
    """
    results = {}
    
    for name, config in indicators_config.items():
        try:
            indicator_type = config.pop('type')
            indicator = create_indicator(indicator_type, **config)
            results[name] = indicator.calculate(data)
        except Exception as e:
            print(f"Error calculating {name}: {e}")
            results[name] = None
    
    return results