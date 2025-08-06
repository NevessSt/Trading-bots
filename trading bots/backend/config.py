import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    
    # MongoDB settings
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/trading_bot')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'trading_bot')
    
    # Binance API settings
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Stripe settings
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours for easier development

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MONGO_DB_NAME = 'trading_bot_test'
    
    # Use test keys for external services
    BINANCE_TESTNET = True

class ProductionConfig(Config):
    """Production configuration"""
    # Production should use strong, randomly generated secrets
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    # Ensure testnet is disabled in production unless explicitly enabled
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'False').lower() == 'true'

# Configuration dictionary
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name):
    """Helper function to get configuration class"""
    return config_dict.get(config_name, config_dict['default'])