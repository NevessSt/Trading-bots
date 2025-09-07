"""Utils Module

This module provides utility functions and helpers for the trading bot:
- Data processing and validation
- Mathematical calculations
- Configuration management
- Logging and monitoring
- Security utilities
- Performance optimization
- Error handling

All utilities are designed to be reusable across different components.
"""

# Import core utilities
from .data_utils import (
    DataProcessor,
    DataValidator,
    PriceDataCleaner,
    TimeSeriesResampler,
    validate_ohlc_data,
    clean_price_data,
    resample_data,
    calculate_returns,
    normalize_data
)

from .math_utils import (
    MathUtils,
    StatisticalAnalyzer,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_volatility,
    calculate_correlation,
    calculate_beta,
    rolling_statistics,
    percentile_rank,
    z_score_normalize
)

from .config_utils import (
    ConfigManager,
    EnvironmentManager,
    load_config,
    save_config,
    get_env_variable,
    validate_config,
    merge_configs,
    setup_logging_config
)

from .performance_utils import (
    PerformanceTracker,
    MemoryProfiler,
    ExecutionTimer,
    CacheManager,
    profile_function,
    measure_execution_time,
    optimize_dataframe,
    batch_process
)

from .security_utils import (
    SecurityManager,
    APIKeyManager,
    EncryptionHelper,
    hash_password,
    verify_password,
    encrypt_data,
    decrypt_data,
    generate_api_key,
    validate_api_key
)

from .error_utils import (
    ErrorHandler,
    RetryManager,
    CircuitBreaker,
    handle_api_error,
    retry_with_backoff,
    log_error,
    create_error_report,
    safe_execute
)

# Version info
__version__ = '1.0.0'
__author__ = 'Trading Bot Team'

# Quick access functions
def quick_data_validation(data, data_type='ohlc'):
    """Quick data validation function"""
    validator = DataValidator()
    return validator.validate(data, data_type)

def quick_performance_metrics(returns):
    """Quick performance metrics calculation"""
    analyzer = StatisticalAnalyzer()
    return analyzer.calculate_performance_metrics(returns)

def quick_config_setup(config_path=None):
    """Quick configuration setup"""
    manager = ConfigManager()
    return manager.load_config(config_path)

def quick_error_handling(func, *args, **kwargs):
    """Quick error handling wrapper"""
    handler = ErrorHandler()
    return handler.safe_execute(func, *args, **kwargs)

# Utility constants
COMMON_TIMEFRAMES = {
    '1m': '1T',
    '5m': '5T', 
    '15m': '15T',
    '30m': '30T',
    '1h': '1H',
    '4h': '4H',
    '1d': '1D',
    '1w': '1W',
    '1M': '1M'
}

COMMON_INDICATORS = {
    'sma': 'Simple Moving Average',
    'ema': 'Exponential Moving Average',
    'rsi': 'Relative Strength Index',
    'macd': 'Moving Average Convergence Divergence',
    'bb': 'Bollinger Bands',
    'stoch': 'Stochastic Oscillator'
}

RISK_LEVELS = {
    'conservative': {'max_position_size': 0.02, 'max_drawdown': 0.05},
    'moderate': {'max_position_size': 0.05, 'max_drawdown': 0.10},
    'aggressive': {'max_position_size': 0.10, 'max_drawdown': 0.20}
}

# Export all utilities
__all__ = [
    # Data utilities
    'DataProcessor', 'DataValidator', 'PriceDataCleaner', 'TimeSeriesResampler',
    'validate_ohlc_data', 'clean_price_data', 'resample_data', 'calculate_returns', 'normalize_data',
    
    # Math utilities
    'MathUtils', 'StatisticalAnalyzer', 'calculate_sharpe_ratio', 'calculate_max_drawdown',
    'calculate_volatility', 'calculate_correlation', 'calculate_beta', 'rolling_statistics',
    'percentile_rank', 'z_score_normalize',
    
    # Config utilities
    'ConfigManager', 'EnvironmentManager', 'load_config', 'save_config', 'get_env_variable',
    'validate_config', 'merge_configs', 'setup_logging_config',
    
    # Performance utilities
    'PerformanceTracker', 'MemoryProfiler', 'ExecutionTimer', 'CacheManager',
    'profile_function', 'measure_execution_time', 'optimize_dataframe', 'batch_process',
    
    # Security utilities
    'SecurityManager', 'APIKeyManager', 'EncryptionHelper', 'hash_password', 'verify_password',
    'encrypt_data', 'decrypt_data', 'generate_api_key', 'validate_api_key',
    
    # Error utilities
    'ErrorHandler', 'RetryManager', 'CircuitBreaker', 'handle_api_error', 'retry_with_backoff',
    'log_error', 'create_error_report', 'safe_execute',
    
    # Quick access functions
    'quick_data_validation', 'quick_performance_metrics', 'quick_config_setup', 'quick_error_handling',
    
    # Constants
    'COMMON_TIMEFRAMES', 'COMMON_INDICATORS', 'RISK_LEVELS'
]