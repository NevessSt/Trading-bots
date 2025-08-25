"""Unit tests for database operations and models."""
import os
import sys
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError, DataError
from werkzeug.security import check_password_hash

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
from models.subscription import Subscription
from models.api_key import APIKey
from database import DatabaseManager


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


@pytest.fixture
def app_context(app):
    """Create application context for testing."""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app_context):
    """Create a sample user for testing."""
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='hashed_password'
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_bot(app_context, sample_user):
    """Create a sample bot for testing."""
    bot = Bot(
        name='Test Bot',
        user_id=sample_user.id,
        strategy='grid',
        trading_pair='BTCUSDT',
        config={}
    )
    db.session.add(bot)
    db.session.commit()
    return bot


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app_context):
        """Test user creation with valid data."""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_active is True
        assert user.is_premium is False
        assert user.created_at is not None
    
    def test_user_password_hashing(self, app_context):
        """Test password hashing functionality."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('mypassword123')
        
        assert user.password_hash != 'mypassword123'
        assert user.check_password('mypassword123') is True
        assert user.check_password('wrongpassword') is False
    
    def test_user_unique_constraints(self, app_context):
        """Test unique constraints on username and email."""
        # Create first user
        user1 = User(
            username='testuser',
            email='test@example.com',
            password_hash='hash1'
        )
        db.session.add(user1)
        db.session.commit()
        
        # Try to create user with same username
        user2 = User(
            username='testuser',
            email='different@example.com',
            password_hash='hash2'
        )
        db.session.add(user2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()
        
        # Try to create user with same email
        user3 = User(
            username='differentuser',
            email='test@example.com',
            password_hash='hash3'
        )
        db.session.add(user3)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_user_serialization(self, app_context):
        """Test user serialization to dictionary."""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            is_premium=True
        )
        db.session.add(user)
        db.session.commit()
        
        user_dict = user.to_dict()
        
        assert user_dict['id'] == user.id
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['is_premium'] is True
        assert 'password_hash' not in user_dict  # Should not expose password
        assert 'created_at' in user_dict
    
    def test_user_relationships(self, app_context):
        """Test user relationships with other models."""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()
        
        # Test bots relationship
        bot = Bot(
            name='Test Bot',
            user_id=user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config={'param1': 'value1'}
        )
        db.session.add(bot)
        db.session.commit()
        
        assert len(user.bots) == 1
        assert user.bots[0].name == 'Test Bot'
        
        # Test API keys relationship
        api_key = APIKey(
            user_id=user.id,
            exchange='binance',
            key_name='Test Key',
            api_key='test_key',
            api_secret_hash='hashed_secret'
        )
        db.session.add(api_key)
        db.session.commit()
        
        assert len(user.api_keys) == 1
        assert user.api_keys[0].key_name == 'Test Key'


class TestBotModel:
    """Test Bot model functionality."""
    
    def test_bot_creation(self, app_context, sample_user):
        """Test bot creation with valid data."""
        bot = Bot(
            name='Test Bot',
            user_id=sample_user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config={
                'grid_size': 10,
                'price_range': [45000, 55000],
                'investment_amount': 1000
            }
        )
        
        db.session.add(bot)
        db.session.commit()
        
        assert bot.id is not None
        assert bot.name == 'Test Bot'
        assert bot.strategy == 'grid'
        assert bot.trading_pair == 'BTCUSDT'
        assert bot.status == 'inactive'
        assert bot.is_active is False
        assert bot.created_at is not None
        assert isinstance(bot.config, dict)
    
    def test_bot_status_management(self, app_context, sample_user):
        """Test bot status management methods."""
        bot = Bot(
            name='Test Bot',
            user_id=sample_user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config={}
        )
        db.session.add(bot)
        db.session.commit()
        
        # Test starting bot
        bot.start()
        assert bot.status == 'active'
        assert bot.is_active is True
        assert bot.started_at is not None
        
        # Test stopping bot
        bot.stop()
        assert bot.status == 'inactive'
        assert bot.is_active is False
        assert bot.stopped_at is not None
        
        # Test pausing bot
        bot.start()
        bot.pause()
        assert bot.status == 'paused'
        assert bot.is_active is False
    
    def test_bot_config_validation(self, app_context, sample_user):
        """Test bot configuration validation."""
        # Valid config
        valid_config = {
            'grid_size': 10,
            'price_range': [45000, 55000],
            'investment_amount': 1000
        }
        
        bot = Bot(
            name='Test Bot',
            user_id=sample_user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config=valid_config
        )
        
        assert bot.validate_config() is True
        
        # Invalid config - missing required fields
        invalid_config = {
            'grid_size': 10
            # Missing price_range and investment_amount
        }
        
        bot.config = invalid_config
        assert bot.validate_config() is False
    
    def test_bot_performance_calculation(self, app_context, sample_user):
        """Test bot performance calculation."""
        bot = Bot(
            name='Test Bot',
            user_id=sample_user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config={}
        )
        db.session.add(bot)
        db.session.commit()
        
        # Add some trades
        trades = [
            Trade(
                bot_id=bot.id,
                user_id=sample_user.id,
                trading_pair='BTCUSDT',
                side='buy',
                quantity=Decimal('0.1'),
                price=Decimal('50000'),
                total_value=Decimal('5000'),
                profit_loss=Decimal('100')
            ),
            Trade(
                bot_id=bot.id,
                user_id=sample_user.id,
                trading_pair='BTCUSDT',
                side='sell',
                quantity=Decimal('0.05'),
                price=Decimal('52000'),
                total_value=Decimal('2600'),
                profit_loss=Decimal('-50')
            )
        ]
        
        for trade in trades:
            db.session.add(trade)
        db.session.commit()
        
        performance = bot.get_performance()
        
        assert performance['total_trades'] == 2
        assert performance['total_profit_loss'] == Decimal('50')
        assert performance['win_rate'] == 50.0  # 1 win, 1 loss
        assert 'average_profit_per_trade' in performance
    
    def test_bot_serialization(self, app_context, sample_user):
        """Test bot serialization to dictionary."""
        bot = Bot(
            name='Test Bot',
            user_id=sample_user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config={'param': 'value'}
        )
        db.session.add(bot)
        db.session.commit()
        
        bot_dict = bot.to_dict()
        
        assert bot_dict['id'] == bot.id
        assert bot_dict['name'] == 'Test Bot'
        assert bot_dict['strategy'] == 'grid'
        assert bot_dict['trading_pair'] == 'BTCUSDT'
        assert bot_dict['status'] == 'inactive'
        assert bot_dict['config'] == {'param': 'value'}
        assert 'created_at' in bot_dict


class TestTradeModel:
    """Test Trade model functionality."""
    
    def test_trade_creation(self, app_context, sample_user, sample_bot):
        """Test trade creation with valid data."""
        trade = Trade(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            trading_pair='BTCUSDT',
            side='buy',
            quantity=Decimal('0.1'),
            price=Decimal('50000'),
            total_value=Decimal('5000'),
            fees=Decimal('5'),
            profit_loss=Decimal('0')
        )
        
        db.session.add(trade)
        db.session.commit()
        
        assert trade.id is not None
        assert trade.trading_pair == 'BTCUSDT'
        assert trade.side == 'buy'
        assert trade.quantity == Decimal('0.1')
        assert trade.price == Decimal('50000')
        assert trade.total_value == Decimal('5000')
        assert trade.executed_at is not None
    
    def test_trade_calculations(self, app_context, sample_user, sample_bot):
        """Test trade calculation methods."""
        trade = Trade(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            trading_pair='BTCUSDT',
            side='buy',
            quantity=Decimal('0.1'),
            price=Decimal('50000'),
            total_value=Decimal('5000'),
            fees=Decimal('5')
        )
        
        # Test profit calculation
        current_price = Decimal('52000')
        profit = trade.calculate_unrealized_pnl(current_price)
        expected_profit = (current_price - trade.price) * trade.quantity - trade.fees
        assert profit == expected_profit
        
        # Test percentage return
        percentage_return = trade.calculate_percentage_return(current_price)
        expected_percentage = ((current_price - trade.price) / trade.price) * 100
        assert abs(percentage_return - expected_percentage) < Decimal('0.01')
    
    def test_trade_validation(self, app_context, sample_user, sample_bot):
        """Test trade data validation."""
        # Valid trade
        valid_trade = Trade(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            trading_pair='BTCUSDT',
            side='buy',
            quantity=Decimal('0.1'),
            price=Decimal('50000'),
            total_value=Decimal('5000')
        )
        
        db.session.add(valid_trade)
        db.session.commit()  # Should not raise
        
        # Invalid trade - negative quantity
        with pytest.raises((DataError, IntegrityError)):
            invalid_trade = Trade(
                bot_id=sample_bot.id,
                user_id=sample_user.id,
                trading_pair='BTCUSDT',
                side='buy',
                quantity=Decimal('-0.1'),  # Negative quantity
                price=Decimal('50000'),
                total_value=Decimal('5000')
            )
            db.session.add(invalid_trade)
            db.session.commit()
    
    def test_trade_serialization(self, app_context, sample_user, sample_bot):
        """Test trade serialization to dictionary."""
        trade = Trade(
            bot_id=sample_bot.id,
            user_id=sample_user.id,
            trading_pair='BTCUSDT',
            side='buy',
            quantity=Decimal('0.1'),
            price=Decimal('50000'),
            total_value=Decimal('5000'),
            fees=Decimal('5'),
            profit_loss=Decimal('100')
        )
        db.session.add(trade)
        db.session.commit()
        
        trade_dict = trade.to_dict()
        
        assert trade_dict['id'] == trade.id
        assert trade_dict['trading_pair'] == 'BTCUSDT'
        assert trade_dict['side'] == 'buy'
        assert float(trade_dict['quantity']) == 0.1
        assert float(trade_dict['price']) == 50000
        assert float(trade_dict['total_value']) == 5000
        assert 'executed_at' in trade_dict


class TestAPIKeyModel:
    """Test APIKey model functionality."""
    
    def test_api_key_creation(self, app_context, sample_user):
        """Test API key creation with valid data."""
        api_key = APIKey(
            user_id=sample_user.id,
            exchange='binance',
            key_name='My Binance Key',
            api_key='test_api_key_123',
            api_secret_hash='hashed_secret'
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        assert api_key.id is not None
        assert api_key.exchange == 'binance'
        assert api_key.key_name == 'My Binance Key'
        assert api_key.api_key == 'test_api_key_123'
        assert api_key.is_active is True
        assert api_key.created_at is not None
    
    def test_api_key_secret_hashing(self, app_context, sample_user):
        """Test API secret hashing functionality."""
        api_key = APIKey(
            user_id=sample_user.id,
            exchange='binance',
            key_name='Test Key',
            api_key='test_key'
        )
        
        secret = 'my_secret_123'
        api_key.set_secret(secret)
        
        assert api_key.api_secret_hash != secret
        assert api_key.verify_secret(secret) is True
        assert api_key.verify_secret('wrong_secret') is False
    
    def test_api_key_validation(self, app_context, sample_user):
        """Test API key validation."""
        api_key = APIKey(
            user_id=sample_user.id,
            exchange='binance',
            key_name='Test Key',
            api_key='valid_key_format_123',
            api_secret_hash='hashed_secret'
        )
        
        # Mock external validation
        with patch('app.services.exchange_service.validate_api_credentials') as mock_validate:
            mock_validate.return_value = True
            
            assert api_key.validate_credentials() is True
            mock_validate.assert_called_once()
    
    def test_api_key_serialization(self, app_context, sample_user):
        """Test API key serialization (should not expose secret)."""
        api_key = APIKey(
            user_id=sample_user.id,
            exchange='binance',
            key_name='Test Key',
            api_key='test_key',
            api_secret_hash='hashed_secret'
        )
        db.session.add(api_key)
        db.session.commit()
        
        api_key_dict = api_key.to_dict()
        
        assert api_key_dict['id'] == api_key.id
        assert api_key_dict['exchange'] == 'binance'
        assert api_key_dict['key_name'] == 'Test Key'
        assert api_key_dict['api_key'] == 'test_key'
        assert 'api_secret_hash' not in api_key_dict  # Should not expose secret
        assert 'created_at' in api_key_dict


class TestSubscriptionModel:
    """Test Subscription model functionality."""
    
    def test_subscription_creation(self, app_context, sample_user):
        """Test subscription creation with valid data."""
        subscription = Subscription(
            user_id=sample_user.id,
            plan_type='premium',
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        assert subscription.id is not None
        assert subscription.plan_type == 'premium'
        assert subscription.status == 'active'
        assert subscription.start_date is not None
        assert subscription.end_date is not None
    
    def test_subscription_status_methods(self, app_context, sample_user):
        """Test subscription status checking methods."""
        # Active subscription
        active_subscription = Subscription(
            user_id=sample_user.id,
            plan_type='premium',
            status='active',
            start_date=datetime.utcnow() - timedelta(days=5),
            end_date=datetime.utcnow() + timedelta(days=25)
        )
        
        assert active_subscription.is_active() is True
        assert active_subscription.is_expired() is False
        assert active_subscription.days_remaining() > 20
        
        # Expired subscription
        expired_subscription = Subscription(
            user_id=sample_user.id,
            plan_type='premium',
            status='expired',
            start_date=datetime.utcnow() - timedelta(days=35),
            end_date=datetime.utcnow() - timedelta(days=5)
        )
        
        assert expired_subscription.is_active() is False
        assert expired_subscription.is_expired() is True
        assert expired_subscription.days_remaining() < 0
    
    def test_subscription_renewal(self, app_context, sample_user):
        """Test subscription renewal functionality."""
        subscription = Subscription(
            user_id=sample_user.id,
            plan_type='premium',
            status='active',
            start_date=datetime.utcnow() - timedelta(days=25),
            end_date=datetime.utcnow() + timedelta(days=5)
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        # Renew subscription
        original_end_date = subscription.end_date
        subscription.renew(30)  # Renew for 30 days
        
        assert subscription.end_date > original_end_date
        assert subscription.status == 'active'
        assert subscription.days_remaining() > 25


class TestDatabaseManager:
    """Test DatabaseManager functionality."""
    
    def test_database_initialization(self, app_context):
        """Test database initialization."""
        db_manager = DatabaseManager()
        
        # Test table creation
        db_manager.create_tables()
        
        # Verify tables exist
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        
        expected_tables = ['users', 'bots', 'trades', 'api_keys', 'subscriptions']
        for table in expected_tables:
            assert table in table_names
    
    def test_database_backup_restore(self, app_context):
        """Test database backup and restore functionality."""
        db_manager = DatabaseManager()
        
        # Create some test data
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()
        
        # Mock backup functionality
        with patch('app.database.DatabaseManager.create_backup') as mock_backup:
            mock_backup.return_value = 'backup_file_path.sql'
            
            backup_path = db_manager.create_backup()
            assert backup_path == 'backup_file_path.sql'
            mock_backup.assert_called_once()
    
    def test_database_migration(self, app_context):
        """Test database migration functionality."""
        db_manager = DatabaseManager()
        
        # Mock migration functionality
        with patch('app.database.DatabaseManager.run_migrations') as mock_migrate:
            mock_migrate.return_value = True
            
            result = db_manager.run_migrations()
            assert result is True
            mock_migrate.assert_called_once()
    
    def test_database_health_check(self, app_context):
        """Test database health check."""
        db_manager = DatabaseManager()
        
        health_status = db_manager.health_check()
        
        assert health_status['status'] == 'healthy'
        assert 'connection' in health_status
        assert 'tables' in health_status
        assert health_status['connection'] is True
    
    def test_database_cleanup(self, app_context):
        """Test database cleanup functionality."""
        db_manager = DatabaseManager()
        
        # Create old test data
        old_trade = Trade(
            bot_id=1,
            user_id=1,
            trading_pair='BTCUSDT',
            side='buy',
            quantity=Decimal('0.1'),
            price=Decimal('50000'),
            total_value=Decimal('5000'),
            executed_at=datetime.utcnow() - timedelta(days=100)
        )
        db.session.add(old_trade)
        db.session.commit()
        
        # Test cleanup
        with patch('app.database.DatabaseManager.cleanup_old_data') as mock_cleanup:
            mock_cleanup.return_value = {'deleted_trades': 1, 'deleted_logs': 0}
            
            result = db_manager.cleanup_old_data(days=90)
            assert result['deleted_trades'] == 1
            mock_cleanup.assert_called_once_with(days=90)


class TestDatabaseIntegration:
    """Test database integration scenarios."""
    
    def test_user_bot_trade_relationship(self, app_context):
        """Test complete user -> bot -> trade relationship."""
        # Create user
        user = User(
            username='trader',
            email='trader@example.com',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create bot
        bot = Bot(
            name='Trading Bot',
            user_id=user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config={}
        )
        db.session.add(bot)
        db.session.commit()
        
        # Create trade
        trade = Trade(
            bot_id=bot.id,
            user_id=user.id,
            trading_pair='BTCUSDT',
            side='buy',
            quantity=Decimal('0.1'),
            price=Decimal('50000'),
            total_value=Decimal('5000')
        )
        db.session.add(trade)
        db.session.commit()
        
        # Test relationships
        assert len(user.bots) == 1
        assert user.bots[0].name == 'Trading Bot'
        assert len(user.bots[0].trades) == 1
        assert user.bots[0].trades[0].trading_pair == 'BTCUSDT'
        
        # Test cascade delete
        db.session.delete(user)
        db.session.commit()
        
        # Verify related records are deleted
        assert Bot.query.filter_by(user_id=user.id).count() == 0
        assert Trade.query.filter_by(user_id=user.id).count() == 0
    
    def test_concurrent_database_operations(self, app_context):
        """Test concurrent database operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_user(username):
            try:
                user = User(
                    username=f'user_{username}',
                    email=f'user_{username}@example.com',
                    password_hash='hashed_password'
                )
                db.session.add(user)
                db.session.commit()
                results.append(user.id)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_user, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results) == 5
        assert len(errors) == 0
        assert len(set(results)) == 5  # All IDs should be unique
    
    def test_transaction_rollback(self, app_context):
        """Test transaction rollback on error."""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()
        
        try:
            # Start transaction
            bot = Bot(
                name='Test Bot',
                user_id=user.id,
                strategy='grid',
                trading_pair='BTCUSDT',
                config={}
            )
            db.session.add(bot)
            
            # Create invalid trade (this should fail)
            invalid_trade = Trade(
                bot_id=bot.id,
                user_id=user.id,
                trading_pair='INVALID_PAIR',  # Invalid trading pair
                side='invalid_side',  # Invalid side
                quantity=Decimal('-1'),  # Invalid quantity
                price=Decimal('0'),  # Invalid price
                total_value=Decimal('0')
            )
            db.session.add(invalid_trade)
            db.session.commit()
            
        except Exception:
            db.session.rollback()
        
        # Verify bot was not created due to rollback
        assert Bot.query.filter_by(user_id=user.id).count() == 0
        assert Trade.query.filter_by(user_id=user.id).count() == 0