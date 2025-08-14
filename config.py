import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import timedelta

# Environment Configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development, staging, production
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
TESTING = os.getenv('TESTING', 'False').lower() == 'true'

# Security Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'max_overflow': 0
}

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# Exchange API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'

COINBASE_API_KEY = os.getenv('COINBASE_API_KEY', '')
COINBASE_SECRET_KEY = os.getenv('COINBASE_SECRET_KEY', '')
COINBASE_PASSPHRASE = os.getenv('COINBASE_PASSPHRASE', '')
COINBASE_SANDBOX = os.getenv('COINBASE_SANDBOX', 'True').lower() == 'true'

KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY', '')
KRAKEN_SECRET_KEY = os.getenv('KRAKEN_SECRET_KEY', '')

# Trading Configuration
DEFAULT_TRADING_PAIR = os.getenv('DEFAULT_TRADING_PAIR', 'BTCUSDT')
DEFAULT_TIMEFRAME = os.getenv('DEFAULT_TIMEFRAME', '1h')
MAX_CONCURRENT_BOTS = int(os.getenv('MAX_CONCURRENT_BOTS', '10'))
DEFAULT_POSITION_SIZE = float(os.getenv('DEFAULT_POSITION_SIZE', '100.0'))
MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '10000.0'))
MIN_POSITION_SIZE = float(os.getenv('MIN_POSITION_SIZE', '10.0'))

# Risk Management
MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '1000.0'))
MAX_DRAWDOWN = float(os.getenv('MAX_DRAWDOWN', '0.20'))  # 20%
DEFAULT_STOP_LOSS = float(os.getenv('DEFAULT_STOP_LOSS', '0.02'))  # 2%
DEFAULT_TAKE_PROFIT = float(os.getenv('DEFAULT_TAKE_PROFIT', '0.04'))  # 4%
MAX_LEVERAGE = float(os.getenv('MAX_LEVERAGE', '3.0'))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.getenv('LOG_FILE', 'logs/trading_bot.log')
MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', '10485760'))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

# Flask Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_THREADED = True

# WebSocket Configuration
WEBSOCKET_PING_INTERVAL = int(os.getenv('WEBSOCKET_PING_INTERVAL', '20'))
WEBSOCKET_PING_TIMEOUT = int(os.getenv('WEBSOCKET_PING_TIMEOUT', '10'))
WEBSOCKET_CLOSE_TIMEOUT = int(os.getenv('WEBSOCKET_CLOSE_TIMEOUT', '10'))

# Rate Limiting
RATE_LIMIT_STORAGE_URL = REDIS_URL
RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100 per hour')
RATE_LIMIT_API = os.getenv('RATE_LIMIT_API', '1000 per hour')

# Caching Configuration
CACHE_TYPE = os.getenv('CACHE_TYPE', 'redis')
CACHE_REDIS_URL = REDIS_URL
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))  # 5 minutes

# Email Configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

# Notification Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#trading-alerts')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Monitoring Configuration
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', '8000'))
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))  # seconds

# Backup Configuration
BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'True').lower() == 'true'
BACKUP_INTERVAL = int(os.getenv('BACKUP_INTERVAL', '3600'))  # 1 hour
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'trading-bot-backups')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# License Configuration
LICENSE_KEY = os.getenv('LICENSE_KEY', '')
LICENSE_SERVER_URL = os.getenv('LICENSE_SERVER_URL', 'https://api.tradingbot.com/license')
LICENSE_CHECK_INTERVAL = int(os.getenv('LICENSE_CHECK_INTERVAL', '86400'))  # 24 hours

# Performance Configuration
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
WORKER_TIMEOUT = int(os.getenv('WORKER_TIMEOUT', '30'))
KEEP_ALIVE = int(os.getenv('KEEP_ALIVE', '2'))

# Data Configuration
DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', '365'))
CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', '86400'))  # 24 hours
MAX_CANDLES_FETCH = int(os.getenv('MAX_CANDLES_FETCH', '1000'))

# Strategy Configuration
STRATEGY_UPDATE_INTERVAL = int(os.getenv('STRATEGY_UPDATE_INTERVAL', '60'))  # seconds
BACKTEST_MAX_DAYS = int(os.getenv('BACKTEST_MAX_DAYS', '365'))
OPTIMIZATION_MAX_ITERATIONS = int(os.getenv('OPTIMIZATION_MAX_ITERATIONS', '100'))

