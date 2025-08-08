"""Test configuration and settings."""
import os
import tempfile
from datetime import timedelta


class TestConfig:
    """Base test configuration."""
    
    # Flask settings
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging
    
    # Security settings
    SECRET_KEY = 'test-secret-key-not-for-production'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
    
    # Redis settings (mock for tests)
    REDIS_URL = 'redis://localhost:6379/1'  # Test database
    CACHE_TYPE = 'simple'  # Simple cache for testing
    
    # Celery settings (mock for tests)
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously in tests
    CELERY_TASK_EAGER_PROPAGATES = True  # Propagate exceptions in tests
    
    # Email settings (mock for tests)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'test@example.com'
    MAIL_PASSWORD = 'test-password'
    MAIL_DEFAULT_SENDER = 'test@example.com'
    MAIL_SUPPRESS_SEND = True  # Don't actually send emails in tests
    
    # Exchange API settings (mock for tests)
    EXCHANGE_API_TIMEOUT = 5
    EXCHANGE_RATE_LIMIT = 100  # Requests per minute
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = tempfile.gettempdir()
    
    # Logging settings
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = None  # Don't log to file in tests
    
    # Rate limiting settings
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100 per minute'
    
    # Security settings
    SESSION_COOKIE_SECURE = False  # Allow HTTP in tests
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # API settings
    API_TITLE = 'Trading Bot API (Test)'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.2'
    
    # Pagination settings
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Trading settings
    MIN_TRADE_AMOUNT = 0.001
    MAX_TRADE_AMOUNT = 1000000
    DEFAULT_SLIPPAGE = 0.001  # 0.1%
    
    # Bot settings
    MAX_BOTS_PER_USER = 10
    MAX_ACTIVE_BOTS_PER_USER = 5
    BOT_UPDATE_INTERVAL = 60  # seconds
    
    # Market data settings
    MARKET_DATA_CACHE_TTL = 60  # seconds
    PRICE_PRECISION = 8
    QUANTITY_PRECISION = 8
    
    # Performance settings
    PERFORMANCE_CALCULATION_INTERVAL = 300  # 5 minutes
    PORTFOLIO_UPDATE_INTERVAL = 60  # 1 minute
    
    # Backup settings
    BACKUP_ENABLED = False  # Disable backups in tests
    BACKUP_INTERVAL = timedelta(hours=24)
    BACKUP_RETENTION_DAYS = 7
    
    # Monitoring settings
    HEALTH_CHECK_ENABLED = True
    METRICS_ENABLED = False  # Disable metrics collection in tests
    
    # Feature flags
    ENABLE_PAPER_TRADING = True
    ENABLE_LIVE_TRADING = False  # Disable live trading in tests
    ENABLE_BACKTESTING = True
    ENABLE_SOCIAL_FEATURES = False
    ENABLE_ADVANCED_ANALYTICS = True
    
    # External service URLs (mock)
    EXCHANGE_API_BASE_URL = 'https://api.mock-exchange.com'
    MARKET_DATA_API_URL = 'https://api.mock-marketdata.com'
    NEWS_API_URL = 'https://api.mock-news.com'
    
    # Webhook settings
    WEBHOOK_TIMEOUT = 5
    WEBHOOK_RETRY_ATTEMPTS = 3
    WEBHOOK_RETRY_DELAY = 1  # seconds
    
    # Encryption settings
    ENCRYPTION_KEY = b'test-encryption-key-32-bytes-long!!'  # 32 bytes for AES-256
    
    # Test-specific settings
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    TRAP_HTTP_EXCEPTIONS = False
    TRAP_BAD_REQUEST_ERRORS = False
    
    @staticmethod
    def init_app(app):
        """Initialize application with test configuration."""
        pass


class UnitTestConfig(TestConfig):
    """Configuration for unit tests."""
    
    # Use even faster in-memory database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable external services
    CELERY_TASK_ALWAYS_EAGER = True
    MAIL_SUPPRESS_SEND = True
    
    # Faster token expiration for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    
    # Minimal logging
    LOG_LEVEL = 'WARNING'
    
    # Disable rate limiting for unit tests
    RATELIMIT_ENABLED = False
    
    # Disable caching
    CACHE_TYPE = 'null'


class IntegrationTestConfig(TestConfig):
    """Configuration for integration tests."""
    
    # Use temporary file database for persistence across requests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_integration.db'
    
    # Enable more realistic settings
    CELERY_TASK_ALWAYS_EAGER = False  # Test async behavior
    
    # Longer token expiration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    
    # Enable rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = '1000 per minute'  # Higher limit for tests
    
    # Enable caching
    CACHE_TYPE = 'simple'
    
    # More verbose logging
    LOG_LEVEL = 'INFO'


class E2ETestConfig(TestConfig):
    """Configuration for end-to-end tests."""
    
    # Use persistent database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_e2e.db'
    
    # Production-like settings
    CELERY_TASK_ALWAYS_EAGER = False
    MAIL_SUPPRESS_SEND = False  # Test email sending (to test server)
    
    # Realistic token expiration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Enable all features
    ENABLE_LIVE_TRADING = False  # Still disabled for safety
    ENABLE_SOCIAL_FEATURES = True
    ENABLE_ADVANCED_ANALYTICS = True
    
    # Enable rate limiting
    RATELIMIT_ENABLED = True
    
    # Full logging
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = 'test_e2e.log'


