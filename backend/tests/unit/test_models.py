"""Unit tests for database models."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.subscription import Subscription
from models.api_key import APIKey
from models import db
from werkzeug.security import check_password_hash


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation(self, app_context):
        """Test user creation with valid data."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash is not None
        assert user.password_hash != 'password123'
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
    
    def test_password_hashing(self, app_context):
        """Test password is properly hashed."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert check_password_hash(user.password_hash, 'password123')
        assert not check_password_hash(user.password_hash, 'wrongpassword')
    
    def test_check_password_method(self, app_context):
        """Test check_password method."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False
    
    def test_user_repr(self, app_context):
        """Test user string representation."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        assert repr(user) == '<User testuser>'
    
    def test_user_to_dict(self, app_context):
        """Test user serialization to dictionary."""
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        user.id = 1
        
        user_dict = user.to_dict()
        
        assert user_dict['id'] == 1
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['is_active'] is True
        assert user_dict['is_premium'] is False
        assert 'password_hash' not in user_dict
        assert 'created_at' in user_dict
    
    def test_user_validation_empty_username(self, app_context):
        """Test user validation with empty username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            User(
                username='',
                email='test@example.com',
                password='password123'
            )
    
    def test_user_validation_invalid_email(self, app_context):
        """Test user validation with invalid email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            User(
                username='testuser',
                email='invalid-email',
                password='password123'
            )
    
    def test_user_validation_weak_password(self, app_context):
        """Test user validation with weak password."""
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            User(
                username='testuser',
                email='test@example.com',
                password='123'
            )


class TestBotModel:
    """Test cases for Bot model."""
    
    def test_bot_creation(self, app_context, test_user):
        """Test bot creation with valid data."""
        bot = Bot(
            user_id=test_user.id,
            name='Test Bot',
            strategy='scalping',
            symbol='BTCUSDT',
            base_amount=1000.0
        )
        
        assert bot.name == 'Test Bot'
        assert bot.user_id == test_user.id
        assert bot.strategy == 'scalping'
        assert bot.symbol == 'BTCUSDT'
        assert bot.base_amount == 1000.0
        assert bot.is_active is False
        assert bot.created_at is not None
    
    def test_bot_profit_loss_calculation(self, app_context, test_user):
        """Test bot profit/loss calculation."""
        bot = Bot(
            user_id=test_user.id,
            name='Test Bot',
            strategy='scalping',
            symbol='BTCUSDT',
            base_amount=1000.0
        )
        bot.total_profit_loss = Decimal('200.00')
        
        assert bot.profit_loss == Decimal('200.00')
        assert bot.get_win_rate() == 0
    
    def test_bot_repr(self, app_context, test_user):
        """Test bot string representation."""
        bot = Bot(
            user_id=test_user.id,
            name='Test Bot',
            strategy='scalping',
            symbol='BTCUSDT',
            base_amount=1000.0
        )
        
        assert repr(bot) == '<Bot Test Bot (scalping) - BTCUSDT>'
    
    def test_bot_to_dict(self, app_context, test_user):
        """Test bot serialization to dictionary."""
        bot = Bot(
            user_id=test_user.id,
            name='Test Bot',
            strategy='scalping',
            symbol='BTCUSDT',
            base_amount=1000.0
        )
        bot.id = 1
        
        bot_dict = bot.to_dict()
        
        assert bot_dict['id'] == 1
        assert bot_dict['name'] == 'Test Bot'
        assert bot_dict['strategy'] == 'scalping'
        assert bot_dict['symbol'] == 'BTCUSDT'
        assert bot_dict['base_amount'] == 1000.0
        assert bot_dict['is_active'] is False


class TestTradeModel:
    """Test cases for Trade model."""
    
    def test_trade_creation(self, app_context, test_bot):
        """Test trade creation with valid data."""
        trade = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='buy',
            trade_type='market',
            quantity=Decimal('0.001'),
            price=Decimal('50000.00'),
            bot_id=test_bot.id
        )
        
        assert trade.bot_id == test_bot.id
        assert trade.symbol == 'BTCUSDT'
        assert trade.side == 'buy'
        assert trade.quantity == Decimal('0.001')
        assert trade.price == Decimal('50000.00')
        assert trade.trade_type == 'market'
        assert trade.status == 'pending'
        assert trade.created_at is not None
    
    def test_trade_total_calculation(self, app_context, test_bot):
        """Test trade total calculation."""
        trade = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='buy',
            trade_type='market',
            quantity=Decimal('0.001'),
            price=Decimal('50000.00'),
            bot_id=test_bot.id
        )
        
        assert trade.total == Decimal('50.00')
    
    def test_trade_repr(self, app_context, test_bot):
        """Test trade string representation."""
        trade = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='buy',
            trade_type='market',
            quantity=Decimal('0.001'),
            price=Decimal('50000.00'),
            bot_id=test_bot.id
        )
        
        assert repr(trade) == '<Trade buy 0.001 BTCUSDT>'
    
    def test_trade_to_dict(self, app_context, test_bot):
        """Test trade serialization to dictionary."""
        trade = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='buy',
            trade_type='market',
            quantity=Decimal('0.001'),
            price=Decimal('50000.00'),
            bot_id=test_bot.id
        )
        trade.id = 1
        
        trade_dict = trade.to_dict()
        
        assert trade_dict['id'] == 1
        assert trade_dict['symbol'] == 'BTCUSDT'
        assert trade_dict['side'] == 'buy'
        assert trade_dict['quantity'] == '0.001'
        assert trade_dict['price'] == '50000.00'
        assert trade_dict['total'] == '50.00'
        assert trade_dict['status'] == 'pending'


class TestSubscriptionModel:
    """Test cases for Subscription model."""
    
    def test_subscription_creation(self, app_context, test_user):
        """Test subscription creation with valid data."""
        subscription = Subscription(
            user_id=test_user.id,
            plan_type='pro',
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        assert subscription.user_id == test_user.id
        assert subscription.plan_type == 'pro'
        assert subscription.status == 'active'
        assert subscription.start_date is not None
        assert subscription.end_date is not None
    
    def test_subscription_is_active(self, app_context, test_user):
        """Test subscription active status check."""
        # Active subscription
        active_subscription = Subscription(
            user_id=test_user.id,
            plan_type='pro',
            status='active',
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        assert active_subscription.is_currently_active() is True
        
        # Expired subscription
        expired_subscription = Subscription(
            user_id=test_user.id,
            plan_type='pro',
            status='active',
            start_date=datetime.utcnow() - timedelta(days=31),
            end_date=datetime.utcnow() - timedelta(days=1)
        )
        
        assert expired_subscription.is_currently_active() is False
        
        # Cancelled subscription
        cancelled_subscription = Subscription(
            user_id=test_user.id,
            plan_type='pro',
            status='cancelled',
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        assert cancelled_subscription.is_currently_active() is False


class TestAPIKeyModel:
    """Test cases for APIKey model."""
    
    def test_api_key_creation(self, app_context, test_user):
        """Test API key creation with valid data."""
        api_key = APIKey(
            user_id=test_user.id,
            exchange='binance',
            key_name='My Binance Key',
            api_key='test_api_key',
            api_secret='test_api_secret'
        )
        
        assert api_key.user_id == test_user.id
        assert api_key.exchange == 'binance'
        assert api_key.key_name == 'My Binance Key'
        assert api_key.api_key == 'test_api_key'
        assert api_key.api_secret_hash is not None
        assert api_key.check_secret('test_api_secret') is True
        assert api_key.is_active is True
        assert api_key.created_at is not None
    
    def test_api_key_repr(self, app_context, test_user):
        """Test API key string representation."""
        api_key = APIKey(
            user_id=test_user.id,
            exchange='binance',
            key_name='My Binance Key',
            api_key='test_api_key',
            api_secret='test_api_secret'
        )
        
        assert repr(api_key) == '<APIKey My Binance Key (binance)>'
    
    def test_api_key_to_dict(self, app_context, test_user):
        """Test API key serialization to dictionary."""
        api_key = APIKey(
            user_id=test_user.id,
            exchange='binance',
            key_name='My Binance Key',
            api_key='test_api_key',
            api_secret='test_api_secret'
        )
        api_key.id = 1
        
        api_key_dict = api_key.to_dict()
        
        assert api_key_dict['id'] == 1
        assert api_key_dict['exchange'] == 'binance'
        assert api_key_dict['key_name'] == 'My Binance Key'
        assert api_key_dict['is_active'] is True
        # Sensitive data should not be included
        assert 'api_key' not in api_key_dict
        assert 'api_secret_hash' not in api_key_dict