# API Configuration
API_VERSION = os.getenv('API_VERSION', 'v1')
API_TITLE = os.getenv('API_TITLE', 'TradingBot Pro API')
API_DESCRIPTION = os.getenv('API_DESCRIPTION', 'Professional Trading Bot API')
API_DOCS_URL = os.getenv('API_DOCS_URL', '/docs')
API_REDOC_URL = os.getenv('API_REDOC_URL', '/redoc')

# CORS Configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
CORS_HEADERS = ['Content-Type', 'Authorization']

# Session Configuration
SESSION_TYPE = 'redis'
SESSION_REDIS = None  # Will be set in app initialization
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_KEY_PREFIX = 'tradingbot:'
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

# File Upload Configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx'}

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Default Strategy Parameters
DEFAULT_STRATEGY_PARAMS = {
    'rsi': {
        'period': 14,
        'overbought': 70,
        'oversold': 30,
        'position_size': 100.0,
        'stop_loss': 0.02,
        'take_profit': 0.04
    },
    'macd': {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9,
        'position_size': 100.0,
        'stop_loss': 0.02,
        'take_profit': 0.04
    },
    'ema_crossover': {
        'fast_period': 10,
        'slow_period': 20,
        'position_size': 100.0,
        'stop_loss': 0.02,
        'take_profit': 0.04
    },
    'advanced_grid': {
        'grid_levels': 10,
        'grid_spacing': 0.01,
        'base_order_size': 100.0,
        'safety_order_size': 150.0,
        'take_profit': 0.02,
        'stop_loss': 0.05,
        'max_safety_orders': 5
    },
    'smart_dca': {
        'base_order_amount': 100.0,
        'safety_order_amount': 150.0,
        'price_deviation': 0.02,
        'take_profit': 0.03,
        'stop_loss': 0.10,
        'max_safety_orders': 10,
        'cooldown_period': 300
    },
    'advanced_scalping': {
        'rsi_period': 14,
        'rsi_overbought': 80,
        'rsi_oversold': 20,
        'ema_fast': 5,
        'ema_slow': 10,
        'volume_threshold': 1.5,
        'volatility_threshold': 0.01,
        'profit_target': 0.005,
        'stop_loss': 0.003,
        'max_holding_time': 300
    }
}

# Risk Management Profiles
RISK_PROFILES = {
    'conservative': {
        'max_position_size': 50.0,
        'max_daily_loss': 100.0,
        'max_drawdown': 0.05,
        'stop_loss': 0.01,
        'take_profit': 0.02,
        'max_leverage': 1.0
    },
    'moderate': {
        'max_position_size': 200.0,
        'max_daily_loss': 500.0,
        'max_drawdown': 0.10,
        'stop_loss': 0.02,
        'take_profit': 0.04,
        'max_leverage': 2.0
    },
    'aggressive': {
        'max_position_size': 1000.0,
        'max_daily_loss': 2000.0,
        'max_drawdown': 0.20,
        'stop_loss': 0.03,
        'take_profit': 0.06,
        'max_leverage': 5.0
    }
}

# Exchange Configuration
EXCHANGE_CONFIG = {
    'binance': {
        'api_key': BINANCE_API_KEY,
        'secret': BINANCE_SECRET_KEY,
        'sandbox': BINANCE_TESTNET,
        'rate_limit': 1200,  # requests per minute
        'timeout': 30000,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',  # spot, margin, future
            'adjustForTimeDifference': True
        }
    },
    'coinbase': {
        'api_key': COINBASE_API_KEY,
        'secret': COINBASE_SECRET_KEY,
        'passphrase': COINBASE_PASSPHRASE,
        'sandbox': COINBASE_SANDBOX,
        'rate_limit': 10,  # requests per second
        'timeout': 30000,
        'enableRateLimit': True
    },
    'kraken': {
        'api_key': KRAKEN_API_KEY,
        'secret': KRAKEN_SECRET_KEY,
        'rate_limit': 60,  # requests per minute
        'timeout': 30000,
        'enableRateLimit': True
    }
}

