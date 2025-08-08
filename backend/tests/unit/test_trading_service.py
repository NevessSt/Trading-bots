"""Unit tests for trading service."""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta

from services.trading_service import TradingService
from models.bot import Bot
from models.trade import Trade
from models.api_key import APIKey
from models import db


class TestTradingService:
    """Test cases for TradingService."""
    
    def test_create_bot_success(self, app_context, test_user, test_api_key):
        """Test successful bot creation."""
        trading_service = TradingService()
        
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'scalping',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'initial_balance': '1000.00',
            'api_key_id': test_api_key.id
        }
        
        with patch.object(db.session, 'add') as mock_add, \
             patch.object(db.session, 'commit') as mock_commit:
            
            result = trading_service.create_bot(test_user.id, bot_data)
            
            assert result['success'] is True
            assert result['message'] == 'Bot created successfully'
            assert 'bot' in result
            assert result['bot']['name'] == 'Test Bot'
            assert result['bot']['strategy'] == 'scalping'
            
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
    
    def test_create_bot_invalid_api_key(self, app_context, test_user):
        """Test bot creation with invalid API key."""
        trading_service = TradingService()
        
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'scalping',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'initial_balance': '1000.00',
            'api_key_id': 999  # Non-existent API key
        }
        
        with patch.object(APIKey, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            result = trading_service.create_bot(test_user.id, bot_data)
            
            assert result['success'] is False
            assert 'Invalid API key' in result['message']
    
    def test_start_bot_success(self, app_context, test_bot):
        """Test successful bot start."""
        trading_service = TradingService()
        
        with patch.object(trading_service, '_validate_bot_configuration', return_value=True), \
             patch.object(trading_service, '_initialize_exchange_connection', return_value=True), \
             patch.object(db.session, 'commit') as mock_commit:
            
            result = trading_service.start_bot(test_bot.id)
            
            assert result['success'] is True
            assert result['message'] == 'Bot started successfully'
            assert test_bot.is_active is True
            mock_commit.assert_called_once()
    
    def test_start_bot_already_active(self, app_context, test_bot):
        """Test starting an already active bot."""
        trading_service = TradingService()
        test_bot.is_active = True
        
        result = trading_service.start_bot(test_bot.id)
        
        assert result['success'] is False
        assert 'Bot is already active' in result['message']
    
    def test_stop_bot_success(self, app_context, test_bot):
        """Test successful bot stop."""
        trading_service = TradingService()
        test_bot.is_active = True
        
        with patch.object(trading_service, '_close_open_positions') as mock_close, \
             patch.object(db.session, 'commit') as mock_commit:
            
            result = trading_service.stop_bot(test_bot.id)
            
            assert result['success'] is True
            assert result['message'] == 'Bot stopped successfully'
            assert test_bot.is_active is False
            mock_close.assert_called_once()
            mock_commit.assert_called_once()
    
    def test_stop_bot_not_active(self, app_context, test_bot):
        """Test stopping an inactive bot."""
        trading_service = TradingService()
        test_bot.is_active = False
        
        result = trading_service.stop_bot(test_bot.id)
        
        assert result['success'] is False
        assert 'Bot is not active' in result['message']
    
    def test_execute_trade_buy_success(self, app_context, test_bot):
        """Test successful buy trade execution."""
        trading_service = TradingService()
        
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': '0.001',
            'price': '50000.00',
            'trade_type': 'limit'
        }
        
        mock_exchange_response = {
            'id': 'exchange_order_id',
            'status': 'filled',
            'filled': 0.001,
            'average': 50000.00
        }
        
        with patch.object(trading_service, '_get_exchange_client') as mock_exchange, \
             patch.object(db.session, 'add') as mock_add, \
             patch.object(db.session, 'commit') as mock_commit:
            
            mock_exchange.return_value.create_order.return_value = mock_exchange_response
            
            result = trading_service.execute_trade(test_bot.id, trade_data)
            
            assert result['success'] is True
            assert result['message'] == 'Trade executed successfully'
            assert 'trade' in result
            
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
    
    def test_execute_trade_insufficient_balance(self, app_context, test_bot):
        """Test trade execution with insufficient balance."""
        trading_service = TradingService()
        test_bot.current_balance = Decimal('10.00')  # Low balance
        
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': '1.0',  # Large quantity
            'price': '50000.00',
            'trade_type': 'limit'
        }
        
        result = trading_service.execute_trade(test_bot.id, trade_data)
        
        assert result['success'] is False
        assert 'Insufficient balance' in result['message']
    
    def test_execute_trade_exchange_error(self, app_context, test_bot):
        """Test trade execution with exchange error."""
        trading_service = TradingService()
        
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': '0.001',
            'price': '50000.00',
            'trade_type': 'limit'
        }
        
        with patch.object(trading_service, '_get_exchange_client') as mock_exchange:
            mock_exchange.return_value.create_order.side_effect = Exception('Exchange error')
            
            result = trading_service.execute_trade(test_bot.id, trade_data)
            
            assert result['success'] is False
            assert 'Exchange error' in result['message']
    
    def test_get_market_data_success(self, app_context):
        """Test successful market data retrieval."""
        trading_service = TradingService()
        
        mock_ticker = {
            'symbol': 'BTCUSDT',
            'last': 50000.00,
            'bid': 49999.00,
            'ask': 50001.00,
            'high': 51000.00,
            'low': 49000.00,
            'volume': 1000.0
        }
        
        with patch.object(trading_service, '_get_exchange_client') as mock_exchange:
            mock_exchange.return_value.fetch_ticker.return_value = mock_ticker
            
            result = trading_service.get_market_data('binance', 'BTCUSDT')
            
            assert result['success'] is True
            assert result['data']['symbol'] == 'BTCUSDT'
            assert result['data']['last'] == 50000.00
    
    def test_get_market_data_error(self, app_context):
        """Test market data retrieval with error."""
        trading_service = TradingService()
        
        with patch.object(trading_service, '_get_exchange_client') as mock_exchange:
            mock_exchange.return_value.fetch_ticker.side_effect = Exception('Market data error')
            
            result = trading_service.get_market_data('binance', 'BTCUSDT')
            
            assert result['success'] is False
            assert 'Market data error' in result['message']
    
    def test_get_bot_performance(self, app_context, test_bot):
        """Test bot performance calculation."""
        trading_service = TradingService()
        
        # Create some mock trades
        mock_trades = [
            MagicMock(side='buy', quantity=Decimal('0.001'), price=Decimal('50000'), total=Decimal('50')),
            MagicMock(side='sell', quantity=Decimal('0.001'), price=Decimal('52000'), total=Decimal('52'))
        ]
        
        with patch.object(Trade, 'query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = mock_trades
            
            result = trading_service.get_bot_performance(test_bot.id)
            
            assert result['success'] is True
            assert 'performance' in result
            assert 'total_trades' in result['performance']
            assert 'profit_loss' in result['performance']
    
    def test_update_bot_configuration(self, app_context, test_bot):
        """Test bot configuration update."""
        trading_service = TradingService()
        
        update_data = {
            'name': 'Updated Bot Name',
            'strategy': 'grid_trading'
        }
        
        with patch.object(db.session, 'commit') as mock_commit:
            
            result = trading_service.update_bot_configuration(test_bot.id, update_data)
            
            assert result['success'] is True
            assert result['message'] == 'Bot configuration updated successfully'
            assert test_bot.name == 'Updated Bot Name'
            assert test_bot.strategy == 'grid_trading'
            mock_commit.assert_called_once()
    
    def test_delete_bot_success(self, app_context, test_bot):
        """Test successful bot deletion."""
        trading_service = TradingService()
        test_bot.is_active = False  # Bot must be inactive to delete
        
        with patch.object(db.session, 'delete') as mock_delete, \
             patch.object(db.session, 'commit') as mock_commit:
            
            result = trading_service.delete_bot(test_bot.id)
            
            assert result['success'] is True
            assert result['message'] == 'Bot deleted successfully'
            mock_delete.assert_called_once_with(test_bot)
            mock_commit.assert_called_once()
    
    def test_delete_bot_active(self, app_context, test_bot):
        """Test deletion of active bot (should fail)."""
        trading_service = TradingService()
        test_bot.is_active = True
        
        result = trading_service.delete_bot(test_bot.id)
        
        assert result['success'] is False
        assert 'Cannot delete active bot' in result['message']
    
    def test_get_trade_history(self, app_context, test_bot):
        """Test trade history retrieval."""
        trading_service = TradingService()
        
        mock_trades = [
            MagicMock(id=1, symbol='BTCUSDT', side='buy'),
            MagicMock(id=2, symbol='BTCUSDT', side='sell')
        ]
        
        with patch.object(Trade, 'query') as mock_query:
            mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_trades
            
            result = trading_service.get_trade_history(test_bot.id, limit=10)
            
            assert result['success'] is True
            assert len(result['trades']) == 2
    
    def test_calculate_risk_metrics(self, app_context, test_bot):
        """Test risk metrics calculation."""
        trading_service = TradingService()
        
        # Mock historical trades for risk calculation
        mock_trades = [
            MagicMock(profit_loss=Decimal('100')),
            MagicMock(profit_loss=Decimal('-50')),
            MagicMock(profit_loss=Decimal('200')),
            MagicMock(profit_loss=Decimal('-25'))
        ]
        
        with patch.object(Trade, 'query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = mock_trades
            
            result = trading_service.calculate_risk_metrics(test_bot.id)
            
            assert result['success'] is True
            assert 'risk_metrics' in result
            assert 'sharpe_ratio' in result['risk_metrics']
            assert 'max_drawdown' in result['risk_metrics']
            assert 'win_rate' in result['risk_metrics']
    
    def test_backtest_strategy(self, app_context, test_bot):
        """Test strategy backtesting."""
        trading_service = TradingService()
        
        backtest_params = {
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'initial_balance': 1000.0
        }
        
        mock_historical_data = [
            {'timestamp': '2023-01-01', 'open': 50000, 'high': 51000, 'low': 49000, 'close': 50500},
            {'timestamp': '2023-01-02', 'open': 50500, 'high': 52000, 'low': 50000, 'close': 51500}
        ]
        
        with patch.object(trading_service, '_fetch_historical_data', return_value=mock_historical_data), \
             patch.object(trading_service, '_run_backtest_simulation') as mock_simulation:
            
            mock_simulation.return_value = {
                'total_return': 15.5,
                'max_drawdown': -5.2,
                'sharpe_ratio': 1.8,
                'total_trades': 25
            }
            
            result = trading_service.backtest_strategy(test_bot.id, backtest_params)
            
            assert result['success'] is True
            assert 'backtest_results' in result
            assert result['backtest_results']['total_return'] == 15.5
    
    def test_get_portfolio_summary(self, app_context, test_user):
        """Test portfolio summary generation."""
        trading_service = TradingService()
        
        mock_bots = [
            MagicMock(id=1, name='Bot 1', current_balance=Decimal('1200'), initial_balance=Decimal('1000')),
            MagicMock(id=2, name='Bot 2', current_balance=Decimal('800'), initial_balance=Decimal('1000'))
        ]
        
        with patch.object(Bot, 'query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = mock_bots
            
            result = trading_service.get_portfolio_summary(test_user.id)
            
            assert result['success'] is True
            assert 'portfolio' in result
            assert result['portfolio']['total_balance'] == '2000.00'
            assert result['portfolio']['total_profit_loss'] == '200.00'
    
    def test_validate_trading_parameters(self, app_context):
        """Test trading parameter validation."""
        trading_service = TradingService()
        
        # Valid parameters
        valid_params = {
            'symbol': 'BTCUSDT',
            'quantity': '0.001',
            'price': '50000.00',
            'side': 'buy'
        }
        
        result = trading_service._validate_trading_parameters(valid_params)
        assert result['valid'] is True
        
        # Invalid parameters
        invalid_params = {
            'symbol': '',  # Empty symbol
            'quantity': '-0.001',  # Negative quantity
            'price': '0',  # Zero price
            'side': 'invalid'  # Invalid side
        }
        
        result = trading_service._validate_trading_parameters(invalid_params)
        assert result['valid'] is False
        assert 'errors' in result