"""Test configuration and fixtures."""
import os
import pytest
import tempfile
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from flask_testing import TestCase

# Set test environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'
os.environ['WTF_CSRF_ENABLED'] = 'false'

from app import create_app
from db import db as _db
from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.subscription import Subscription
from models.api_key import APIKey
from services.auth_service import AuthService
from services.trading_service import TradingService
from services.subscription_service import SubscriptionService


class BaseTestCase(TestCase):
    """Base test case for all tests."""
    
    def create_app(self):
        """Create application for testing."""
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'JWT_SECRET_KEY': 'test-jwt-secret',
            'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
            'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
            'WTF_CSRF_ENABLED': False,
            'BCRYPT_LOG_ROUNDS': 4,  # Faster for testing
            'MAIL_SUPPRESS_SEND': True
        }
        return create_app(config)
    
    def setUp(self):
        """Set up test database."""
        _db.create_all()
    
    def tearDown(self):
        """Clean up test database."""
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'WTF_CSRF_ENABLED': False,
        'REDIS_URL': 'redis://localhost:6379/15',  # Use test database
        'MAIL_SUPPRESS_SEND': True,
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_fake_key',
        'STRIPE_SECRET_KEY': 'sk_test_fake_key',
        'EXCHANGE_API_KEY': 'test_api_key',
        'EXCHANGE_SECRET_KEY': 'test_secret_key',
    })
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()
        _db.session.remove()
        _db.get_engine().dispose()
    
    os.close(db_fd)
    try:
        os.unlink(db_path)
    except PermissionError:
        # On Windows, sometimes the file is still locked
        import time
        time.sleep(0.1)
        try:
            os.unlink(db_path)
        except PermissionError:
            pass  # Ignore if we can't delete the temp file


