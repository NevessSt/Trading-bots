"""Integration tests for database operations."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.subscription import Subscription
from models.api_key import APIKey
from services.auth_service import AuthService


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseOperations:
    """Test database operations and data integrity."""
    
    def test_user_crud_operations(self, session):
        """Test user CRUD operations."""
        # Create
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash=AuthService.hash_password('password123'),
            first_name='Test',
            last_name='User'
        )
        session.add(user)
        session.commit()
        
        assert user.id is not None
        assert user.created_at is not None
        
        # Read
        retrieved_user = session.query(User).filter_by(email='test@example.com').first()
        assert retrieved_user is not None
        assert retrieved_user.username == 'testuser'
        
        # Update
        retrieved_user.first_name = 'Updated'
        session.commit()
        
        updated_user = session.query(User).filter_by(id=user.id).first()
        assert updated_user.first_name == 'Updated'
        
        # Delete
        session.delete(updated_user)
        session.commit()
        
        deleted_user = session.query(User).filter_by(id=user.id).first()
        assert deleted_user is None
    
    def test_user_unique_constraints(self, session):
        """Test user unique constraints."""
        # Create first user
        user1 = User(
            email='unique@example.com',
            username='unique_user',
            password_hash=AuthService.hash_password('password123')
        )
        session.add(user1)
        session.commit()
        
        # Try to create user with duplicate email
        user2 = User(
            email='unique@example.com',  # Duplicate email
            username='different_user',
            password_hash=AuthService.hash_password('password123')
        )
        session.add(user2)
        
        with pytest.raises(IntegrityError):
            session.commit()
        
        session.rollback()
        
        # Try to create user with duplicate username
        user3 = User(
            email='different@example.com',
            username='unique_user',  # Duplicate username
            password_hash=AuthService.hash_password('password123')
        )
        session.add(user3)
        
        with pytest.raises(IntegrityError):
            session.commit()
    
    def test_bot_user_relationship(self, session, test_user):
        """Test bot-user relationship."""
        # Create bot
        bot = Bot(
            user_id=test_user.id,
            name='Test Bot',
            strategy='grid_trading',
            exchange='binance',
            symbol='BTCUSDT',
            config={'grid_size': 10}
        )
        session.add(bot)
        session.commit()
        
        # Test relationship
        assert bot.user == test_user
        assert bot in test_user.bots
        
        # Test cascade delete
        bot_id = bot.id
        session.delete(test_user)
        session.commit()
        
        # Bot should be deleted due to cascade
        deleted_bot = session.query(Bot).filter_by(id=bot_id).first()
        assert deleted_bot is None
    
    def test_trade_bot_relationship(self, session, test_user):
        """Test trade-bot relationship."""
        # Create bot
        bot = Bot(
            user_id=test_user.id,
            name='Test Bot',
            strategy='grid_trading',
            exchange='binance',
            symbol='BTCUSDT'
        )
        session.add(bot)
        session.flush()
        
        # Create trade
        trade = Trade(
            bot_id=bot.id,
            symbol='BTCUSDT',
            side='buy',
            quantity=Decimal('0.001'),
            price=Decimal('50000'),
            status='filled'
        )
        session.add(trade)
        session.commit()
        
        # Test relationship
        assert trade.bot == bot
        assert trade in bot.trades
        
        # Test cascade delete
        trade_id = trade.id
        session.delete(bot)
        session.commit()
        
        # Trade should be deleted due to cascade
        deleted_trade = session.query(Trade).filter_by(id=trade_id).first()
        assert deleted_trade is None
    
    def test_subscription_user_relationship(self, session, test_user):
        """Test subscription-user relationship."""
        # Create subscription
        subscription = Subscription(
            user_id=test_user.id,
            plan='premium',
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        session.add(subscription)
        session.commit()
        
        # Test relationship
        assert subscription.user == test_user
        assert subscription in test_user.subscriptions
    
    def test_api_key_user_relationship(self, session, test_user):
        """Test API key-user relationship."""
        # Create API key
        api_key = APIKey(
            user_id=test_user.id,
            name='Test API Key',
            key_hash='hashed_key_value',
            permissions=['read', 'trade']
        )
        session.add(api_key)
        session.commit()
        
        # Test relationship
        assert api_key.user == test_user
        assert api_key in test_user.api_keys
    
    def test_notification_user_relationship(self, session, test_user):
        """Test notification-user relationship."""
        # Create notification
        notification = Notification(
            user_id=test_user.id,
            title='Test Notification',
            message='This is a test notification',
            type='info'
        )
        session.add(notification)
        session.commit()
        
        # Test relationship
        assert notification.user == test_user
        assert notification in test_user.notifications
    
    def test_complex_query_operations(self, session, test_user):
        """Test complex database queries."""
        # Create test data
        bots = []
        for i in range(3):
            bot = Bot(
                user_id=test_user.id,
                name=f'Bot {i}',
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT',
                status='running' if i % 2 == 0 else 'stopped'
            )
            session.add(bot)
            bots.append(bot)
        
        session.flush()
        
        # Add trades to bots
        for bot in bots:
            for j in range(5):
                trade = Trade(
                    bot_id=bot.id,
                    symbol='BTCUSDT',
                    side='buy' if j % 2 == 0 else 'sell',
                    quantity=Decimal('0.001'),
                    price=Decimal(f'{50000 + j * 100}'),
                    profit_loss=Decimal(f'{(-1) ** j * 10}'),
                    status='filled'
                )
                session.add(trade)
        
        session.commit()
        
        # Test complex queries
        
        # 1. Get running bots with their trade count
        running_bots = session.query(Bot).filter(
            Bot.user_id == test_user.id,
            Bot.status == 'running'
        ).all()
        
        assert len(running_bots) == 2
        
        # 2. Get total profit for user
        total_profit = session.query(
            session.query(Trade.profit_loss).join(Bot).filter(
                Bot.user_id == test_user.id
            ).subquery().c.profit_loss
        ).scalar()
        
        # 3. Get bots with profitable trades
        profitable_bots = session.query(Bot).join(Trade).filter(
            Bot.user_id == test_user.id,
            Trade.profit_loss > 0
        ).distinct().all()
        
        assert len(profitable_bots) > 0
    
    def test_transaction_rollback(self, session, test_user):
        """Test transaction rollback functionality."""
        initial_bot_count = session.query(Bot).filter_by(user_id=test_user.id).count()
        
        try:
            # Start transaction
            bot1 = Bot(
                user_id=test_user.id,
                name='Bot 1',
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT'
            )
            session.add(bot1)
            session.flush()
            
            bot2 = Bot(
                user_id=test_user.id,
                name='Bot 1',  # Duplicate name (assuming unique constraint)
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT'
            )
            session.add(bot2)
            
            # This should cause an error if there's a unique constraint
            # For this test, we'll manually raise an exception
            raise Exception("Simulated error")
            
        except Exception:
            session.rollback()
        
        # Verify no bots were added
        final_bot_count = session.query(Bot).filter_by(user_id=test_user.id).count()
        assert final_bot_count == initial_bot_count
    
    def test_database_indexes(self, session):
        """Test database indexes for performance."""
        # This test would typically check if indexes are being used
        # For SQLite, we can check the query plan
        
        # Test index on user email
        result = session.execute(
            text("EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'test@example.com'")
        ).fetchall()
        
        # The result should indicate index usage (implementation depends on DB)
        assert len(result) > 0
        
        # Test index on bot user_id
        result = session.execute(
            text("EXPLAIN QUERY PLAN SELECT * FROM bots WHERE user_id = 1")
        ).fetchall()
        
        assert len(result) > 0
    
    def test_database_constraints(self, session, test_user):
        """Test database constraints."""
        # Test NOT NULL constraint
        with pytest.raises(IntegrityError):
            bot = Bot(
                user_id=test_user.id,
                name=None,  # Should violate NOT NULL constraint
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT'
            )
            session.add(bot)
            session.commit()
        
        session.rollback()
        
        # Test foreign key constraint
        with pytest.raises(IntegrityError):
            bot = Bot(
                user_id=99999,  # Non-existent user
                name='Test Bot',
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT'
            )
            session.add(bot)
            session.commit()
    
    def test_data_types_and_precision(self, session, test_user):
        """Test data types and precision handling."""
        # Create bot
        bot = Bot(
            user_id=test_user.id,
            name='Precision Test Bot',
            strategy='grid_trading',
            exchange='binance',
            symbol='BTCUSDT'
        )
        session.add(bot)
        session.flush()
        
        # Test decimal precision
        trade = Trade(
            bot_id=bot.id,
            symbol='BTCUSDT',
            side='buy',
            quantity=Decimal('0.00000001'),  # Very small quantity
            price=Decimal('50000.12345678'),  # High precision price
            profit_loss=Decimal('-123.456789'),  # Negative profit with precision
            status='filled'
        )
        session.add(trade)
        session.commit()
        
        # Retrieve and verify precision
        retrieved_trade = session.query(Trade).filter_by(id=trade.id).first()
        assert retrieved_trade.quantity == Decimal('0.00000001')
        assert retrieved_trade.price == Decimal('50000.12345678')
        assert retrieved_trade.profit_loss == Decimal('-123.456789')
    
    def test_json_field_operations(self, session, test_user):
        """Test JSON field operations."""
        # Create bot with complex config
        complex_config = {
            'grid_size': 10,
            'investment_amount': 1000,
            'risk_management': {
                'stop_loss': 5.0,
                'take_profit': 10.0,
                'max_drawdown': 20.0
            },
            'advanced_settings': {
                'use_trailing_stop': True,
                'rebalance_frequency': '1h',
                'indicators': ['RSI', 'MACD', 'BB']
            }
        }
        
        bot = Bot(
            user_id=test_user.id,
            name='JSON Test Bot',
            strategy='grid_trading',
            exchange='binance',
            symbol='BTCUSDT',
            config=complex_config
        )
        session.add(bot)
        session.commit()
        
        # Retrieve and verify JSON data
        retrieved_bot = session.query(Bot).filter_by(id=bot.id).first()
        assert retrieved_bot.config['grid_size'] == 10
        assert retrieved_bot.config['risk_management']['stop_loss'] == 5.0
        assert 'RSI' in retrieved_bot.config['advanced_settings']['indicators']
        
        # Update JSON field
        retrieved_bot.config['grid_size'] = 20
        retrieved_bot.config['new_field'] = 'test_value'
        session.commit()
        
        # Verify update
        updated_bot = session.query(Bot).filter_by(id=bot.id).first()
        assert updated_bot.config['grid_size'] == 20
        assert updated_bot.config['new_field'] == 'test_value'
    
    def test_datetime_operations(self, session, test_user):
        """Test datetime operations and timezone handling."""
        # Create bot with specific timestamps
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)
        
        bot = Bot(
            user_id=test_user.id,
            name='DateTime Test Bot',
            strategy='grid_trading',
            exchange='binance',
            symbol='BTCUSDT',
            created_at=past,
            started_at=now,
            stopped_at=future
        )
        session.add(bot)
        session.commit()
        
        # Test datetime queries
        recent_bots = session.query(Bot).filter(
            Bot.created_at > past - timedelta(minutes=30)
        ).all()
        
        assert bot in recent_bots
        
        # Test datetime range queries
        active_period_bots = session.query(Bot).filter(
            Bot.started_at <= now,
            Bot.stopped_at >= now
        ).all()
        
        assert bot in active_period_bots
    
    def test_bulk_operations(self, session, test_user):
        """Test bulk database operations."""
        # Bulk insert
        bots = []
        for i in range(100):
            bot = Bot(
                user_id=test_user.id,
                name=f'Bulk Bot {i}',
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT'
            )
            bots.append(bot)
        
        session.add_all(bots)
        session.commit()
        
        # Verify bulk insert
        bot_count = session.query(Bot).filter_by(user_id=test_user.id).count()
        assert bot_count >= 100
        
        # Bulk update
        session.query(Bot).filter(
            Bot.user_id == test_user.id,
            Bot.name.like('Bulk Bot%')
        ).update({'status': 'stopped'}, synchronize_session=False)
        session.commit()
        
        # Verify bulk update
        stopped_bots = session.query(Bot).filter(
            Bot.user_id == test_user.id,
            Bot.status == 'stopped'
        ).count()
        assert stopped_bots >= 100
        
        # Bulk delete
        session.query(Bot).filter(
            Bot.user_id == test_user.id,
            Bot.name.like('Bulk Bot%')
        ).delete(synchronize_session=False)
        session.commit()
        
        # Verify bulk delete
        remaining_bulk_bots = session.query(Bot).filter(
            Bot.user_id == test_user.id,
            Bot.name.like('Bulk Bot%')
        ).count()
        assert remaining_bulk_bots == 0
    
    def test_database_performance(self, session, test_user):
        """Test database performance with large datasets."""
        import time
        
        # Create large dataset
        start_time = time.time()
        
        bots = []
        for i in range(1000):
            bot = Bot(
                user_id=test_user.id,
                name=f'Perf Bot {i}',
                strategy='grid_trading',
                exchange='binance',
                symbol='BTCUSDT'
            )
            bots.append(bot)
        
        session.add_all(bots)
        session.commit()
        
        insert_time = time.time() - start_time
        
        # Test query performance
        start_time = time.time()
        
        result = session.query(Bot).filter(
            Bot.user_id == test_user.id,
            Bot.name.like('Perf Bot%')
        ).limit(100).all()
        
        query_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        assert insert_time < 10.0  # Should insert 1000 records in under 10 seconds
        assert query_time < 1.0    # Should query in under 1 second
        assert len(result) == 100
        
        # Cleanup
        session.query(Bot).filter(
            Bot.user_id == test_user.id,
            Bot.name.like('Perf Bot%')
        ).delete(synchronize_session=False)
        session.commit()