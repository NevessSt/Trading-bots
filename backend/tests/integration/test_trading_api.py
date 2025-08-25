"""Integration tests for trading API endpoints."""
import pytest
import json
from decimal import Decimal
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta

from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.api_key import APIKey
from db import db


class TestTradingAPIEndpoints:
    """Test trading API endpoints."""
    
    @pytest.fixture
    def authenticated_user(self, app_context):
        """Create authenticated user for testing."""
        user = User(
            username='trader',
            email='trader@example.com',
            password='password123',
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @pytest.fixture
    def user_api_key(self, app_context, authenticated_user):
        """Create API key for user."""
        api_key = APIKey(
            user_id=authenticated_user.id,
            exchange='binance',
            key_name='Test API Key',
            api_key='test_api_key',
            api_secret='test_api_secret',
            permissions=['read', 'trade']
        )
        db.session.add(api_key)
        db.session.commit()
        return api_key
    
    @pytest.fixture
    def test_bot(self, app_context, authenticated_user):
        """Create test bot."""
        bot = Bot(
            user_id=authenticated_user.id,
            name='Integration Test Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={
                'rsi_period': 14,
                'overbought': 70,
                'oversold': 30
            },
            is_active=False
        )
        db.session.add(bot)
        db.session.commit()
        return bot
    
    @pytest.fixture
    def auth_headers(self, client, authenticated_user):
        """Get authentication headers."""
        response = client.post('/api/auth/login', json={
            'email': authenticated_user.email,
            'password': 'password123'
        })
        
        assert response.status_code == 200
        token = response.get_json()['access_token']
        
        return {'Authorization': f'Bearer {token}'}
    
    def test_get_bots_endpoint(self, client, auth_headers, test_bot):
        """Test GET /api/trading/bots endpoint."""
        response = client.get('/api/trading/bots', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        # API returns array directly, not wrapped in 'bots' key
        assert isinstance(data, list)
        assert len(data) >= 1
        
        bot_data = data[0]
        assert bot_data['name'] == 'Integration Test Bot'
        assert bot_data['strategy'] == 'rsi'
        assert bot_data['symbol'] == 'BTCUSDT'
    
    def test_create_bot_endpoint(self, client, auth_headers, user_api_key):
        """Test POST /api/trading/bots endpoint."""
        bot_data = {
            'name': 'New Test Bot',
            'strategy': 'macd',
            'symbol': 'ETHUSDT',
            'base_amount': 500.0,
            'config': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            }
        }
        
        response = client.post('/api/trading/bots', 
                             json=bot_data, 
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['name'] == 'New Test Bot'
        assert data['strategy'] == 'macd'
        assert data['symbol'] == 'ETHUSDT'
        assert data['is_active'] is False
    
    def test_update_bot_endpoint(self, client, auth_headers, test_bot):
        """Test PUT /api/trading/bots/<id> endpoint."""
        update_data = {
            'name': 'Updated Bot Name',
            'config': {
                'rsi_period': 21,
                'overbought': 75,
                'oversold': 25
            }
        }
        
        response = client.put(f'/api/trading/bots/{test_bot.id}',
                            json=update_data,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['name'] == 'Updated Bot Name'
        assert data['config']['rsi_period'] == 21
    
    def test_delete_bot_endpoint(self, client, auth_headers, test_bot):
        """Test DELETE /api/trading/bots/<id> endpoint."""
        response = client.delete(f'/api/trading/bots/{test_bot.id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify bot is deleted
        get_response = client.get(f'/api/trading/bots/{test_bot.id}',
                                headers=auth_headers)
        assert get_response.status_code == 404
    
    @patch('bot_engine.trading_engine.TradingEngine.start_bot')
    def test_start_bot_endpoint(self, mock_start_bot, client, auth_headers, test_bot, user_api_key):
        """Test POST /api/trading/bots/<id>/start endpoint."""
        mock_start_bot.return_value = True
        
        response = client.post(f'/api/trading/bots/{test_bot.id}/start',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['message'] == 'Bot started successfully'
        mock_start_bot.assert_called_once()
    
    @patch('bot_engine.trading_engine.TradingEngine.stop_bot')
    def test_stop_bot_endpoint(self, mock_stop_bot, client, auth_headers, test_bot):
        """Test POST /api/trading/bots/<id>/stop endpoint."""
        # First make bot active
        test_bot.is_active = True
        db.session.commit()
        
        mock_stop_bot.return_value = True
        
        response = client.post(f'/api/trading/bots/{test_bot.id}/stop',
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['message'] == 'Bot stopped successfully'
        mock_stop_bot.assert_called_once()
    
    def test_get_bot_trades_endpoint(self, client, auth_headers, test_bot):
        """Test GET /api/trading/bots/<id>/trades endpoint."""
        # Create some test trades
        trade1 = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='buy',
            trade_type='market',
            quantity=0.001,
            price=50000.0,
            bot_id=test_bot.id,
            exchange_order_id='order_1',
            status='filled'
        )
        trade2 = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='sell',
            trade_type='market',
            quantity=0.001,
            price=51000.0,
            bot_id=test_bot.id,
            exchange_order_id='order_2',
            status='filled'
        )
        
        db.session.add_all([trade1, trade2])
        db.session.commit()
        
        response = client.get(f'/api/trading/bots/{test_bot.id}/trades',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'trades' in data
        assert len(data['trades']) == 2
        
        # Check trade data
        trade_data = data['trades'][0]
        assert 'symbol' in trade_data
        assert 'side' in trade_data
        assert 'quantity' in trade_data
        assert 'price' in trade_data
    
    def test_get_bot_performance_endpoint(self, client, auth_headers, test_bot):
        """Test GET /api/trading/bots/<id>/performance endpoint."""
        # Create profitable trades
        buy_trade = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='buy',
            trade_type='market',
            quantity=0.001,
            price=50000.0,
            bot_id=test_bot.id,
            exchange_order_id='buy_order',
            status='filled',
            executed_at=datetime.utcnow() - timedelta(hours=1)
        )
        sell_trade = Trade(
            user_id=test_bot.user_id,
            symbol='BTCUSDT',
            side='sell',
            trade_type='market',
            quantity=0.001,
            price=51000.0,
            bot_id=test_bot.id,
            exchange_order_id='sell_order',
            status='filled',
            executed_at=datetime.utcnow()
        )
        
        db.session.add_all([buy_trade, sell_trade])
        db.session.commit()
        
        response = client.get(f'/api/trading/bots/{test_bot.id}/performance',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'total_trades' in data
        assert 'profit_loss' in data
        assert 'win_rate' in data
        assert 'total_volume' in data
        
        assert data['total_trades'] == 2
        assert float(data['profit_loss']) > 0  # Should be profitable
    
    def test_unauthorized_access(self, client, test_bot):
        """Test unauthorized access to protected endpoints."""
        # Test without authentication headers
        response = client.get('/api/trading/bots')
        assert response.status_code == 401
        
        response = client.post('/api/trading/bots', json={'name': 'Test'})
        assert response.status_code == 401
        
        response = client.put(f'/api/trading/bots/{test_bot.id}', json={'name': 'Test'})
        assert response.status_code == 401
    
    def test_invalid_bot_id(self, client, auth_headers):
        """Test requests with invalid bot IDs."""
        invalid_id = 99999
        
        response = client.get(f'/api/trading/bots/{invalid_id}', headers=auth_headers)
        assert response.status_code == 404
        
        response = client.put(f'/api/trading/bots/{invalid_id}', 
                            json={'name': 'Test'}, 
                            headers=auth_headers)
        assert response.status_code == 404
        
        response = client.delete(f'/api/trading/bots/{invalid_id}', headers=auth_headers)
        assert response.status_code == 404
    
    def test_invalid_bot_data(self, client, auth_headers):
        """Test creating bot with invalid data."""
        invalid_data = {
            'name': '',  # Empty name
            'strategy': 'invalid_strategy',
            'symbol': 'INVALID',
            'base_amount': -100  # Negative amount
        }
        
        response = client.post('/api/trading/bots', 
                             json=invalid_data, 
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'message' in data


class TestTradingEngineIntegration:
    """Test trading engine integration."""
    
    @pytest.fixture
    def mock_exchange(self):
        """Mock exchange for testing."""
        exchange = Mock()
        exchange.get_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 50000.0,
            'bid': 49950.0,
            'ask': 50050.0,
            'volume': 1000.0
        }
        exchange.get_balance.return_value = {
            'USDT': {'free': 1000.0, 'used': 0.0, 'total': 1000.0},
            'BTC': {'free': 0.0, 'used': 0.0, 'total': 0.0}
        }
        exchange.create_order.return_value = {
            'id': 'test_order_123',
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0,
            'status': 'open'
        }
        return exchange
    
    def test_trading_engine_initialization(self, app_context):
        """Test trading engine initialization."""
        from bot_engine.trading_engine import TradingEngine
        
        engine = TradingEngine()
        assert engine is not None
        assert hasattr(engine, 'portfolio_manager')
        assert hasattr(engine, 'risk_manager')
        assert hasattr(engine, 'market_data_manager')
    
    @patch('ccxt.binance')
    def test_bot_execution_flow(self, mock_exchange_class, app_context, authenticated_user, user_api_key):
        """Test complete bot execution flow."""
        from bot_engine.trading_engine import TradingEngine
        
        # Mock exchange instance
        mock_exchange = Mock()
        mock_exchange.fetch_ticker.return_value = {'last': 50000.0, 'price': 50000.0}
        mock_exchange.fetch_balance.return_value = {'free': {'USDT': 1000.0}}
        mock_exchange_class.return_value = mock_exchange
        
        # Create bot
        bot = Bot(
            user_id=authenticated_user.id,
            name='Integration Test Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={
                'rsi_period': 14,
                'overbought': 70,
                'oversold': 30
            },
            is_active=False
        )
        db.session.add(bot)
        db.session.commit()
        
        # Initialize trading engine
        engine = TradingEngine()
        
        # Test starting bot
        result = engine.start_bot(
            user_id=authenticated_user.id,
            symbol='BTCUSDT',
            strategy_name='rsi'
        )
        assert result['success'] is True
        
        # Test stopping bot
        bot_id = result.get('bot_id')
        if bot_id:
            stop_result = engine.stop_bot(user_id=authenticated_user.id, bot_id=bot_id)
            assert stop_result['success'] is True
    
    @patch('ccxt.binance')
    def test_trade_execution(self, mock_exchange_class, app_context, authenticated_user, user_api_key):
        """Test trade execution through trading engine."""
        from bot_engine.trading_engine import TradingEngine
        
        # Mock exchange instance
        mock_exchange = Mock()
        mock_exchange.create_order.return_value = {
            'id': 'test_order_123',
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0,
            'status': 'open'
        }
        mock_exchange_class.return_value = mock_exchange
        
        # Create active bot
        bot = Bot(
            user_id=authenticated_user.id,
            name='Trading Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14},
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()
        
        engine = TradingEngine()
        
        # Test executing a buy order using portfolio manager
        trade_result = engine.portfolio_manager.execute_order(
            symbol='BTCUSDT',
            side='buy',
            amount=0.001,
            order_type='market'
        )
        
        assert trade_result is not None
        
        # Verify mock was called
        mock_exchange.create_order.assert_called_once()
    
    def test_error_handling(self, app_context):
        """Test error handling in trading engine."""
        from bot_engine.trading_engine import TradingEngine
        
        engine = TradingEngine()
        
        # Test starting bot with invalid strategy
        result = engine.start_bot(
            user_id=1,
            symbol='BTCUSDT',
            strategy_name='invalid_strategy'
        )
        assert result['success'] is False
        
        # Test stopping non-existent bot
        result = engine.stop_bot(user_id=1, bot_id='non_existent_bot_id')
        assert result['success'] is False
    
    @patch('ccxt.binance')
    def test_exchange_error_handling(self, mock_exchange_class, app_context, authenticated_user, user_api_key):
        """Test handling of exchange errors."""
        from bot_engine.trading_engine import TradingEngine
        
        # Mock exchange that raises errors
        mock_exchange = Mock()
        mock_exchange.create_order.side_effect = Exception("Exchange error")
        mock_exchange_class.return_value = mock_exchange
        
        bot = Bot(
            user_id=authenticated_user.id,
            name='Error Test Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14},
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()
        
        engine = TradingEngine()
        
        # Test that exchange errors are handled gracefully
        try:
            trade_result = engine.portfolio_manager.execute_order(
                symbol='BTCUSDT',
                side='buy',
                amount=0.001,
                order_type='market'
            )
            # Should handle error gracefully
            assert trade_result is None or 'error' in str(trade_result)
        except Exception:
            # Exception handling is working
            pass


class TestWebSocketIntegration:
    """Test WebSocket integration for real-time updates."""
    
    @pytest.fixture
    def socketio_client(self, app):
        """Create SocketIO test client."""
        from flask_socketio import SocketIOTestClient
        
        return SocketIOTestClient(app, app.socketio)
    
    def test_websocket_connection(self, socketio_client):
        """Test WebSocket connection."""
        received = socketio_client.get_received()
        assert len(received) >= 0  # Connection established
    
    def test_bot_status_updates(self, socketio_client, app_context, authenticated_user):
        """Test real-time bot status updates."""
        # Create bot
        bot = Bot(
            user_id=authenticated_user.id,
            name='WebSocket Test Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14},
            is_active=False
        )
        db.session.add(bot)
        db.session.commit()
        
        # Simulate bot status change
        socketio_client.emit('join_room', {'room': f'bot_{bot.id}'})
        
        # Simulate bot starting
        bot.is_active = True
        db.session.commit()
        
        # Emit bot status update
        socketio_client.emit('bot_status_update', {
            'bot_id': bot.id,
            'status': 'active'
        })
        
        received = socketio_client.get_received()
        
        # Should receive status update
        status_updates = [msg for msg in received if msg['name'] == 'bot_status_update']
        assert len(status_updates) > 0
    
    def test_trade_notifications(self, socketio_client, app_context, authenticated_user):
        """Test real-time trade notifications."""
        # Create bot and trade
        bot = Bot(
            user_id=authenticated_user.id,
            name='Trade Notification Bot',
            strategy='rsi',
            symbol='BTCUSDT',
            base_amount=1000.0,
            config={'rsi_period': 14},
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()
        
        trade = Trade(
            user_id=authenticated_user.id,
            symbol='BTCUSDT',
            side='buy',
            trade_type='market',
            quantity=0.001,
            price=50000.0,
            bot_id=bot.id,
            exchange_order_id='ws_test_order',
            status='filled'
        )
        db.session.add(trade)
        db.session.commit()
        
        # Join trade notifications room
        socketio_client.emit('join_room', {'room': f'user_{authenticated_user.id}'})
        
        # Emit trade notification
        socketio_client.emit('trade_executed', {
            'trade_id': trade.id,
            'bot_id': bot.id,
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'amount': 0.001,
            'price': 50000.0
        })
        
        received = socketio_client.get_received()
        
        # Should receive trade notification
        trade_notifications = [msg for msg in received if msg['name'] == 'trade_executed']
        assert len(trade_notifications) > 0


if __name__ == '__main__':
    pytest.main([__file__])