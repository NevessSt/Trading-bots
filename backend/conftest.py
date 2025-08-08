"""Global test configuration and fixtures for the trading bot platform."""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal
import json
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import Flask
from flask_testing import TestCase

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import application modules
try:
    from app import create_app
    from models import db, User, Bot, Trade, Subscription, APIKey, Notification
    from services.auth_service import AuthService
    from services.trading_service import TradingService
    from config import TestConfig
except ImportError as e:
    # Mock imports if modules don't exist yet
    print(f"Warning: Could not import modules: {e}")
    create_app = None
    db = None
    User = Bot = Trade = Subscription = APIKey = Notification = None
    AuthService = TradingService = None
    TestConfig = None


# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
        'DATABASE_URL': 'sqlite:///:memory:',
        'REDIS_URL': 'redis://localhost:6379/1',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ECHO': False,
        'MAIL_SUPPRESS_SEND': True,
        'CELERY_ALWAYS_EAGER': True,
        'CELERY_EAGER_PROPAGATES_EXCEPTIONS': True,
        'RATE_LIMIT_ENABLED': False,
        'CACHE_TYPE': 'simple',
        'EXCHANGE_API_SANDBOX': True,
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_fake_key',
        'STRIPE_SECRET_KEY': 'sk_test_fake_key',
        'BINANCE_API_KEY': 'test_binance_key',
        'BINANCE_SECRET_KEY': 'test_binance_secret',
        'COINBASE_API_KEY': 'test_coinbase_key',
        'COINBASE_SECRET_KEY': 'test_coinbase_secret',
        'KRAKEN_API_KEY': 'test_kraken_key',
        'KRAKEN_SECRET_KEY': 'test_kraken_secret',
    }
    return config


# Database fixtures
@pytest.fixture(scope="session")
def database_engine(test_config):
    """Create a test database engine."""
    from models import db as _db
    
    engine = create_engine(
        test_config['DATABASE_URL'],
        echo=test_config['SQLALCHEMY_ECHO']
    )
    
    # Create all tables
    _db.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    _db.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(database_engine):
    """Create a database session for testing."""
    if not database_engine:
        return None
    
    Session = sessionmaker(bind=database_engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()


# Flask app fixtures
@pytest.fixture(scope="session")
def app(test_config):
    """Create a Flask app for testing."""
    if not create_app:
        # Create a minimal Flask app for testing
        app = Flask(__name__)
        app.config.update(test_config)
        return app
    
    app = create_app(test_config)
    
    with app.app_context():
        if db:
            db.create_all()
        yield app
        if db:
            db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def app_context(app):
    """Create an application context."""
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def request_context(app):
    """Create a request context."""
    with app.test_request_context():
        yield


# Redis fixtures
@pytest.fixture(scope="session")
def redis_client(test_config):
    """Create a Redis client for testing."""
    try:
        client = redis.from_url(test_config['REDIS_URL'])
        client.ping()  # Test connection
        yield client
        client.flushdb()  # Clean up
    except (redis.ConnectionError, redis.TimeoutError):
        # Mock Redis if not available
        yield Mock()


# User fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'timezone': 'UTC',
        'is_verified': True,
        'is_active': True
    }


