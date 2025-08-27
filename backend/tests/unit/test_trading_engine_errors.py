"""Unit tests for trading engine error handling and bot lifecycle."""
import pytest
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal

from bot_engine.trading_engine import TradingEngine
from models.user import User
from models.bot import Bot
from models.api_key import APIKey


class TestTradingEngineErrors:
    """Test trading engine error handling scenarios."""
    
    def test_bot_start_missing_api_keys(self, app_context):
        """Test bot start fails when API keys are missing."""
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            with pytest.raises(ValueError, match="MISSING_API_KEYS"):
                engine = TradingEngine(user_id=1)
    
    def test_bot_start_invalid_strategy(self, app_context):
        """Test bot start fails with invalid strategy."""
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        mock_api_key.api_key = 'test_key'
        mock_api_key.api_secret = 'test_secret'
        mock_api_key.exchange = 'binance'
        mock_api_key.testnet = True
        
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query, \
             patch('bot_engine.trading_engine.ccxt.binance') as mock_exchange:
            
            mock_query.filter_by.return_value.first.return_value = mock_api_key
            mock_exchange_instance = MagicMock()
            mock_exchange.return_value = mock_exchange_instance
            
            engine = TradingEngine(user_id=1)
            
            result = engine.start_bot(
                user_id=1,
                symbol='BTCUSDT',
                strategy_name='invalid_strategy'
            )
            
            assert result['success'] is False
            assert 'Invalid strategy' in result['message']
    
    def test_bot_stop_nonexistent_bot(self, app_context):
        """Test stopping a non-existent bot."""
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        mock_api_key.api_key = 'test_key'
        mock_api_key.api_secret = 'test_secret'
        mock_api_key.exchange = 'binance'
        mock_api_key.testnet = True
        
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query, \
             patch('bot_engine.trading_engine.ccxt.binance') as mock_exchange, \
             patch('bot_engine.trading_engine.Bot.query') as mock_bot_query:
            
            mock_query.filter_by.return_value.first.return_value = mock_api_key
            mock_exchange_instance = MagicMock()
            mock_exchange.return_value = mock_exchange_instance
            mock_bot_query.get.return_value = None
            
            engine = TradingEngine(user_id=1)
            
            result = engine.stop_bot(user_id=1, bot_id='nonexistent_id')
            
            assert result['success'] is False
            assert 'Bot not found' in result['message']
    
    def test_trade_execution_insufficient_balance(self, app_context):
        """Test trade execution with insufficient balance."""
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        mock_api_key.api_key = 'test_key'
        mock_api_key.api_secret = 'test_secret'
        mock_api_key.exchange = 'binance'
        mock_api_key.testnet = True
        
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query, \
             patch('bot_engine.trading_engine.ccxt.binance') as mock_exchange:
            
            mock_query.filter_by.return_value.first.return_value = mock_api_key
            mock_exchange_instance = MagicMock()
            mock_exchange_instance.fetch_balance.return_value = {
                'USDT': {'free': 10.0, 'used': 0.0, 'total': 10.0}
            }
            mock_exchange.return_value = mock_exchange_instance
            
            engine = TradingEngine(user_id=1)
            
            result = engine.execute_trade(
                user_id=1,
                symbol='BTCUSDT',
                side='buy',
                amount=1000.0,  # More than available balance
                price=45000.0
            )
            
            assert result['success'] is False
            assert 'Insufficient balance' in result['message']
    
    def test_market_data_exchange_error(self, app_context):
        """Test market data retrieval with exchange error."""
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        mock_api_key.api_key = 'test_key'
        mock_api_key.api_secret = 'test_secret'
        mock_api_key.exchange = 'binance'
        mock_api_key.testnet = True
        
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query, \
             patch('bot_engine.trading_engine.ccxt.binance') as mock_exchange:
            
            mock_query.filter_by.return_value.first.return_value = mock_api_key
            mock_exchange_instance = MagicMock()
            mock_exchange_instance.fetch_ticker.side_effect = Exception("Network error")
            mock_exchange.return_value = mock_exchange_instance
            
            engine = TradingEngine(user_id=1)
            
            result = engine.get_market_data('BTCUSDT')
            
            assert result is None or result.get('success') is False
    
    def test_websocket_connection_error(self, app_context):
        """Test WebSocket connection error handling."""
        mock_api_key = MagicMock()
        mock_api_key.is_active = True
        mock_api_key.api_key = 'test_key'
        mock_api_key.api_secret = 'test_secret'
        mock_api_key.exchange = 'binance'
        mock_api_key.testnet = True
        
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query, \
             patch('bot_engine.trading_engine.ccxt.binance') as mock_exchange:
            
            mock_query.filter_by.return_value.first.return_value = mock_api_key
            mock_exchange_instance = MagicMock()
            mock_exchange.return_value = mock_exchange_instance
            
            engine = TradingEngine(user_id=1)
            
            # Mock WebSocket connection failure
            with patch.object(engine, '_start_websocket') as mock_ws:
                mock_ws.side_effect = ConnectionError("WebSocket connection failed")
                
                result = engine.start_websocket_stream(['BTCUSDT'])
                
                assert result['success'] is False
                assert 'connection' in result['message'].lower()


