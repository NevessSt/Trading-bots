"""Integration tests for database operations and model relationships."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.api_key import APIKey
from models.subscription import Subscription
from db import db


class TestDatabaseIntegration:
    """Test database operations and model relationships."""
    
    def test_user_creation_and_retrieval(self, app_context):
        """Test user creation and retrieval operations."""
        # Create user
        user = User(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Retrieve user
        retrieved_user = User.query.filter_by(username='testuser').first()
        
        assert retrieved_user is not None
        assert retrieved_user.username == 'testuser'
        assert retrieved_user.email == 'test@example.com'
        assert retrieved_user.check_password('password123')
        assert retrieved_user.created_at is not None
    
    def test_user_unique_constraints(self, app_context):
        """Test user unique constraints."""
        # Create first user
        user1 = User(
            username='uniqueuser',
            email='unique@example.com',
            password='password123'
        )
        db.session.add(user1)
        db.session.commit()
        
        # Try to create user with same username
        user2 = User(
            username='uniqueuser',
            email='different@example.com',
            password='password123'
        )
        db.session.add(user2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()
        
        # Try to create user with same email
        user3 = User(
            username='differentuser',
            email='unique@example.com',
            password='password123'
        )
        db.session.add(user3)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
    
    def test_bot_user_relationship(self, app_context):
        """Test bot-user relationship."""
        # Create user
        user = User(
            username='botowner',
            email='botowner@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create bots for user
        bot1 = Bot(
            user_id=user.id,
            name='Bot 1',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14}
        )
        bot2 = Bot(
            user_id=user.id,
            name='Bot 2',
            strategy='macd',
            symbol='ETHUSDT',
            base_amount=500.0,
            config={'fast_period': 12}
        )
        
        db.session.add_all([bot1, bot2])
        db.session.commit()
        
        # Test relationship
        assert len(user.bots) == 2
        assert bot1.user == user
        assert bot2.user == user
        
        # Test querying bots by user
        user_bots = Bot.query.filter_by(user_id=user.id).all()
        assert len(user_bots) == 2
    
    def test_trade_bot_relationship(self, app_context):
        """Test trade-bot relationship."""
        # Create user and bot
        user = User(
            username='trader',
            email='trader@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        bot = Bot(
            user_id=user.id,
            name='Trading Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14}
        )
        db.session.add(bot)
        db.session.commit()
        
        # Create trades for bot
        trade1 = Trade(
            bot_id=bot.id,
            symbol='BTCUSDT',
            side='buy',
            amount=0.001,
            price=50000.0,
            exchange_order_id='order_1',
            status='filled'
        )
        trade2 = Trade(
            bot_id=bot.id,
            symbol='BTCUSDT',
            side='sell',
            amount=0.001,
            price=51000.0,
            exchange_order_id='order_2',
            status='filled'
        )
        
        db.session.add_all([trade1, trade2])
        db.session.commit()
        
        # Test relationship
        assert len(bot.trades) == 2
        assert trade1.bot == bot
        assert trade2.bot == bot
        
        # Test querying trades by bot
        bot_trades = Trade.query.filter_by(bot_id=bot.id).all()
        assert len(bot_trades) == 2
    
    def test_api_key_user_relationship(self, app_context):
        """Test API key-user relationship."""
        # Create user
        user = User(
            username='apiuser',
            email='apiuser@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create API keys for user
        api_key1 = APIKey(
            user_id=user.id,
            exchange='binance',
            key_name='Binance Main',
            api_key='binance_key_1',
            api_secret='binance_secret_1',
            permissions=['read', 'trade']
        )
        api_key2 = APIKey(
            user_id=user.id,
            exchange='coinbase',
            key_name='Coinbase Pro',
            api_key='coinbase_key_1',
            api_secret='coinbase_secret_1',
            permissions=['read']
        )
        
        db.session.add_all([api_key1, api_key2])
        db.session.commit()
        
        # Test relationship
        assert len(user.api_keys) == 2
        assert api_key1.user == user
        assert api_key2.user == user
        
        # Test querying API keys by user
        user_keys = APIKey.query.filter_by(user_id=user.id).all()
        assert len(user_keys) == 2
    
    def test_subscription_user_relationship(self, app_context):
        """Test subscription-user relationship."""
        # Create user
        user = User(
            username='subscriber',
            email='subscriber@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create subscription for user
        subscription = Subscription(
            user_id=user.id,
            plan_type='premium',
            status='active',
            stripe_subscription_id='sub_123',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
        db.session.commit()
        
        # Test relationship
        assert user.subscription == subscription
        assert subscription.user == user
    
    def test_cascade_delete_user_bots(self, app_context):
        """Test cascade delete when user is deleted."""
        # Create user with bots
        user = User(
            username='deleteuser',
            email='deleteuser@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        bot = Bot(
            user_id=user.id,
            name='Delete Test Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14}
        )
        db.session.add(bot)
        db.session.commit()
        
        bot_id = bot.id
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        # Check that bot is also deleted (cascade)
        deleted_bot = Bot.query.get(bot_id)
        assert deleted_bot is None
    
    def test_cascade_delete_bot_trades(self, app_context):
        """Test cascade delete when bot is deleted."""
        # Create user, bot, and trades
        user = User(
            username='tradeuser',
            email='tradeuser@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        bot = Bot(
            user_id=user.id,
            name='Trade Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14}
        )
        db.session.add(bot)
        db.session.commit()
        
        trade = Trade(
            bot_id=bot.id,
            symbol='BTCUSDT',
            side='buy',
            amount=0.001,
            price=50000.0,
            exchange_order_id='cascade_test',
            status='filled'
        )
        db.session.add(trade)
        db.session.commit()
        
        trade_id = trade.id
        
        # Delete bot
        db.session.delete(bot)
        db.session.commit()
        
        # Check that trade is also deleted (cascade)
        deleted_trade = Trade.query.get(trade_id)
        assert deleted_trade is None
    
    def test_complex_query_operations(self, app_context):
        """Test complex database queries."""
        # Create test data
        user1 = User(username='user1', email='user1@example.com', password='pass')
        user2 = User(username='user2', email='user2@example.com', password='pass')
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Create bots for users
        bot1 = Bot(
            user_id=user1.id, name='Bot1', strategy='rsi', 
            symbol='BTCUSDT', base_amount=1000.0, config={},
            is_active=True
        )
        bot2 = Bot(
            user_id=user1.id, name='Bot2', strategy='macd',
            symbol='ETHUSDT', base_amount=500.0, config={},
            is_active=False
        )
        bot3 = Bot(
            user_id=user2.id, name='Bot3', strategy='rsi',
            symbol='BTCUSDT', base_amount=2000.0, config={},
            is_active=True
        )
        db.session.add_all([bot1, bot2, bot3])
        db.session.commit()
        
        # Create trades
        trade1 = Trade(
            bot_id=bot1.id, symbol='BTCUSDT', side='buy',
            amount=0.001, price=50000.0, exchange_order_id='t1',
            status='filled', executed_at=datetime.utcnow() - timedelta(days=1)
        )
        trade2 = Trade(
            bot_id=bot1.id, symbol='BTCUSDT', side='sell',
            amount=0.001, price=51000.0, exchange_order_id='t2',
            status='filled', executed_at=datetime.utcnow()
        )
        trade3 = Trade(
            bot_id=bot3.id, symbol='BTCUSDT', side='buy',
            amount=0.002, price=49000.0, exchange_order_id='t3',
            status='filled', executed_at=datetime.utcnow()
        )
        db.session.add_all([trade1, trade2, trade3])
        db.session.commit()
        
        # Test complex queries
        
        # 1. Get all active bots
        active_bots = Bot.query.filter_by(is_active=True).all()
        assert len(active_bots) == 2
        
        # 2. Get all RSI strategy bots
        rsi_bots = Bot.query.filter_by(strategy='rsi').all()
        assert len(rsi_bots) == 2
        
        # 3. Get all trades for BTCUSDT
        btc_trades = Trade.query.filter_by(symbol='BTCUSDT').all()
        assert len(btc_trades) == 3
        
        # 4. Get trades from last 2 days
        recent_trades = Trade.query.filter(
            Trade.executed_at >= datetime.utcnow() - timedelta(days=2)
        ).all()
        assert len(recent_trades) == 3
        
        # 5. Join query: Get all trades with bot and user info
        trades_with_info = db.session.query(Trade, Bot, User).join(
            Bot, Trade.bot_id == Bot.id
        ).join(
            User, Bot.user_id == User.id
        ).all()
        assert len(trades_with_info) == 3
        
        # 6. Aggregate query: Count trades per bot
        from sqlalchemy import func
        trade_counts = db.session.query(
            Bot.name, func.count(Trade.id).label('trade_count')
        ).join(Trade).group_by(Bot.id).all()
        
        assert len(trade_counts) == 2  # bot1 and bot3 have trades
        
        # Find bot1's trade count
        bot1_count = next((count for name, count in trade_counts if name == 'Bot1'), 0)
        assert bot1_count == 2
    
    def test_transaction_rollback(self, app_context):
        """Test transaction rollback on error."""
        # Create user
        user = User(
            username='rollbackuser',
            email='rollback@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        initial_bot_count = Bot.query.count()
        
        try:
            # Start transaction
            bot1 = Bot(
                user_id=user.id,
                name='Valid Bot',
                strategy='rsi',
                symbol='BTCUSDT',
                base_amount=1000.0,
                config={'rsi_period': 14}
            )
            db.session.add(bot1)
            
            # This should cause an error (invalid user_id)
            bot2 = Bot(
                user_id=99999,  # Non-existent user
                name='Invalid Bot',
                strategy='rsi',
                symbol='BTCUSDT',
                base_amount=1000.0,
                config={'rsi_period': 14}
            )
            db.session.add(bot2)
            db.session.commit()
            
        except IntegrityError:
            db.session.rollback()
        
        # Check that no bots were added
        final_bot_count = Bot.query.count()
        assert final_bot_count == initial_bot_count
    
    def test_bulk_operations(self, app_context):
        """Test bulk database operations."""
        # Create user
        user = User(
            username='bulkuser',
            email='bulk@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create bot
        bot = Bot(
            user_id=user.id,
            name='Bulk Test Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14}
        )
        db.session.add(bot)
        db.session.commit()
        
        # Bulk insert trades
        trades = []
        for i in range(100):
            trade = Trade(
                bot_id=bot.id,
                symbol='BTCUSDT',
                side='buy' if i % 2 == 0 else 'sell',
                amount=0.001,
                price=50000.0 + i,
                exchange_order_id=f'bulk_order_{i}',
                status='filled',
                executed_at=datetime.utcnow() - timedelta(minutes=i)
            )
            trades.append(trade)
        
        db.session.add_all(trades)
        db.session.commit()
        
        # Verify bulk insert
        trade_count = Trade.query.filter_by(bot_id=bot.id).count()
        assert trade_count == 100
        
        # Bulk update
        Trade.query.filter_by(bot_id=bot.id, side='buy').update(
            {'status': 'partially_filled'}
        )
        db.session.commit()
        
        # Verify bulk update
        updated_count = Trade.query.filter_by(
            bot_id=bot.id, status='partially_filled'
        ).count()
        assert updated_count == 50  # Half were buy orders
        
        # Bulk delete
        Trade.query.filter_by(bot_id=bot.id, side='sell').delete()
        db.session.commit()
        
        # Verify bulk delete
        remaining_count = Trade.query.filter_by(bot_id=bot.id).count()
        assert remaining_count == 50  # Only buy orders remain
    
    def test_database_constraints_and_validations(self, app_context):
        """Test database constraints and model validations."""
        # Test user email validation
        with pytest.raises(ValueError):
            user = User(
                username='testuser',
                email='invalid-email',  # Invalid email format
                password='password123'
            )
            user.validate_email()
        
        # Test bot amount constraints
        user = User(
            username='constraintuser',
            email='constraint@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Test negative base amount
        with pytest.raises(ValueError):
            bot = Bot(
                user_id=user.id,
                name='Invalid Bot',
                strategy='rsi',
                symbol='BTCUSDT',
                base_amount=-100.0,  # Negative amount
                config={'rsi_period': 14}
            )
            bot.validate_base_amount()
        
        # Test invalid strategy
        with pytest.raises(ValueError):
            bot = Bot(
                user_id=user.id,
                name='Invalid Strategy Bot',
                strategy='invalid_strategy',
                symbol='BTCUSDT',
                base_amount=1000.0,
                config={}
            )
            bot.validate_strategy()
        
        # Test trade amount constraints
        valid_bot = Bot(
            user_id=user.id,
            name='Valid Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14}
        )
        db.session.add(valid_bot)
        db.session.commit()
        
        with pytest.raises(ValueError):
            trade = Trade(
                bot_id=valid_bot.id,
                symbol='BTCUSDT',
                side='buy',
                amount=0.0,  # Zero amount
                price=50000.0,
                exchange_order_id='invalid_trade',
                status='filled'
            )
            trade.validate_amount()


if __name__ == '__main__':
    pytest.main([__file__])