@pytest.fixture
def test_user(db_session, sample_user_data):
    """Create a test user."""
    if not User or not db_session:
        return Mock(id=1, **sample_user_data)
    
    user = User(**sample_user_data)
    user.set_password(sample_user_data['password'])
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user."""
    if not User or not db_session:
        return Mock(id=2, is_admin=True, username='admin', email='admin@example.com')
    
    user = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        is_admin=True,
        is_verified=True,
        is_active=True
    )
    user.set_password('AdminPassword123!')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def premium_user(db_session):
    """Create a premium user with subscription."""
    if not User or not Subscription or not db_session:
        return Mock(id=3, subscription_type='premium', username='premium', email='premium@example.com')
    
    user = User(
        username='premium',
        email='premium@example.com',
        first_name='Premium',
        last_name='User',
        is_verified=True,
        is_active=True
    )
    user.set_password('PremiumPassword123!')
    db_session.add(user)
    db_session.flush()
    
    subscription = Subscription(
        user_id=user.id,
        plan_type='premium',
        status='active',
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(subscription)
    db_session.commit()
    return user


# Bot fixtures
@pytest.fixture
def sample_bot_data():
    """Sample bot data for testing."""
    return {
        'name': 'Test Bot',
        'description': 'A test trading bot',
        'exchange': 'binance',
        'symbol': 'BTCUSDT',
        'strategy': 'grid_trading',
        'config': {
            'grid_size': 10,
            'grid_spacing': 0.01,
            'base_order_size': 100,
            'safety_order_size': 200,
            'max_safety_orders': 5,
            'take_profit': 0.02,
            'stop_loss': 0.05
        },
        'risk_level': 'medium',
        'max_position_size': Decimal('1000.00'),
        'is_active': False
    }


@pytest.fixture
def test_bot(db_session, test_user, sample_bot_data):
    """Create a test bot."""
    if not Bot or not db_session:
        return Mock(id=1, user_id=test_user.id if hasattr(test_user, 'id') else 1, **sample_bot_data)
    
    bot = Bot(
        user_id=test_user.id,
        **sample_bot_data
    )
    db_session.add(bot)
    db_session.commit()
    return bot


@pytest.fixture
def active_bot(db_session, test_user, sample_bot_data):
    """Create an active test bot."""
    if not Bot or not db_session:
        data = {**sample_bot_data, 'is_active': True, 'status': 'running'}
        return Mock(id=2, user_id=test_user.id if hasattr(test_user, 'id') else 1, **data)
    
    bot_data = {**sample_bot_data, 'is_active': True, 'status': 'running'}
    bot = Bot(
        user_id=test_user.id,
        **bot_data
    )
    db_session.add(bot)
    db_session.commit()
    return bot


# Trade fixtures
@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'type': 'market',
        'quantity': Decimal('0.001'),
        'price': Decimal('50000.00'),
        'status': 'filled',
        'exchange_order_id': 'test_order_123',
        'executed_at': datetime.utcnow()
    }


@pytest.fixture
def test_trade(db_session, test_bot, sample_trade_data):
    """Create a test trade."""
    if not Trade or not db_session:
        return Mock(id=1, bot_id=test_bot.id if hasattr(test_bot, 'id') else 1, **sample_trade_data)
    
    trade = Trade(
        bot_id=test_bot.id,
        **sample_trade_data
    )
    db_session.add(trade)
    db_session.commit()
    return trade


# API Key fixtures
@pytest.fixture
def test_api_key(db_session, test_user):
    """Create a test API key."""
    if not APIKey or not db_session:
        return Mock(
            id=1,
            user_id=test_user.id if hasattr(test_user, 'id') else 1,
            key='test_api_key_123',
            name='Test API Key',
            permissions=['read', 'trade'],
            is_active=True
        )
    
    api_key = APIKey(
        user_id=test_user.id,
        key='test_api_key_123',
        name='Test API Key',
        permissions=['read', 'trade'],
        is_active=True
    )
    db_session.add(api_key)
    db_session.commit()
    return api_key


# Service fixtures
@pytest.fixture
def auth_service(app_context):
    """Create an AuthService instance."""
    if not AuthService:
        return Mock()
    return AuthService()


@pytest.fixture
def trading_service(app_context):
    """Create a TradingService instance."""
    if not TradingService:
        return Mock()
    return TradingService()


# Authentication fixtures
@pytest.fixture
def auth_headers(test_user, auth_service):
    """Create authentication headers for API requests."""
    if not auth_service or not hasattr(auth_service, 'generate_tokens'):
        return {'Authorization': 'Bearer fake_token'}
    
    tokens = auth_service.generate_tokens(test_user)
    return {'Authorization': f'Bearer {tokens["access_token"]}'}


@pytest.fixture
def admin_auth_headers(admin_user, auth_service):
    """Create admin authentication headers for API requests."""
    if not auth_service or not hasattr(auth_service, 'generate_tokens'):
        return {'Authorization': 'Bearer fake_admin_token'}
    
    tokens = auth_service.generate_tokens(admin_user)
    return {'Authorization': f'Bearer {tokens["access_token"]}'}


# Mock fixtures
@pytest.fixture
def mock_exchange_api():
    """Mock exchange API responses."""
    with patch('services.exchange_service.ExchangeService') as mock:
        mock_instance = Mock()
        mock_instance.get_account_balance.return_value = {
            'USDT': {'free': '1000.00', 'locked': '0.00'},
            'BTC': {'free': '0.1', 'locked': '0.0'}
        }
        mock_instance.get_ticker.return_value = {
            'symbol': 'BTCUSDT',
            'price': '50000.00',
            'bid': '49999.00',
            'ask': '50001.00'
        }
        mock_instance.place_order.return_value = {
            'id': 'test_order_123',
            'status': 'filled',
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'amount': '0.001',
            'price': '50000.00'
        }
        mock_instance.get_order_status.return_value = {
            'id': 'test_order_123',
            'status': 'filled'
        }
        mock_instance.cancel_order.return_value = True
        mock_instance.get_candlesticks.return_value = [
            [1640995200000, 50000, 51000, 49500, 50500, 100],
            [1640995260000, 50500, 51500, 50000, 51000, 150]
        ]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('redis.Redis') as mock:
        mock_instance = Mock()
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.delete.return_value = 1
        mock_instance.exists.return_value = False
        mock_instance.expire.return_value = True
        mock_instance.incr.return_value = 1
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    with patch('services.email_service.EmailService') as mock:
        mock_instance = Mock()
        mock_instance.send_verification_email.return_value = True
        mock_instance.send_password_reset_email.return_value = True
        mock_instance.send_notification_email.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with patch('stripe.checkout.Session') as mock_session, \
         patch('stripe.Subscription') as mock_subscription:
        
        mock_session.create.return_value = Mock(
            id='cs_test_123',
            url='https://checkout.stripe.com/pay/cs_test_123'
        )
        
        mock_subscription.retrieve.return_value = Mock(
            id='sub_test_123',
            status='active',
            current_period_end=int((datetime.utcnow() + timedelta(days=30)).timestamp())
        )
        
        yield {
            'session': mock_session,
            'subscription': mock_subscription
        }


# Temporary directory fixtures
@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file for testing."""
    temp_file_path = temp_dir / 'test_file.txt'
    temp_file_path.write_text('test content')
    yield temp_file_path


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    """Automatically cleanup test data after each test."""
    yield
    
    if db_session:
        # Clean up any test data
        try:
            db_session.rollback()
        except Exception:
            pass


# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment."""
    # Set environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    
    # Create test directories
    test_dirs = ['test-results', 'htmlcov', 'logs', 'tmp']
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    yield
    
    # Cleanup
    # Note: We don't remove directories as they might contain useful test artifacts


# Pytest hooks
def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Add markers based on test location
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Mark slow tests
        if "slow" in item.name.lower() or "load" in item.name.lower():
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """Setup for each test."""
    # Skip tests based on markers and environment
    if item.get_closest_marker("skip_ci") and os.environ.get("CI"):
        pytest.skip("Skipped in CI environment")
    
    if item.get_closest_marker("windows_only") and os.name != 'nt':
        pytest.skip("Windows only test")
    
    if item.get_closest_marker("linux_only") and os.name == 'nt':
        pytest.skip("Linux only test")


def pytest_runtest_teardown(item):
    """Teardown for each test."""
    # Clean up any global state
    pass