class TestBotLifecycleErrors:
    """Test bot lifecycle error scenarios."""
    
    def test_bot_creation_duplicate_name(self, app_context, test_user):
        """Test bot creation with duplicate name."""
        existing_bot = MagicMock()
        existing_bot.name = 'Test Bot'
        existing_bot.user_id = test_user.id
        
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'scalping',
            'symbol': 'BTCUSDT',
            'base_amount': 100.0
        }
        
        with patch('services.trading_service.Bot.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = existing_bot
            
            from services.trading_service import TradingService
            service = TradingService()
            
            result = service.create_bot(test_user.id, bot_data)
            
            assert result['success'] is False
            assert 'already exists' in result['message']
    
    def test_bot_start_already_active(self, app_context, test_user):
        """Test starting an already active bot."""
        active_bot = MagicMock()
        active_bot.id = 'test_bot_id'
        active_bot.user_id = test_user.id
        active_bot.is_active = True
        active_bot.status = 'running'
        
        with patch('services.trading_service.Bot.query') as mock_query:
            mock_query.get.return_value = active_bot
            
            from services.trading_service import TradingService
            service = TradingService()
            
            result = service.start_bot(test_user.id, 'test_bot_id')
            
            assert result['success'] is False
            assert 'already active' in result['message']
    
    def test_bot_stop_already_inactive(self, app_context, test_user):
        """Test stopping an already inactive bot."""
        inactive_bot = MagicMock()
        inactive_bot.id = 'test_bot_id'
        inactive_bot.user_id = test_user.id
        inactive_bot.is_active = False
        inactive_bot.status = 'stopped'
        
        with patch('services.trading_service.Bot.query') as mock_query:
            mock_query.get.return_value = inactive_bot
            
            from services.trading_service import TradingService
            service = TradingService()
            
            result = service.stop_bot(test_user.id, 'test_bot_id')
            
            assert result['success'] is False
            assert 'not active' in result['message']
    
    def test_bot_update_nonexistent(self, app_context, test_user):
        """Test updating a non-existent bot."""
        update_data = {
            'name': 'Updated Bot',
            'base_amount': 200.0
        }
        
        with patch('services.trading_service.Bot.query') as mock_query:
            mock_query.get.return_value = None
            
            from services.trading_service import TradingService
            service = TradingService()
            
            result = service.update_bot(test_user.id, 'nonexistent_id', update_data)
            
            assert result['success'] is False
            assert 'not found' in result['message']
    
    def test_bot_delete_with_active_trades(self, app_context, test_user):
        """Test deleting a bot with active trades."""
        bot_with_trades = MagicMock()
        bot_with_trades.id = 'test_bot_id'
        bot_with_trades.user_id = test_user.id
        bot_with_trades.is_active = True
        
        active_trade = MagicMock()
        active_trade.status = 'open'
        
        with patch('services.trading_service.Bot.query') as mock_bot_query, \
             patch('services.trading_service.Trade.query') as mock_trade_query:
            
            mock_bot_query.get.return_value = bot_with_trades
            mock_trade_query.filter_by.return_value.filter.return_value.first.return_value = active_trade
            
            from services.trading_service import TradingService
            service = TradingService()
            
            result = service.delete_bot(test_user.id, 'test_bot_id')
            
            assert result['success'] is False
            assert 'active trades' in result['message']


class TestPerformanceCalculationErrors:
    """Test performance calculation error scenarios."""
    
    def test_performance_no_trades(self, app_context, test_user):
        """Test performance calculation with no trades."""
        bot_no_trades = MagicMock()
        bot_no_trades.id = 'test_bot_id'
        bot_no_trades.user_id = test_user.id
        
        with patch('services.trading_service.Bot.query') as mock_bot_query, \
             patch('services.trading_service.Trade.query') as mock_trade_query:
            
            mock_bot_query.get.return_value = bot_no_trades
            mock_trade_query.filter_by.return_value.all.return_value = []
            
            from services.trading_service import TradingService
            service = TradingService()
            
            result = service.get_bot_performance('test_bot_id')
            
            assert result['total_trades'] == 0
            assert result['total_profit'] == 0.0
            assert result['win_rate'] == 0.0
    
    def test_performance_calculation_error(self, app_context):
        """Test performance calculation with invalid data."""
        invalid_trade = MagicMock()
        invalid_trade.profit_loss = None  # Invalid profit_loss
        invalid_trade.status = 'completed'
        
        with patch('services.trading_service.Trade.query') as mock_trade_query:
            mock_trade_query.filter_by.return_value.all.return_value = [invalid_trade]
            
            from services.trading_service import TradingService
            service = TradingService()
            
            # Should handle None values gracefully
            result = service.get_bot_performance('test_bot_id')
            
            assert 'total_trades' in result
            assert 'total_profit' in result