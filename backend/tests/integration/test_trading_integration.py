"""Integration tests for trading system."""
import pytest
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from models.user import User
from models.bot import Bot
from models.trade import Trade
from models.api_key import APIKey
from db import db


class TestTradingIntegration:
    """Integration tests for complete trading workflow."""
    
    def test_complete_bot_lifecycle(self, client, app_context):
        """Test complete bot creation, configuration, and trading lifecycle."""
        # Step 1: Create user and login
        user = User(
            username='traderuser',
            email='trader@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        login_data = {
            'username': 'traderuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Create API key
        api_key = APIKey(
            user_id=user.id,
            exchange='binance',
            key_name='Test API Key',
            api_key='test_api_key',
            api_secret='test_api_secret'
        )
        db.session.add(api_key)
        db.session.commit()
        
        # Step 3: Create bot
        bot_data = {
            'name': 'Integration Test Bot',
            'strategy': 'scalping',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'initial_balance': '1000.00',
            'api_key_id': api_key.id
        }
        
        with patch('app.services.trading_service.TradingService._validate_api_key', return_value=True):
            response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=headers)
        
        assert response.status_code == 201
        bot_response = json.loads(response.data)
        bot_id = bot_response['bot']['id']
        
        # Verify bot was created in database
        bot = Bot.query.get(bot_id)
        assert bot is not None
        assert bot.name == 'Integration Test Bot'
        assert bot.user_id == user.id
        assert bot.is_active is False
        
        # Step 4: Start bot
        with patch('app.services.trading_service.TradingService._validate_bot_configuration', return_value=True), \
             patch('app.services.trading_service.TradingService._initialize_exchange_connection', return_value=True):
            
            response = client.post(f'/api/bots/{bot_id}/start', headers=headers)
        
        assert response.status_code == 200
        start_response = json.loads(response.data)
        assert start_response['success'] is True
        
        # Verify bot is active
        bot = Bot.query.get(bot_id)
        assert bot.is_active is True
        
        # Step 5: Execute trade
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': '0.001',
            'price': '50000.00',
            'trade_type': 'limit'
        }
        
        mock_exchange_response = {
            'id': 'exchange_order_123',
            'status': 'filled',
            'filled': 0.001,
            'average': 50000.00,
            'cost': 50.00
        }
        
        with patch('app.services.trading_service.TradingService._get_exchange_client') as mock_exchange:
            mock_exchange.return_value.create_order.return_value = mock_exchange_response
            
            response = client.post(f'/api/bots/{bot_id}/trade',
                                 data=json.dumps(trade_data),
                                 content_type='application/json',
                                 headers=headers)
        
        assert response.status_code == 201
        trade_response = json.loads(response.data)
        assert trade_response['success'] is True
        
        # Verify trade was recorded
        trade = Trade.query.filter_by(bot_id=bot_id).first()
        assert trade is not None
        assert trade.symbol == 'BTCUSDT'
        assert trade.side == 'buy'
        assert trade.status == 'filled'
        
        # Step 6: Check bot performance
        response = client.get(f'/api/analytics/bots/{bot_id}/performance', headers=headers)
        assert response.status_code == 200
        performance_data = json.loads(response.data)
        assert 'performance' in performance_data
        
        # Step 7: Stop bot
        with patch('app.services.trading_service.TradingService._close_open_positions'):
            response = client.post(f'/api/bots/{bot_id}/stop', headers=headers)
        
        assert response.status_code == 200
        stop_response = json.loads(response.data)
        assert stop_response['success'] is True
        
        # Verify bot is inactive
        bot = Bot.query.get(bot_id)
        assert bot.is_active is False
    
    def test_multi_bot_portfolio_management(self, client, app_context):
        """Test managing multiple bots in a portfolio."""
        # Create user and login
        user = User(
            username='portfoliouser',
            email='portfolio@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        login_data = {
            'username': 'portfoliouser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Create API key
        api_key = APIKey(
            user_id=user.id,
            exchange='binance',
            key_name='Portfolio API Key',
            api_key='test_api_key',
            api_secret='test_api_secret'
        )
        db.session.add(api_key)
        db.session.commit()
        
        # Create multiple bots
        bot_configs = [
            {
                'name': 'Scalping Bot',
                'strategy': 'scalping',
                'symbol': 'BTCUSDT',
                'initial_balance': '1000.00'
            },
            {
                'name': 'Grid Trading Bot',
                'strategy': 'grid_trading',
                'symbol': 'ETHUSDT',
                'initial_balance': '1500.00'
            },
            {
                'name': 'DCA Bot',
                'strategy': 'dca',
                'symbol': 'ADAUSDT',
                'initial_balance': '500.00'
            }
        ]
        
        bot_ids = []
        
        with patch('app.services.trading_service.TradingService._validate_api_key', return_value=True):
            for config in bot_configs:
                config.update({
                    'exchange': 'binance',
                    'api_key_id': api_key.id
                })
                
                response = client.post('/api/bots',
                                     data=json.dumps(config),
                                     content_type='application/json',
                                     headers=headers)
                
                assert response.status_code == 201
                bot_data = json.loads(response.data)
                bot_ids.append(bot_data['bot']['id'])
        
        # Verify all bots were created
        assert len(bot_ids) == 3
        
        # Get bots list
        response = client.get('/api/bots', headers=headers)
        assert response.status_code == 200
        bots_data = json.loads(response.data)
        assert len(bots_data['bots']) == 3
        
        # Start all bots
        with patch('app.services.trading_service.TradingService._validate_bot_configuration', return_value=True), \
             patch('app.services.trading_service.TradingService._initialize_exchange_connection', return_value=True):
            
            for bot_id in bot_ids:
                response = client.post(f'/api/bots/{bot_id}/start', headers=headers)
                assert response.status_code == 200
        
        # Execute trades on different bots
        trades = [
            {'bot_id': bot_ids[0], 'symbol': 'BTCUSDT', 'quantity': '0.001', 'price': '50000.00'},
            {'bot_id': bot_ids[1], 'symbol': 'ETHUSDT', 'quantity': '0.1', 'price': '3000.00'},
            {'bot_id': bot_ids[2], 'symbol': 'ADAUSDT', 'quantity': '100', 'price': '0.50'}
        ]
        
        mock_exchange_response = {
            'id': 'exchange_order_123',
            'status': 'filled',
            'filled': 1.0,
            'average': 1.0,
            'cost': 1.0
        }
        
        with patch('app.services.trading_service.TradingService._get_exchange_client') as mock_exchange:
            mock_exchange.return_value.create_order.return_value = mock_exchange_response
            
            for trade in trades:
                trade_data = {
                    'symbol': trade['symbol'],
                    'side': 'buy',
                    'quantity': trade['quantity'],
                    'price': trade['price'],
                    'trade_type': 'limit'
                }
                
                response = client.post(f'/api/bots/{trade["bot_id"]}/trade',
                                     data=json.dumps(trade_data),
                                     content_type='application/json',
                                     headers=headers)
                
                assert response.status_code == 201
        
        # Get portfolio summary
        response = client.get('/api/analytics/portfolio', headers=headers)
        assert response.status_code == 200
        portfolio_data = json.loads(response.data)
        assert 'portfolio' in portfolio_data
        assert portfolio_data['portfolio']['active_bots'] == 3
        
        # Stop all bots
        with patch('app.services.trading_service.TradingService._close_open_positions'):
            for bot_id in bot_ids:
                response = client.post(f'/api/bots/{bot_id}/stop', headers=headers)
                assert response.status_code == 200
    
    def test_trading_with_insufficient_balance(self, client, app_context):
        """Test trading scenarios with insufficient balance."""
        # Create user, login, and setup bot
        user = User(
            username='balanceuser',
            email='balance@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        login_data = {
            'username': 'balanceuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Create bot with low balance
        bot = Bot(
            name='Low Balance Bot',
            user_id=user.id,
            strategy='scalping',
            exchange='binance',
            symbol='BTCUSDT',
            initial_balance=Decimal('10.00'),  # Very low balance
            current_balance=Decimal('10.00')
        )
        db.session.add(bot)
        db.session.commit()
        
        # Try to execute large trade
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': '1.0',  # Large quantity
            'price': '50000.00',
            'trade_type': 'limit'
        }
        
        response = client.post(f'/api/bots/{bot.id}/trade',
                             data=json.dumps(trade_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 400
        error_data = json.loads(response.data)
        assert 'insufficient' in error_data['message'].lower()
    
    def test_trading_error_handling(self, client, app_context):
        """Test trading system error handling."""
        # Create user, login, and setup bot
        user = User(
            username='erroruser',
            email='error@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        login_data = {
            'username': 'erroruser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        bot = Bot(
            name='Error Test Bot',
            user_id=user.id,
            strategy='scalping',
            exchange='binance',
            symbol='BTCUSDT',
            initial_balance=Decimal('1000.00'),
            current_balance=Decimal('1000.00'),
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()
        
        # Test exchange connection error
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': '0.001',
            'price': '50000.00',
            'trade_type': 'limit'
        }
        
        with patch('app.services.trading_service.TradingService._get_exchange_client') as mock_exchange:
            mock_exchange.return_value.create_order.side_effect = Exception('Exchange connection error')
            
            response = client.post(f'/api/bots/{bot.id}/trade',
                                 data=json.dumps(trade_data),
                                 content_type='application/json',
                                 headers=headers)
        
        assert response.status_code == 500
        error_data = json.loads(response.data)
        assert 'error' in error_data['message'].lower()
        
        # Verify trade was not recorded
        trade_count = Trade.query.filter_by(bot_id=bot.id).count()
        assert trade_count == 0
    
    def test_real_time_market_data_integration(self, client, app_context):
        """Test real-time market data integration."""
        # Create user and login
        user = User(
            username='marketuser',
            email='market@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        login_data = {
            'username': 'marketuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Mock market data
        mock_ticker = {
            'symbol': 'BTCUSDT',
            'last': 50000.00,
            'bid': 49999.00,
            'ask': 50001.00,
            'high': 51000.00,
            'low': 49000.00,
            'volume': 1000.0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        with patch('app.services.trading_service.TradingService._get_exchange_client') as mock_exchange:
            mock_exchange.return_value.fetch_ticker.return_value = mock_ticker
            
            # Get market data
            response = client.get('/api/market/BTCUSDT?exchange=binance', headers=headers)
        
        assert response.status_code == 200
        market_data = json.loads(response.data)
        assert market_data['success'] is True
        assert market_data['data']['symbol'] == 'BTCUSDT'
        assert market_data['data']['last'] == 50000.00
    
    def test_bot_performance_analytics_integration(self, client, app_context):
        """Test bot performance analytics integration."""
        # Create user and login
        user = User(
            username='analyticsuser',
            email='analytics@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        login_data = {
            'username': 'analyticsuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Create bot
        bot = Bot(
            name='Analytics Bot',
            user_id=user.id,
            strategy='scalping',
            exchange='binance',
            symbol='BTCUSDT',
            initial_balance=Decimal('1000.00'),
            current_balance=Decimal('1200.00')  # Profitable bot
        )
        db.session.add(bot)
        db.session.commit()
        
        # Create some trades
        trades = [
            Trade(
                bot_id=bot.id,
                symbol='BTCUSDT',
                side='buy',
                quantity=Decimal('0.001'),
                price=Decimal('50000.00'),
                status='filled',
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            Trade(
                bot_id=bot.id,
                symbol='BTCUSDT',
                side='sell',
                quantity=Decimal('0.001'),
                price=Decimal('52000.00'),
                status='filled',
                created_at=datetime.utcnow()
            )
        ]
        
        for trade in trades:
            db.session.add(trade)
        db.session.commit()
        
        # Get performance analytics
        response = client.get(f'/api/analytics/bots/{bot.id}/performance', headers=headers)
        assert response.status_code == 200
        performance_data = json.loads(response.data)
        
        assert 'performance' in performance_data
        assert performance_data['performance']['total_trades'] >= 2
        assert 'profit_loss' in performance_data['performance']
        assert 'win_rate' in performance_data['performance']
        
        # Get trade history
        response = client.get(f'/api/bots/{bot.id}/trades', headers=headers)
        assert response.status_code == 200
        trades_data = json.loads(response.data)
        assert len(trades_data['trades']) >= 2