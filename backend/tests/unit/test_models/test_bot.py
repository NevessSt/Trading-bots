"""Unit tests for Bot model."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from models.bot import Bot
from models.user import User
from models.trade import Trade


@pytest.mark.unit
class TestBotModel:
    """Test Bot model functionality."""
    
    def test_create_bot(self, session, test_user):
        """Test creating a new bot."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config={
                'symbol': 'BTC/USDT',
                'grid_size': 10,
                'profit_target': 0.02
            }
        )
        session.add(bot)
        session.commit()
        
        assert bot.id is not None
        assert bot.name == 'Test Bot'
        assert bot.strategy == 'grid_trading'
        assert bot.user_id == test_user.id
        assert bot.is_active is False
        assert bot.is_paper_trading is True
        assert bot.created_at is not None
        assert bot.updated_at is not None
        assert bot.config['symbol'] == 'BTC/USDT'
    
    def test_bot_user_relationship(self, session, test_user):
        """Test bot-user relationship."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id
        )
        session.add(bot)
        session.commit()
        
        assert bot.user == test_user
        assert bot in test_user.bots
    
    def test_bot_name_unique_per_user(self, session, test_user):
        """Test that bot names must be unique per user."""
        bot1 = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id
        )
        bot2 = Bot(
            name='Test Bot',
            strategy='dca',
            user_id=test_user.id
        )
        
        session.add(bot1)
        session.commit()
        
        session.add(bot2)
        with pytest.raises(IntegrityError):
            session.commit()
    
    def test_bot_repr(self, session, test_user):
        """Test bot string representation."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id
        )
        session.add(bot)
        session.commit()
        
        assert repr(bot) == f'<Bot {bot.name}>'
    
    def test_bot_to_dict(self, session, test_user):
        """Test bot dictionary representation."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config={'symbol': 'BTC/USDT'},
            is_active=True,
            is_paper_trading=False
        )
        session.add(bot)
        session.commit()
        
        bot_dict = bot.to_dict()
        
        assert bot_dict['id'] == bot.id
        assert bot_dict['name'] == 'Test Bot'
        assert bot_dict['strategy'] == 'grid_trading'
        assert bot_dict['user_id'] == test_user.id
        assert bot_dict['is_active'] is True
        assert bot_dict['is_paper_trading'] is False
        assert bot_dict['config'] == {'symbol': 'BTC/USDT'}
        assert 'created_at' in bot_dict
        assert 'updated_at' in bot_dict
    
    def test_bot_start_stop(self, session, test_user):
        """Test bot start/stop functionality."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id
        )
        session.add(bot)
        session.commit()
        
        # Test start
        assert bot.is_active is False
        assert bot.started_at is None
        
        bot.start()
        session.commit()
        
        assert bot.is_active is True
        assert bot.started_at is not None
        assert isinstance(bot.started_at, datetime)
        
        # Test stop
        bot.stop()
        session.commit()
        
        assert bot.is_active is False
        assert bot.stopped_at is not None
        assert isinstance(bot.stopped_at, datetime)
    
    def test_bot_performance_calculation(self, session, test_user):
        """Test bot performance calculation."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            initial_balance=1000.0
        )
        session.add(bot)
        session.commit()
        
        # Add some trades
        trades = [
            Trade(
                bot_id=bot.id,
                symbol='BTC/USDT',
                side='buy',
                amount=0.001,
                price=50000.0,
                status='filled'
            ),
            Trade(
                bot_id=bot.id,
                symbol='BTC/USDT',
                side='sell',
                amount=0.001,
                price=51000.0,
                status='filled'
            )
        ]
        session.add_all(trades)
        session.commit()
        
        # Update performance
        bot.update_performance()
        session.commit()
        
        assert bot.total_trades == 2
        assert bot.profitable_trades == 1
        assert bot.total_profit > 0
        assert bot.win_rate == 0.5
    
    def test_bot_risk_management(self, session, test_user):
        """Test bot risk management."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config={
                'max_drawdown': 0.1,
                'stop_loss': 0.05,
                'daily_loss_limit': 100.0
            },
            initial_balance=1000.0,
            current_balance=900.0  # 10% drawdown
        )
        session.add(bot)
        session.commit()
        
        # Test drawdown check
        assert bot.check_drawdown() is True  # Exceeds max drawdown
        
        # Test daily loss limit
        bot.daily_loss = 150.0
        assert bot.check_daily_loss_limit() is True  # Exceeds daily limit
        
        # Test risk limits
        assert bot.should_stop_trading() is True
    
    def test_bot_config_validation(self, session, test_user):
        """Test bot configuration validation."""
        # Valid grid trading config
        valid_config = {
            'symbol': 'BTC/USDT',
            'grid_size': 10,
            'profit_target': 0.02,
            'investment_amount': 1000
        }
        
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config=valid_config
        )
        session.add(bot)
        session.commit()
        
        assert bot.validate_config() is True
        
        # Invalid config (missing required fields)
        invalid_config = {
            'symbol': 'BTC/USDT'
            # Missing grid_size, profit_target, etc.
        }
        
        bot.config = invalid_config
        assert bot.validate_config() is False
    
    def test_bot_status_tracking(self, session, test_user):
        """Test bot status tracking."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id
        )
        session.add(bot)
        session.commit()
        
        # Test initial status
        assert bot.status == 'inactive'
        
        # Test status changes
        bot.set_status('running')
        assert bot.status == 'running'
        
        bot.set_status('paused')
        assert bot.status == 'paused'
        
        bot.set_status('error', 'Connection failed')
        assert bot.status == 'error'
        assert bot.error_message == 'Connection failed'
    
    def test_bot_trade_history(self, session, test_user):
        """Test bot trade history."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id
        )
        session.add(bot)
        session.commit()
        
        # Add trades
        trades = []
        for i in range(5):
            trade = Trade(
                bot_id=bot.id,
                symbol='BTC/USDT',
                side='buy' if i % 2 == 0 else 'sell',
                amount=0.001,
                price=50000.0 + i * 100,
                status='filled'
            )
            trades.append(trade)
        
        session.add_all(trades)
        session.commit()
        
        # Test trade relationships
        assert len(bot.trades) == 5
        assert all(trade.bot_id == bot.id for trade in bot.trades)
        
        # Test recent trades
        recent_trades = bot.get_recent_trades(limit=3)
        assert len(recent_trades) == 3
    
    def test_bot_profit_calculation(self, session, test_user):
        """Test bot profit calculation methods."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            initial_balance=1000.0
        )
        session.add(bot)
        session.commit()
        
        # Add profitable and losing trades
        trades = [
            Trade(
                bot_id=bot.id,
                symbol='BTC/USDT',
                side='buy',
                amount=0.001,
                price=50000.0,
                profit_loss=10.0,
                status='filled'
            ),
            Trade(
                bot_id=bot.id,
                symbol='BTC/USDT',
                side='sell',
                amount=0.001,
                price=49000.0,
                profit_loss=-10.0,
                status='filled'
            ),
            Trade(
                bot_id=bot.id,
                symbol='BTC/USDT',
                side='buy',
                amount=0.001,
                price=51000.0,
                profit_loss=20.0,
                status='filled'
            )
        ]
        session.add_all(trades)
        session.commit()
        
        # Calculate profits
        total_profit = bot.calculate_total_profit()
        daily_profit = bot.calculate_daily_profit()
        
        assert total_profit == 20.0  # 10 - 10 + 20
        assert daily_profit == 20.0  # All trades today
        
        # Test profit percentage
        profit_percentage = bot.calculate_profit_percentage()
        assert profit_percentage == 2.0  # 20/1000 * 100
    
    def test_bot_strategy_specific_methods(self, session, test_user):
        """Test strategy-specific methods."""
        # Grid trading bot
        grid_bot = Bot(
            name='Grid Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config={
                'symbol': 'BTC/USDT',
                'grid_size': 10,
                'profit_target': 0.02,
                'price_range': [45000, 55000]
            }
        )
        
        # DCA bot
        dca_bot = Bot(
            name='DCA Bot',
            strategy='dca',
            user_id=test_user.id,
            config={
                'symbol': 'ETH/USDT',
                'investment_amount': 100,
                'dca_interval': 3600,
                'max_orders': 10
            }
        )
        
        session.add_all([grid_bot, dca_bot])
        session.commit()
        
        # Test grid-specific methods
        assert grid_bot.get_grid_levels() is not None
        assert grid_bot.calculate_grid_spacing() > 0
        
        # Test DCA-specific methods
        assert dca_bot.get_next_dca_time() is not None
        assert dca_bot.calculate_average_price() >= 0
    
    def test_bot_alerts_and_notifications(self, session, test_user):
        """Test bot alerts and notifications."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config={
                'profit_alert_threshold': 50.0,
                'loss_alert_threshold': -25.0
            }
        )
        session.add(bot)
        session.commit()
        
        # Test profit alert
        bot.total_profit = 60.0
        assert bot.should_send_profit_alert() is True
        
        # Test loss alert
        bot.total_profit = -30.0
        assert bot.should_send_loss_alert() is True
        
        # Test error alert
        bot.set_status('error', 'API connection failed')
        assert bot.should_send_error_alert() is True
    
    def test_bot_backup_and_restore(self, session, test_user):
        """Test bot backup and restore functionality."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config={'symbol': 'BTC/USDT', 'grid_size': 10},
            is_active=True,
            total_profit=100.0
        )
        session.add(bot)
        session.commit()
        
        # Create backup
        backup_data = bot.create_backup()
        
        assert backup_data['name'] == 'Test Bot'
        assert backup_data['strategy'] == 'grid_trading'
        assert backup_data['config']['symbol'] == 'BTC/USDT'
        assert backup_data['total_profit'] == 100.0
        
        # Test restore
        new_bot = Bot.restore_from_backup(backup_data, test_user.id)
        session.add(new_bot)
        session.commit()
        
        assert new_bot.name == bot.name
        assert new_bot.strategy == bot.strategy
        assert new_bot.config == bot.config
        assert new_bot.user_id == test_user.id
    
    def test_bot_clone(self, session, test_user):
        """Test bot cloning functionality."""
        original_bot = Bot(
            name='Original Bot',
            strategy='grid_trading',
            user_id=test_user.id,
            config={'symbol': 'BTC/USDT', 'grid_size': 10}
        )
        session.add(original_bot)
        session.commit()
        
        # Clone bot
        cloned_bot = original_bot.clone('Cloned Bot')
        session.add(cloned_bot)
        session.commit()
        
        assert cloned_bot.name == 'Cloned Bot'
        assert cloned_bot.strategy == original_bot.strategy
        assert cloned_bot.config == original_bot.config
        assert cloned_bot.user_id == original_bot.user_id
        assert cloned_bot.id != original_bot.id
        assert cloned_bot.is_active is False  # Cloned bots start inactive
    
    def test_bot_resource_usage(self, session, test_user):
        """Test bot resource usage tracking."""
        bot = Bot(
            name='Test Bot',
            strategy='grid_trading',
            user_id=test_user.id
        )
        session.add(bot)
        session.commit()
        
        # Track API calls
        bot.increment_api_calls()
        bot.increment_api_calls()
        assert bot.api_calls_today == 2
        
        # Track memory usage
        bot.update_memory_usage(50.5)
        assert bot.memory_usage == 50.5
        
        # Track CPU usage
        bot.update_cpu_usage(25.3)
        assert bot.cpu_usage == 25.3