# Supported Trading Pairs
SUPPORTED_PAIRS = {
    'binance': [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
        'XRPUSDT', 'LTCUSDT', 'LINKUSDT', 'BCHUSDT', 'XLMUSDT',
        'UNIUSDT', 'VETUSDT', 'FILUSDT', 'TRXUSDT', 'EOSUSDT',
        'ATOMUSDT', 'MKRUSDT', 'COMPUSDT', 'YFIUSDT', 'SNXUSDT'
    ],
    'coinbase': [
        'BTC-USD', 'ETH-USD', 'LTC-USD', 'BCH-USD', 'XRP-USD',
        'ADA-USD', 'DOT-USD', 'LINK-USD', 'UNI-USD', 'COMP-USD'
    ],
    'kraken': [
        'XBTUSD', 'ETHUSD', 'LTCUSD', 'BCHUSD', 'XRPUSD',
        'ADAUSD', 'DOTUSD', 'LINKUSD', 'UNIUSD', 'COMPUSD'
    ]
}

# Timeframes
SUPPORTED_TIMEFRAMES = {
    '1m': 60,
    '3m': 180,
    '5m': 300,
    '15m': 900,
    '30m': 1800,
    '1h': 3600,
    '2h': 7200,
    '4h': 14400,
    '6h': 21600,
    '8h': 28800,
    '12h': 43200,
    '1d': 86400,
    '3d': 259200,
    '1w': 604800,
    '1M': 2592000
}

# Technical Indicators Configuration
INDICATOR_CONFIG = {
    'sma': {'periods': [10, 20, 50, 100, 200]},
    'ema': {'periods': [10, 20, 50, 100, 200]},
    'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'bollinger_bands': {'period': 20, 'std_dev': 2},
    'stochastic': {'k_period': 14, 'd_period': 3},
    'williams_r': {'period': 14},
    'atr': {'period': 14},
    'adx': {'period': 14},
    'cci': {'period': 20}
}

# Machine Learning Configuration
ML_CONFIG = {
    'enabled': os.getenv('ML_ENABLED', 'False').lower() == 'true',
    'model_update_interval': int(os.getenv('ML_MODEL_UPDATE_INTERVAL', '86400')),  # 24 hours
    'training_data_days': int(os.getenv('ML_TRAINING_DATA_DAYS', '90')),
    'prediction_horizon': int(os.getenv('ML_PREDICTION_HORIZON', '24')),  # hours
    'feature_engineering': {
        'technical_indicators': True,
        'price_patterns': True,
        'volume_analysis': True,
        'sentiment_analysis': False
    },
    'models': {
        'xgboost': {'enabled': True, 'params': {'n_estimators': 100, 'max_depth': 6}},
        'lightgbm': {'enabled': True, 'params': {'n_estimators': 100, 'max_depth': 6}},
        'neural_network': {'enabled': False, 'params': {'hidden_layers': [64, 32], 'epochs': 100}}
    }
}

# Portfolio Optimization Configuration
PORTFOLIO_CONFIG = {
    'rebalance_frequency': os.getenv('PORTFOLIO_REBALANCE_FREQUENCY', 'daily'),  # daily, weekly, monthly
    'optimization_method': os.getenv('PORTFOLIO_OPTIMIZATION_METHOD', 'max_sharpe'),  # max_sharpe, min_variance, max_return
    'risk_free_rate': float(os.getenv('PORTFOLIO_RISK_FREE_RATE', '0.02')),  # 2% annual
    'lookback_period': int(os.getenv('PORTFOLIO_LOOKBACK_PERIOD', '252')),  # trading days
    'min_weight': float(os.getenv('PORTFOLIO_MIN_WEIGHT', '0.05')),  # 5%
    'max_weight': float(os.getenv('PORTFOLIO_MAX_WEIGHT', '0.30'))  # 30%
}

