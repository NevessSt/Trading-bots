"""Global pytest configuration and fixtures."""

import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test environment setup
os.environ['TESTING'] = 'true'
os.environ['LOG_LEVEL'] = 'WARNING'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/15'


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        'database_url': 'sqlite:///:memory:',
        'redis_url': 'redis://localhost:6379/15',
        'secret_key': 'test-secret-key',
        'jwt_secret': 'test-jwt-secret',
        'testing': True,
        'debug': False,
        'log_level': 'WARNING'
    }


@pytest.fixture
def mock_database():
    """Mock database connection."""
    with patch('database.connection.get_db_connection') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        yield mock_connection


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch('redis.Redis') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': 'hashed_password',
        'api_key': 'test_api_key',
        'api_secret': 'test_api_secret',
        'license_type': 'premium',
        'license_expires': datetime.now() + timedelta(days=30),
        'created_at': datetime.now(),
        'is_active': True
    }


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return {
        'id': 1,
        'user_id': 1,
        'symbol': 'BTCUSDT',
        'side': 'BUY',
        'quantity': 0.001,
        'price': 50000.0,
        'status': 'FILLED',
        'order_id': 'test_order_123',
        'timestamp': datetime.now(),
        'pnl': 100.0,
        'commission': 0.1
    }


@pytest.fixture
def sample_historical_data():
    """Sample historical price data for backtesting."""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1H')
    np.random.seed(42)  # For reproducible tests
    
    # Generate realistic OHLCV data
    base_price = 50000
    price_changes = np.random.normal(0, 0.02, len(dates))
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))  # Minimum price of $1000
    
    data = []
    for i, date in enumerate(dates):
        open_price = prices[i]
        close_price = prices[i] * (1 + np.random.normal(0, 0.01))
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
        volume = np.random.uniform(100, 1000)
        
        data.append({
            'timestamp': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 2)
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def mock_binance_client():
    """Mock Binance API client."""
    with patch('binance.client.Client') as mock_client:
        client_instance = Mock()
        
        # Mock common API responses
        client_instance.get_account.return_value = {
            'balances': [
                {'asset': 'BTC', 'free': '1.0', 'locked': '0.0'},
                {'asset': 'USDT', 'free': '10000.0', 'locked': '0.0'}
            ]
        }
        
        client_instance.get_symbol_ticker.return_value = {
            'symbol': 'BTCUSDT',
            'price': '50000.0'
        }
        
        client_instance.create_order.return_value = {
            'symbol': 'BTCUSDT',
            'orderId': 123456,
            'status': 'FILLED',
            'executedQty': '0.001',
            'cummulativeQuoteQty': '50.0'
        }
        
        mock_client.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_trading_engine():
    """Mock trading engine for backtesting."""
    with patch('bot_engine.trading_engine.TradingEngine') as mock_engine:
        engine_instance = Mock()
        
        # Mock backtest results
        engine_instance.run_backtest.return_value = {
            'success': True,
            'strategy': 'RSI',
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'results': {
                'total_trades': 150,
                'winning_trades': 90,
                'losing_trades': 60,
                'win_rate': 0.6,
                'total_return': 0.15,
                'max_drawdown': 0.08,
                'sharpe_ratio': 1.2,
                'profit_factor': 1.5,
                'avg_trade_return': 0.001,
                'volatility': 0.02,
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'initial_capital': 10000,
                'final_capital': 11500
            }
        }
        
        mock_engine.return_value = engine_instance
        yield engine_instance


@pytest.fixture
def mock_strategy():
    """Mock trading strategy."""
    strategy = Mock()
    strategy.name = 'TestStrategy'
    strategy.parameters = {'period': 14, 'threshold': 0.7}
    strategy.generate_signals.return_value = [
        {'timestamp': datetime.now(), 'signal': 'BUY', 'confidence': 0.8},
        {'timestamp': datetime.now() + timedelta(hours=1), 'signal': 'SELL', 'confidence': 0.7}
    ]
    return strategy


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    with patch('services.notification_service.NotificationService') as mock_service:
        service_instance = Mock()
        service_instance.send_telegram.return_value = True
        service_instance.send_email.return_value = True
        service_instance.send_discord.return_value = True
        mock_service.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_api_keys():
    """Sample encrypted API keys for testing."""
    return {
        'binance_api_key': 'encrypted_api_key_123',
        'binance_api_secret': 'encrypted_api_secret_456',
        'telegram_token': 'encrypted_telegram_token_789',
        'discord_webhook': 'encrypted_discord_webhook_abc'
    }


@pytest.fixture
def mock_encryption_service():
    """Mock encryption service."""
    with patch('services.encryption_service.EncryptionService') as mock_service:
        service_instance = Mock()
        service_instance.encrypt.return_value = 'encrypted_data'
        service_instance.decrypt.return_value = 'decrypted_data'
        mock_service.return_value = service_instance
        yield service_instance


@pytest.fixture
def mock_jwt_service():
    """Mock JWT service for authentication testing."""
    with patch('services.auth_service.JWTService') as mock_service:
        service_instance = Mock()
        service_instance.generate_token.return_value = 'mock_jwt_token'
        service_instance.verify_token.return_value = {
            'user_id': 1,
            'username': 'testuser',
            'exp': (datetime.now() + timedelta(hours=24)).timestamp()
        }
        mock_service.return_value = service_instance
        yield service_instance


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup code here if needed
    pass


# Custom pytest markers
pytest_configure = lambda config: [
    config.addinivalue_line("markers", "unit: Unit tests"),
    config.addinivalue_line("markers", "integration: Integration tests"),
    config.addinivalue_line("markers", "security: Security tests"),
    config.addinivalue_line("markers", "performance: Performance tests"),
    config.addinivalue_line("markers", "backtest: Backtesting tests"),
    config.addinivalue_line("markers", "strategy: Strategy tests"),
    config.addinivalue_line("markers", "api: API tests"),
    config.addinivalue_line("markers", "database: Database tests"),
    config.addinivalue_line("markers", "slow: Slow running tests"),
    config.addinivalue_line("markers", "fast: Fast running tests")
]


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.fast)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Add strategy marker for backtesting tests
        if "strategy" in item.name.lower() or "backtest" in item.name.lower():
            item.add_marker(pytest.mark.strategy)
            item.add_marker(pytest.mark.backtest)
        
        # Add API marker for API-related tests
        if "api" in item.name.lower() or "endpoint" in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        # Add database marker for database tests
        if "database" in item.name.lower() or "db" in item.name.lower():
            item.add_marker(pytest.mark.database)