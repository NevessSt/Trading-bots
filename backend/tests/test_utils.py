"""Test utilities and helper functions."""
import json
import time
import random
import string
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import from backend directory using explicit path
import importlib.util
app_spec = importlib.util.spec_from_file_location("app", os.path.join(backend_dir, "app.py"))
app_module = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app_module)
create_app = app_module.create_app
from db import db
from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.api_key import APIKey
from models.subscription import Subscription
from utils.security import generate_api_key, hash_api_secret
# Import test_config from the same directory
import importlib.util
test_config_spec = importlib.util.spec_from_file_location("test_config", os.path.join(os.path.dirname(__file__), "test_config.py"))
test_config_module = importlib.util.module_from_spec(test_config_spec)
test_config_spec.loader.exec_module(test_config_module)
TestConfig = test_config_module.TestConfig
MOCK_MARKET_DATA = test_config_module.MOCK_MARKET_DATA
MOCK_EXCHANGE_RESPONSE = test_config_module.MOCK_EXCHANGE_RESPONSE


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_user(username: str = None, email: str = None, password: str = None, **kwargs) -> User:
        """Create a test user."""
        username = username or f"testuser_{random.randint(1000, 9999)}"
        email = email or f"test_{random.randint(1000, 9999)}@example.com"
        password = password or "testpassword123"
        
        user = User(
            username=username,
            email=email,
            **kwargs
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    @staticmethod
    def create_api_key(user: User, exchange: str = 'binance', **kwargs) -> APIKey:
        """Create a test API key."""
        api_key = APIKey(
            user_id=user.id,
            exchange=exchange,
            key_name=kwargs.get('key_name', f'Test Key {random.randint(1000, 9999)}'),
            api_key=kwargs.get('api_key', generate_api_key()),
            api_secret_hash=hash_api_secret(kwargs.get('api_secret', 'test_secret')),
            **{k: v for k, v in kwargs.items() if k not in ['key_name', 'api_key', 'api_secret']}
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        return api_key
    
    @staticmethod
    def create_bot(user: User, api_key: APIKey = None, **kwargs) -> Bot:
        """Create a test bot."""
        if api_key is None:
            api_key = TestDataFactory.create_api_key(user)
        
        bot = Bot(
            user_id=user.id,
            api_key_id=api_key.id,
            name=kwargs.get('name', f'Test Bot {random.randint(1000, 9999)}'),
            strategy=kwargs.get('strategy', 'grid'),
            trading_pair=kwargs.get('trading_pair', 'BTCUSDT'),
            status=kwargs.get('status', 'stopped'),
            config=kwargs.get('config', {
                'grid_size': 10,
                'price_range': [45000, 55000],
                'investment_amount': 1000
            }),
            **{k: v for k, v in kwargs.items() if k not in ['name', 'strategy', 'trading_pair', 'status', 'config']}
        )
        
        db.session.add(bot)
        db.session.commit()
        
        return bot
    
    @staticmethod
    def create_trade(bot: Bot, user: User = None, **kwargs) -> Trade:
        """Create a test trade."""
        if user is None:
            user = User.query.get(bot.user_id)
        
        trade = Trade(
            bot_id=bot.id,
            user_id=user.id,
            trading_pair=kwargs.get('trading_pair', bot.trading_pair),
            side=kwargs.get('side', 'buy'),
            quantity=Decimal(str(kwargs.get('quantity', '0.001'))),
            price=Decimal(str(kwargs.get('price', '50000'))),
            total_value=Decimal(str(kwargs.get('total_value', '50'))),
            order_type=kwargs.get('order_type', 'market'),
            status=kwargs.get('status', 'filled'),
            exchange_order_id=kwargs.get('exchange_order_id', f'order_{random.randint(10000, 99999)}'),
            executed_at=kwargs.get('executed_at', datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if k not in [
                'trading_pair', 'side', 'quantity', 'price', 'total_value',
                'order_type', 'status', 'exchange_order_id', 'executed_at'
            ]}
        )
        
        db.session.add(trade)
        db.session.commit()
        
        return trade
    
    @staticmethod
    def create_subscription(user: User, **kwargs) -> Subscription:
        """Create a test subscription."""
        subscription = Subscription(
            user_id=user.id,
            plan=kwargs.get('plan', 'premium'),
            status=kwargs.get('status', 'active'),
            start_date=kwargs.get('start_date', datetime.utcnow()),
            end_date=kwargs.get('end_date', datetime.utcnow() + timedelta(days=30)),
            **{k: v for k, v in kwargs.items() if k not in ['plan', 'status', 'start_date', 'end_date']}
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return subscription


class APITestHelper:
    """Helper class for API testing."""
    
    def __init__(self, client: FlaskClient):
        self.client = client
        self._auth_token = None
        self._auth_headers = None
    
    def register_user(self, user_data: Dict[str, str] = None) -> TestResponse:
        """Register a new user."""
        if user_data is None:
            user_data = {
                'username': f'testuser_{random.randint(1000, 9999)}',
                'email': f'test_{random.randint(1000, 9999)}@example.com',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123'
            }
        
        return self.client.post('/api/auth/register',
                               data=json.dumps(user_data),
                               content_type='application/json')
    
    def login_user(self, username: str = None, password: str = None) -> TestResponse:
        """Login a user and store auth token."""
        login_data = {
            'username': username or 'testuser',
            'password': password or 'testpassword123'
        }
        
        response = self.client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            self._auth_token = data['access_token']
            self._auth_headers = {'Authorization': f'Bearer {self._auth_token}'}
        
        return response
    
    def logout_user(self) -> TestResponse:
        """Logout the current user."""
        response = self.client.post('/api/auth/logout', headers=self._auth_headers)
        self._auth_token = None
        self._auth_headers = None
        return response
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return self._auth_headers or {}
    
    def get(self, url: str, **kwargs) -> TestResponse:
        """Make authenticated GET request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.auth_headers)
        return self.client.get(url, headers=headers, **kwargs)
    
    def post(self, url: str, data: Dict = None, **kwargs) -> TestResponse:
        """Make authenticated POST request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.auth_headers)
        headers.setdefault('Content-Type', 'application/json')
        
        if data and headers.get('Content-Type') == 'application/json':
            data = json.dumps(data)
        
        return self.client.post(url, data=data, headers=headers, **kwargs)
    
    def put(self, url: str, data: Dict = None, **kwargs) -> TestResponse:
        """Make authenticated PUT request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.auth_headers)
        headers.setdefault('Content-Type', 'application/json')
        
        if data and headers.get('Content-Type') == 'application/json':
            data = json.dumps(data)
        
        return self.client.put(url, data=data, headers=headers, **kwargs)
    
    def delete(self, url: str, **kwargs) -> TestResponse:
        """Make authenticated DELETE request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.auth_headers)
        return self.client.delete(url, headers=headers, **kwargs)


class ResponseValidator:
    """Helper class for validating API responses."""
    
    @staticmethod
    def assert_success(response: TestResponse, expected_status: int = 200):
        """Assert that response is successful."""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.data}"
    
    @staticmethod
    def assert_error(response: TestResponse, expected_status: int = 400):
        """Assert that response is an error."""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.data}"
        
        data = json.loads(response.data)
        assert 'error' in data or 'errors' in data or 'message' in data
    
    @staticmethod
    def assert_validation_error(response: TestResponse, field: str = None):
        """Assert that response is a validation error."""
        ResponseValidator.assert_error(response, 400)
        
        data = json.loads(response.data)
        if field:
            assert field in str(data), f"Field '{field}' not found in validation errors: {data}"
    
    @staticmethod
    def assert_unauthorized(response: TestResponse):
        """Assert that response is unauthorized."""
        ResponseValidator.assert_error(response, 401)
    
    @staticmethod
    def assert_forbidden(response: TestResponse):
        """Assert that response is forbidden."""
        ResponseValidator.assert_error(response, 403)
    
    @staticmethod
    def assert_not_found(response: TestResponse):
        """Assert that response is not found."""
        ResponseValidator.assert_error(response, 404)
    
    @staticmethod
    def assert_json_structure(response: TestResponse, expected_keys: List[str]):
        """Assert that response JSON has expected structure."""
        ResponseValidator.assert_success(response)
        
        data = json.loads(response.data)
        for key in expected_keys:
            assert key in data, f"Key '{key}' not found in response: {data}"
    
    @staticmethod
    def assert_pagination(response: TestResponse):
        """Assert that response has pagination structure."""
        ResponseValidator.assert_success(response)
        
        data = json.loads(response.data)
        pagination_keys = ['page', 'per_page', 'total', 'pages']
        
        for key in pagination_keys:
            assert key in data, f"Pagination key '{key}' not found in response: {data}"
    
    @staticmethod
    def assert_no_sensitive_data(response: TestResponse, sensitive_fields: List[str] = None):
        """Assert that response doesn't contain sensitive data."""
        if sensitive_fields is None:
            sensitive_fields = ['password', 'password_hash', 'api_secret', 'secret_key', 'private_key']
        
        response_text = response.data.decode('utf-8').lower()
        
        for field in sensitive_fields:
            assert field.lower() not in response_text, f"Sensitive field '{field}' found in response"