class PerformanceTestConfig(TestConfig):
    """Configuration for performance tests."""
    
    # Use PostgreSQL for performance testing (if available)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URL',
        'sqlite:///test_performance.db'
    )
    
    # Disable debug mode for realistic performance
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Production-like settings
    CELERY_TASK_ALWAYS_EAGER = False
    
    # Realistic limits
    MAX_BOTS_PER_USER = 100
    MAX_ACTIVE_BOTS_PER_USER = 50
    
    # Enable caching
    CACHE_TYPE = 'redis'
    
    # Minimal logging to avoid I/O overhead
    LOG_LEVEL = 'ERROR'
    
    # Higher rate limits
    RATELIMIT_DEFAULT = '10000 per minute'


class SecurityTestConfig(TestConfig):
    """Configuration for security tests."""
    
    # Use separate database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_security.db'
    
    # Enable security features
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Shorter token expiration for security tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # Enable rate limiting with strict limits
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = '10 per minute'
    
    # Enable all security features
    ENABLE_CSRF_PROTECTION = True
    ENABLE_CONTENT_SECURITY_POLICY = True
    
    # Strict validation
    STRICT_VALIDATION = True
    
    # Security logging
    LOG_LEVEL = 'INFO'
    SECURITY_LOG_FILE = 'test_security.log'


# Configuration mapping
config = {
    'unit': UnitTestConfig,
    'integration': IntegrationTestConfig,
    'e2e': E2ETestConfig,
    'performance': PerformanceTestConfig,
    'security': SecurityTestConfig,
    'default': TestConfig
}


def get_config(config_name=None):
    """Get configuration class by name."""
    if config_name is None:
        config_name = os.environ.get('TEST_CONFIG', 'default')
    
    return config.get(config_name, TestConfig)


# Test data constants
TEST_USER_DATA = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'testpassword123',
    'confirm_password': 'testpassword123'
}

TEST_API_KEY_DATA = {
    'exchange': 'binance',
    'key_name': 'Test API Key',
    'api_key': 'test_api_key_123',
    'api_secret': 'test_api_secret_456'
}

TEST_BOT_DATA = {
    'name': 'Test Bot',
    'strategy': 'grid',
    'trading_pair': 'BTCUSDT',
    'config': {
        'grid_size': 10,
        'price_range': [45000, 55000],
        'investment_amount': 1000
    }
}

TEST_TRADE_DATA = {
    'trading_pair': 'BTCUSDT',
    'side': 'buy',
    'quantity': '0.001',
    'order_type': 'market'
}

# Mock data for external services
MOCK_MARKET_DATA = {
    'BTCUSDT': {
        'symbol': 'BTCUSDT',
        'price': '50000.00',
        'change_24h': '2.5',
        'volume_24h': '1000000',
        'high_24h': '51000.00',
        'low_24h': '49000.00'
    }
}

MOCK_EXCHANGE_RESPONSE = {
    'orderId': '12345',
    'symbol': 'BTCUSDT',
    'status': 'FILLED',
    'executedQty': '0.001',
    'cummulativeQuoteQty': '50.00',
    'fills': [{
        'price': '50000.00',
        'qty': '0.001',
        'commission': '0.05',
        'commissionAsset': 'USDT'
    }]
}

# Test utilities
class TestConstants:
    """Constants used across tests."""
    
    # Time constants
    TIMEOUT_SHORT = 1  # seconds
    TIMEOUT_MEDIUM = 5  # seconds
    TIMEOUT_LONG = 30  # seconds
    
    # Retry constants
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # seconds
    
    # Precision constants
    PRICE_PRECISION = 8
    QUANTITY_PRECISION = 8
    PERCENTAGE_PRECISION = 4
    
    # Validation constants
    MIN_PASSWORD_LENGTH = 8
    MAX_USERNAME_LENGTH = 50
    MAX_EMAIL_LENGTH = 100
    
    # Trading constants
    MIN_TRADE_AMOUNT = 0.001
    MAX_TRADE_AMOUNT = 1000000
    DEFAULT_SLIPPAGE = 0.001
    
    # Performance thresholds
    MAX_RESPONSE_TIME = 1.0  # seconds
    MAX_QUERY_TIME = 0.1  # seconds
    MAX_MEMORY_USAGE = 100 * 1024 * 1024  # 100MB


# Environment-specific overrides
if os.environ.get('CI'):
    # CI/CD environment adjustments
    TestConfig.SQLALCHEMY_ECHO = False
    TestConfig.LOG_LEVEL = 'WARNING'
    TestConfig.CELERY_TASK_ALWAYS_EAGER = True
    
if os.environ.get('GITHUB_ACTIONS'):
    # GitHub Actions specific settings
    TestConfig.REDIS_URL = 'redis://localhost:6379/0'
    TestConfig.SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/test_db'