@pytest.fixture(scope='function')
def app_context(app):
    """Create application context for the tests."""
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    """Create database session for the tests."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Configure session to use the connection
    from sqlalchemy.orm import sessionmaker, scoped_session
    Session = scoped_session(sessionmaker(bind=connection))
    
    # Make session available to the app
    db.session = Session
    
    yield Session
    
    Session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post('/api/auth/login', json={
        'username': test_user.username,
        'password': 'password123'
    })
    
    assert response.status_code == 200
    token = response.json['access_token']
    
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_headers(client, admin_user):
    """Get authentication headers for admin user."""
    response = client.post('/api/auth/login', json={
        'username': admin_user.username,
        'password': 'admin123'
    })
    
    assert response.status_code == 200
    token = response.json['access_token']
    
    return {'Authorization': f'Bearer {token}'}


# User Fixtures
@pytest.fixture
def test_user(session):
    """Create a test user."""
    user = User(
        email='test@example.com',
        username='testuser',
        password='password123',
        is_verified=True,
        subscription_plan='basic'
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def admin_user(session):
    """Create an admin user."""
    user = User(
        email='admin@example.com',
        username='admin',
        password_hash=AuthService.hash_password('admin123'),
        is_verified=True,
        role='admin',
        subscription_plan='premium'
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def unverified_user(session):
    """Create an unverified user."""
    user = User(
        email='unverified@example.com',
        username='unverified',
        password_hash=AuthService.hash_password('password123'),
        is_verified=False
    )
    session.add(user)
    session.commit()
    return user


# Bot Fixtures
@pytest.fixture
def test_bot(session, test_user):
    """Create a test bot."""
    bot = Bot(
        user_id=test_user.id,
        name='Test Bot',
        strategy='grid_trading',
        symbol='BTCUSDT',
        base_amount=1000.0,
        config={
            'symbol': 'BTC/USDT',
            'grid_size': 10,
            'profit_target': 0.02,
            'stop_loss': 0.05
        },
        is_active=False
    )
    session.add(bot)
    session.commit()
    return bot


@pytest.fixture
def active_bot(session, test_user):
    """Create an active test bot."""
    bot = Bot(
        user_id=test_user.id,
        name='Active Bot',
        strategy='dca',
        symbol='ETHUSDT',
        base_amount=500.0,
        config={
            'symbol': 'ETH/USDT',
            'investment_amount': 100,
            'dca_interval': 3600
        },
        is_active=True
    )
    session.add(bot)
    session.commit()
    return bot


# Trade Fixtures
@pytest.fixture
def test_trade(session, test_bot):
    """Create a test trade."""
    trade = Trade(
        bot_id=test_bot.id,
        symbol='BTC/USDT',
        side='buy',
        amount=0.001,
        price=50000.0,
        exchange_order_id='test_order_123',
        status='filled'
    )
    session.add(trade)
    session.commit()
    return trade


# Subscription Fixtures
@pytest.fixture
def test_subscription(session, test_user):
    """Create a test subscription."""
    subscription = Subscription(
        user_id=test_user.id,
        plan='basic',
        status='active',
        stripe_subscription_id='sub_test_123'
    )
    session.add(subscription)
    session.commit()
    return subscription


# API Key Fixtures
@pytest.fixture
def test_api_key(session, test_user):
    """Create a test API key."""
    api_key = APIKey(
        user_id=test_user.id,
        exchange='binance',
        key_name='Test API Key',
        api_key='test_api_key_value',
        api_secret='test_api_secret_value',
        permissions=['read', 'trade']
    )
    session.add(api_key)
    session.commit()
    return api_key


# Mock Fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('redis.Redis') as mock:
        redis_instance = Mock()
        mock.return_value = redis_instance
        yield redis_instance


@pytest.fixture
def mock_exchange_api():
    """Mock exchange API."""
    exchange_instance = Mock()
    
    # Mock common methods
    exchange_instance.get_ticker.return_value = {
        'symbol': 'BTC/USDT',
        'price': 50000.0,
        'bid': 49950.0,
        'ask': 50050.0
    }
    
    exchange_instance.create_order.return_value = {
        'id': 'order_123',
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 0.001,
        'price': 50000.0,
        'status': 'open'
    }
    
    exchange_instance.get_balance.return_value = {
        'USDT': {'free': 1000.0, 'used': 0.0, 'total': 1000.0},
        'BTC': {'free': 0.0, 'used': 0.0, 'total': 0.0}
    }
    
    return exchange_instance


@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with patch('stripe.Customer') as mock_customer, \
         patch('stripe.Subscription') as mock_subscription, \
         patch('stripe.PaymentMethod') as mock_payment_method:
        
        # Mock customer
        mock_customer.create.return_value = Mock(id='cus_test_123')
        mock_customer.retrieve.return_value = Mock(id='cus_test_123')
        
        # Mock subscription
        mock_subscription.create.return_value = Mock(
            id='sub_test_123',
            status='active',
            current_period_end=1234567890
        )
        mock_subscription.retrieve.return_value = Mock(
            id='sub_test_123',
            status='active'
        )
        
        # Mock payment method
        mock_payment_method.attach.return_value = Mock(id='pm_test_123')
        
        yield {
            'customer': mock_customer,
            'subscription': mock_subscription,
            'payment_method': mock_payment_method
        }


@pytest.fixture
def mock_email():
    """Mock email service."""
    with patch('services.email_service.EmailService') as mock:
        email_instance = Mock()
        mock.return_value = email_instance
        email_instance.send_verification_email.return_value = True
        email_instance.send_password_reset_email.return_value = True
        email_instance.send_notification_email.return_value = True
        yield email_instance


# Test Data Fixtures
@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        'BTC/USDT': {
            'price': 50000.0,
            'volume': 1000.0,
            'high': 52000.0,
            'low': 48000.0,
            'change': 0.02
        },
        'ETH/USDT': {
            'price': 3000.0,
            'volume': 5000.0,
            'high': 3100.0,
            'low': 2900.0,
            'change': -0.01
        }
    }


@pytest.fixture
def sample_bot_config():
    """Sample bot configuration for testing."""
    return {
        'grid_trading': {
            'symbol': 'BTC/USDT',
            'grid_size': 10,
            'profit_target': 0.02,
            'stop_loss': 0.05,
            'investment_amount': 1000
        },
        'dca': {
            'symbol': 'ETH/USDT',
            'investment_amount': 100,
            'dca_interval': 3600,
            'max_orders': 10
        },
        'arbitrage': {
            'symbol': 'BTC/USDT',
            'min_profit_threshold': 0.005,
            'max_position_size': 0.1
        }
    }


# Performance Testing Fixtures
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


# Cleanup Fixtures
@pytest.fixture(autouse=True)
def cleanup_files():
    """Clean up test files after each test."""
    yield
    # Cleanup logic here if needed
    pass


# Pytest Hooks
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runintegration", action="store_true", default=False, help="run integration tests"
    )