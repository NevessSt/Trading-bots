import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from services.trading_service import TradingService
from models.bot import Bot
from models.user import User


class TestBotLifecycle:
    """Test bot lifecycle management including creation, start, stop, and deletion."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock()
        user.id = 1
        user.username = "testuser"
        return user
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot for testing."""
        bot = Mock()
        bot.id = 1
        bot.name = "Test Bot"
        bot.symbol = "BTCUSDT"
        bot.strategy = "moving_average"
        bot.status = "inactive"
        bot.user_id = 1
        bot.created_at = datetime.now()
        return bot
    
    @pytest.fixture
    def trading_service(self):
        """Create TradingService instance for testing."""
        return TradingService()
    
    @patch('services.trading_service.db')
    def test_create_bot_success(self, mock_db, trading_service, mock_user):
        """Test successful bot creation."""
        bot_data = {
            'name': 'Test Bot',
            'symbol': 'BTCUSDT',
            'strategy': 'moving_average',
            'parameters': {'period': 20, 'threshold': 0.02}
        }
        
        mock_db.session.add = MagicMock()
        mock_db.session.commit = MagicMock()
        
        with patch('services.trading_service.Bot') as mock_bot_class:
            mock_bot_instance = Mock()
            mock_bot_instance.id = 1
            mock_bot_class.return_value = mock_bot_instance
            
            result = trading_service.create_bot(mock_user.id, bot_data)
            
            assert result is not None
            mock_db.session.add.assert_called_once()
            mock_db.session.commit.assert_called_once()
    
    def test_create_bot_invalid_strategy(self, trading_service, mock_user):
        """Test bot creation fails with invalid strategy."""
        bot_data = {
            'name': 'Test Bot',
            'symbol': 'BTCUSDT',
            'strategy': 'invalid_strategy',
            'parameters': {}
        }
        
        with pytest.raises(ValueError, match="Invalid strategy"):
            trading_service.create_bot(mock_user.id, bot_data)
    
    def test_create_bot_invalid_symbol(self, trading_service, mock_user):
        """Test bot creation fails with invalid symbol."""
        bot_data = {
            'name': 'Test Bot',
            'symbol': 'INVALID',
            'strategy': 'moving_average',
            'parameters': {'period': 20}
        }
        
        with pytest.raises(ValueError, match="Invalid trading symbol"):
            trading_service.create_bot(mock_user.id, bot_data)
    
    @patch('services.trading_service.db')
    @patch('services.trading_service.get_trading_engine')
    def test_start_bot_success(self, mock_get_engine, mock_db, trading_service, mock_bot):
        """Test successful bot start."""
        mock_bot.status = "inactive"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        mock_db.session.commit = MagicMock()
        
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine
        
        with patch('services.trading_service.BotManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager.return_value = mock_manager_instance
            
            result = trading_service.start_bot(1, 1)
            
            assert result['status'] == 'success'
            mock_manager_instance.start_bot.assert_called_once()
    
    @patch('services.trading_service.db')
    def test_start_bot_already_active(self, mock_db, trading_service, mock_bot):
        """Test starting an already active bot returns appropriate message."""
        mock_bot.status = "active"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        
        result = trading_service.start_bot(1, 1)
        
        assert result['status'] == 'info'
        assert 'already active' in result['message']
    
    @patch('services.trading_service.db')
    def test_start_bot_not_found(self, mock_db, trading_service):
        """Test starting non-existent bot raises error."""
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Bot not found"):
            trading_service.start_bot(1, 999)
    
    @patch('services.trading_service.db')
    def test_stop_bot_success(self, mock_db, trading_service, mock_bot):
        """Test successful bot stop."""
        mock_bot.status = "active"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        mock_db.session.commit = MagicMock()
        
        with patch('services.trading_service.BotManager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager.return_value = mock_manager_instance
            
            result = trading_service.stop_bot(1, 1)
            
            assert result['status'] == 'success'
            mock_manager_instance.stop_bot.assert_called_once()
    
    @patch('services.trading_service.db')
    def test_stop_bot_already_inactive(self, mock_db, trading_service, mock_bot):
        """Test stopping an already inactive bot returns appropriate message."""
        mock_bot.status = "inactive"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        
        result = trading_service.stop_bot(1, 1)
        
        assert result['status'] == 'info'
        assert 'already inactive' in result['message']
    
    @patch('services.trading_service.db')
    def test_delete_bot_success(self, mock_db, trading_service, mock_bot):
        """Test successful bot deletion."""
        mock_bot.status = "inactive"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        mock_db.session.delete = MagicMock()
        mock_db.session.commit = MagicMock()
        
        result = trading_service.delete_bot(1, 1)
        
        assert result['status'] == 'success'
        mock_db.session.delete.assert_called_once_with(mock_bot)
        mock_db.session.commit.assert_called_once()
    
    @patch('services.trading_service.db')
    def test_delete_active_bot_fails(self, mock_db, trading_service, mock_bot):
        """Test deleting an active bot fails."""
        mock_bot.status = "active"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        
        with pytest.raises(ValueError, match="Cannot delete active bot"):
            trading_service.delete_bot(1, 1)
    
    @patch('services.trading_service.db')
    def test_get_bot_performance(self, mock_db, trading_service, mock_bot):
        """Test getting bot performance metrics."""
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        
        with patch('services.trading_service.PerformanceCalculator') as mock_calc:
            mock_calc_instance = Mock()
            mock_calc_instance.calculate_performance.return_value = {
                'total_return': 0.15,
                'win_rate': 0.65,
                'total_trades': 50,
                'profit_loss': 150.0
            }
            mock_calc.return_value = mock_calc_instance
            
            performance = trading_service.get_bot_performance(1, 1)
            
            assert performance['total_return'] == 0.15
            assert performance['win_rate'] == 0.65
            assert performance['total_trades'] == 50
    
    @patch('services.trading_service.db')
    def test_update_bot_parameters(self, mock_db, trading_service, mock_bot):
        """Test updating bot parameters."""
        mock_bot.status = "inactive"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        mock_db.session.commit = MagicMock()
        
        new_params = {'period': 30, 'threshold': 0.03}
        
        result = trading_service.update_bot(1, 1, {'parameters': new_params})
        
        assert result['status'] == 'success'
        mock_db.session.commit.assert_called_once()
    
    @patch('services.trading_service.db')
    def test_update_active_bot_fails(self, mock_db, trading_service, mock_bot):
        """Test updating an active bot fails."""
        mock_bot.status = "active"
        mock_db.session.query.return_value.filter_by.return_value.first.return_value = mock_bot
        
        with pytest.raises(ValueError, match="Cannot update active bot"):
            trading_service.update_bot(1, 1, {'parameters': {'period': 30}})