class MockService:
    """Helper class for mocking external services."""
    
    @staticmethod
    @contextmanager
    def mock_exchange_service():
        """Mock exchange service."""
        with patch('app.services.exchange_service.ExchangeService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            # Mock common methods
            mock_instance.validate_api_credentials.return_value = True
            mock_instance.get_account_balance.return_value = {'USDT': 10000, 'BTC': 0.1}
            mock_instance.place_order.return_value = MOCK_EXCHANGE_RESPONSE
            mock_instance.get_order_status.return_value = 'FILLED'
            mock_instance.cancel_order.return_value = True
            mock_instance.get_market_data.return_value = MOCK_MARKET_DATA['BTCUSDT']
            
            yield mock_instance
    
    @staticmethod
    @contextmanager
    def mock_redis_service():
        """Mock Redis service."""
        with patch('app.services.cache_service.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.set.return_value = True
            mock_redis.delete.return_value = True
            mock_redis.exists.return_value = False
            
            yield mock_redis
    
    @staticmethod
    @contextmanager
    def mock_celery_service():
        """Mock Celery service."""
        with patch('app.tasks.celery') as mock_celery:
            mock_task = MagicMock()
            mock_task.delay.return_value = MagicMock(id='test-task-id')
            mock_celery.send_task.return_value = mock_task
            
            yield mock_celery
    
    @staticmethod
    @contextmanager
    def mock_email_service():
        """Mock email service."""
        with patch('app.services.email_service.send_email') as mock_send:
            mock_send.return_value = True
            yield mock_send


class PerformanceTimer:
    """Helper class for measuring performance."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing."""
        self.start_time = time.time()
    
    def stop(self):
        """Stop timing."""
        self.end_time = time.time()
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0
        
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    def assert_under(self, max_time: float):
        """Assert that elapsed time is under maximum."""
        assert self.elapsed < max_time, f"Operation took {self.elapsed:.3f}s, expected under {max_time}s"
    
    @contextmanager
    def measure(self):
        """Context manager for measuring time."""
        self.start()
        try:
            yield self
        finally:
            self.stop()


class DatabaseHelper:
    """Helper class for database operations in tests."""
    
    @staticmethod
    def clean_db():
        """Clean all data from database."""
        # Delete in reverse order of dependencies
        db.session.query(Trade).delete()
        db.session.query(Bot).delete()
        db.session.query(APIKey).delete()
        db.session.query(Subscription).delete()
        db.session.query(User).delete()
        db.session.commit()
    
    @staticmethod
    def count_records(model_class) -> int:
        """Count records in a table."""
        return db.session.query(model_class).count()
    
    @staticmethod
    def get_last_record(model_class):
        """Get the last inserted record."""
        return db.session.query(model_class).order_by(model_class.id.desc()).first()
    
    @staticmethod
    @contextmanager
    def transaction():
        """Context manager for database transactions."""
        try:
            yield
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise


class RandomDataGenerator:
    """Helper class for generating random test data."""
    
    @staticmethod
    def random_string(length: int = 10, chars: str = None) -> str:
        """Generate random string."""
        if chars is None:
            chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def random_email() -> str:
        """Generate random email."""
        username = RandomDataGenerator.random_string(8)
        domain = RandomDataGenerator.random_string(6)
        return f"{username}@{domain}.com"
    
    @staticmethod
    def random_price(min_price: float = 1000, max_price: float = 100000) -> Decimal:
        """Generate random price."""
        price = random.uniform(min_price, max_price)
        return Decimal(f"{price:.2f}")
    
    @staticmethod
    def random_quantity(min_qty: float = 0.001, max_qty: float = 10) -> Decimal:
        """Generate random quantity."""
        qty = random.uniform(min_qty, max_qty)
        return Decimal(f"{qty:.6f}")
    
    @staticmethod
    def random_trading_pair() -> str:
        """Generate random trading pair."""
        bases = ['BTC', 'ETH', 'BNB', 'ADA', 'DOT']
        quotes = ['USDT', 'BUSD', 'USD', 'EUR']
        return f"{random.choice(bases)}{random.choice(quotes)}"
    
    @staticmethod
    def random_datetime(days_ago: int = 30) -> datetime:
        """Generate random datetime within specified days ago."""
        start_date = datetime.utcnow() - timedelta(days=days_ago)
        end_date = datetime.utcnow()
        
        time_between = end_date - start_date
        random_seconds = random.randint(0, int(time_between.total_seconds()))
        
        return start_date + timedelta(seconds=random_seconds)


class TestAssertions:
    """Custom assertions for testing."""
    
    @staticmethod
    def assert_decimal_equal(actual: Decimal, expected: Decimal, places: int = 8):
        """Assert that two decimals are equal within specified decimal places."""
        multiplier = Decimal(10) ** places
        actual_rounded = (actual * multiplier).to_integral_value() / multiplier
        expected_rounded = (expected * multiplier).to_integral_value() / multiplier
        
        assert actual_rounded == expected_rounded, f"Expected {expected_rounded}, got {actual_rounded}"
    
    @staticmethod
    def assert_datetime_close(actual: datetime, expected: datetime, delta_seconds: int = 5):
        """Assert that two datetimes are close within specified seconds."""
        diff = abs((actual - expected).total_seconds())
        assert diff <= delta_seconds, f"Datetimes differ by {diff} seconds, expected within {delta_seconds}"
    
    @staticmethod
    def assert_percentage_close(actual: float, expected: float, tolerance: float = 0.01):
        """Assert that two percentages are close within tolerance."""
        diff = abs(actual - expected)
        assert diff <= tolerance, f"Percentages differ by {diff}, expected within {tolerance}"
    
    @staticmethod
    def assert_list_contains_subset(actual_list: List, expected_subset: List):
        """Assert that list contains all items from subset."""
        for item in expected_subset:
            assert item in actual_list, f"Item {item} not found in {actual_list}"
    
    @staticmethod
    def assert_dict_contains_subset(actual_dict: Dict, expected_subset: Dict):
        """Assert that dictionary contains all key-value pairs from subset."""
        for key, value in expected_subset.items():
            assert key in actual_dict, f"Key {key} not found in {actual_dict}"
            assert actual_dict[key] == value, f"Expected {key}={value}, got {actual_dict[key]}"


# Utility functions
def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1) -> bool:
    """Wait for a condition to become true."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    
    return False


def retry_on_failure(func, max_retries: int = 3, delay: float = 0.1):
    """Retry function on failure."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay)


def generate_test_jwt_token(user_id: int, expires_delta: timedelta = None) -> str:
    """Generate a test JWT token."""
    import jwt
    from datetime import datetime, timedelta
    
    if expires_delta is None:
        expires_delta = timedelta(hours=1)
    
    payload = {
        'sub': str(user_id),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + expires_delta
    }
    
    return jwt.encode(payload, TestConfig.JWT_SECRET_KEY, algorithm='HS256')


def create_test_file(content: str, filename: str = None) -> str:
    """Create a temporary test file."""
    import tempfile
    import os
    
    if filename is None:
        fd, filepath = tempfile.mkstemp(text=True)
        with os.fdopen(fd, 'w') as f:
            f.write(content)
    else:
        filepath = os.path.join(tempfile.gettempdir(), filename)
        with open(filepath, 'w') as f:
            f.write(content)
    
    return filepath


def cleanup_test_file(filepath: str):
    """Clean up a test file."""
    import os
    
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass


def hash_password_for_test(password: str) -> str:
    """Hash password for testing purposes."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_mock_market_data(symbol: str = 'BTCUSDT') -> Dict[str, Any]:
    """Generate mock market data."""
    base_price = random.uniform(30000, 70000)
    
    return {
        'symbol': symbol,
        'price': f"{base_price:.2f}",
        'change_24h': f"{random.uniform(-10, 10):.2f}",
        'volume_24h': f"{random.uniform(100000, 1000000):.0f}",
        'high_24h': f"{base_price * random.uniform(1.01, 1.05):.2f}",
        'low_24h': f"{base_price * random.uniform(0.95, 0.99):.2f}",
        'timestamp': int(time.time())
    }


def generate_mock_trade_data(symbol: str = 'BTCUSDT', side: str = 'buy') -> Dict[str, Any]:
    """Generate mock trade data."""
    quantity = random.uniform(0.001, 1.0)
    price = random.uniform(30000, 70000)
    
    return {
        'orderId': str(random.randint(100000, 999999)),
        'symbol': symbol,
        'side': side,
        'quantity': f"{quantity:.6f}",
        'price': f"{price:.2f}",
        'status': 'FILLED',
        'executedQty': f"{quantity:.6f}",
        'cummulativeQuoteQty': f"{quantity * price:.2f}",
        'timestamp': int(time.time() * 1000)
    }