# Alert Configuration
ALERT_CONFIG = {
    'price_change_threshold': float(os.getenv('ALERT_PRICE_CHANGE_THRESHOLD', '0.05')),  # 5%
    'volume_spike_threshold': float(os.getenv('ALERT_VOLUME_SPIKE_THRESHOLD', '2.0')),  # 2x average
    'profit_loss_threshold': float(os.getenv('ALERT_PL_THRESHOLD', '100.0')),  # $100
    'drawdown_threshold': float(os.getenv('ALERT_DRAWDOWN_THRESHOLD', '0.10')),  # 10%
    'enabled_channels': {
        'email': os.getenv('ALERT_EMAIL_ENABLED', 'True').lower() == 'true',
        'sms': os.getenv('ALERT_SMS_ENABLED', 'False').lower() == 'true',
        'slack': os.getenv('ALERT_SLACK_ENABLED', 'False').lower() == 'true',
        'telegram': os.getenv('ALERT_TELEGRAM_ENABLED', 'False').lower() == 'true'
    }
}

# Development Configuration
if ENVIRONMENT == 'development':
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_trading_bot.db'
    BINANCE_TESTNET = True
    COINBASE_SANDBOX = True
    LOG_LEVEL = 'DEBUG'
    MAX_CONCURRENT_BOTS = 3
    RATE_LIMIT_DEFAULT = '1000 per hour'

# Testing Configuration
elif ENVIRONMENT == 'testing':
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BINANCE_TESTNET = True
    COINBASE_SANDBOX = True
    LOG_LEVEL = 'WARNING'
    MAX_CONCURRENT_BOTS = 1
    WTF_CSRF_ENABLED = False

# Production Configuration
elif ENVIRONMENT == 'production':
    DEBUG = False
    TESTING = False
    BINANCE_TESTNET = False
    COINBASE_SANDBOX = False
    LOG_LEVEL = 'INFO'
    # Use environment variables for sensitive data
    assert SECRET_KEY != 'your-secret-key-change-in-production', "Change SECRET_KEY in production!"
    assert JWT_SECRET_KEY != 'your-jwt-secret-key', "Change JWT_SECRET_KEY in production!"

# Configuration Class
@dataclass
class Config:
    """Main configuration class"""
    
    # Basic Flask Configuration
    SECRET_KEY: str = SECRET_KEY
    DEBUG: bool = DEBUG
    TESTING: bool = TESTING
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI: str = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = SQLALCHEMY_TRACK_MODIFICATIONS
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = None
    
    # Redis Configuration
    REDIS_URL: str = REDIS_URL
    
    # Trading Configuration
    MAX_CONCURRENT_BOTS: int = MAX_CONCURRENT_BOTS
    DEFAULT_POSITION_SIZE: float = DEFAULT_POSITION_SIZE
    
    # Risk Management
    MAX_DAILY_LOSS: float = MAX_DAILY_LOSS
    MAX_DRAWDOWN: float = MAX_DRAWDOWN
    
    # Exchange Configuration
    EXCHANGE_CONFIG: Dict[str, Dict[str, Any]] = None
    
    # Strategy Configuration
    DEFAULT_STRATEGY_PARAMS: Dict[str, Dict[str, Any]] = None
    
    # Risk Profiles
    RISK_PROFILES: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize complex configurations"""
        if self.SQLALCHEMY_ENGINE_OPTIONS is None:
            self.SQLALCHEMY_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS
        
        if self.EXCHANGE_CONFIG is None:
            self.EXCHANGE_CONFIG = EXCHANGE_CONFIG
        
        if self.DEFAULT_STRATEGY_PARAMS is None:
            self.DEFAULT_STRATEGY_PARAMS = DEFAULT_STRATEGY_PARAMS
        
        if self.RISK_PROFILES is None:
            self.RISK_PROFILES = RISK_PROFILES

# Create configuration instance
config = Config()

# Export commonly used configurations
__all__ = [
    'config',
    'Config',
    'ENVIRONMENT',
    'DEBUG',
    'TESTING',
    'SECRET_KEY',
    'DATABASE_URL',
    'REDIS_URL',
    'EXCHANGE_CONFIG',
    'DEFAULT_STRATEGY_PARAMS',
    'RISK_PROFILES',
    'SUPPORTED_PAIRS',
    'SUPPORTED_TIMEFRAMES',
    'INDICATOR_CONFIG',
    'ML_CONFIG',
    'PORTFOLIO_CONFIG',
    'ALERT_CONFIG'
]