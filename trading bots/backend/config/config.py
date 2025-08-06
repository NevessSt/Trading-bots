import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # MongoDB settings
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/trading_bot')
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    
    # Binance API settings
    BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.environ.get('BINANCE_API_SECRET')
    BINANCE_TESTNET = os.environ.get('BINANCE_TESTNET', 'True').lower() == 'true'
    
    # Trading settings
    DEFAULT_TRADE_AMOUNT = float(os.environ.get('DEFAULT_TRADE_AMOUNT', '10.0'))  # Default amount in USD
    MAX_OPEN_TRADES = int(os.environ.get('MAX_OPEN_TRADES', '3'))
    MAX_DAILY_LOSS = float(os.environ.get('MAX_DAILY_LOSS', '5.0'))  # Percentage
    
    # Notification settings
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    # Stripe settings
    STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Subscription plans
    SUBSCRIPTION_PLANS = {
        'free': {
            'name': 'Free',
            'price': 0,
            'features': {
                'max_bots': 1,
                'strategies': ['rsi'],
                'notifications': ['email'],
                'backtest': True,
                'live_trading': False
            }
        },
        'basic': {
            'name': 'Basic',
            'price': 9.99,
            'features': {
                'max_bots': 3,
                'strategies': ['rsi', 'macd', 'ema_crossover'],
                'notifications': ['email', 'telegram'],
                'backtest': True,
                'live_trading': True
            }
        },
        'premium': {
            'name': 'Premium',
            'price': 19.99,
            'features': {
                'max_bots': 10,
                'strategies': ['rsi', 'macd', 'ema_crossover'],
                'notifications': ['email', 'telegram', 'in_app'],
                'backtest': True,
                'live_trading': True,
                'priority_support': True
            }
        }
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    MONGO_URI = os.environ.get('TEST_MONGO_URI', 'mongodb://localhost:27017/trading_bot_test')

class ProductionConfig(Config):
    """Production configuration"""
    # Production-specific settings
    pass

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Get current configuration
def get_config():
    """Get current configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])