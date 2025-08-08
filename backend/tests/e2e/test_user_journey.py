"""End-to-end tests for complete user journey."""
import pytest
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.models.user import User
from app.models.bot import Bot
from app.models.trade import Trade
from app.models.api_key import APIKey
from app.models.subscription import Subscription
from app.extensions import db


class TestCompleteUserJourney:
    """End-to-end tests for complete user journey."""
    
    def test_new_user_complete_journey(self, client, app_context):
        """Test complete journey from registration to successful trading."""
        # Step 1: User Registration
        registration_data = {
            'username': 'newtrader',
            'email': 'newtrader@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(registration_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        registration_response = json.loads(response.data)
        assert registration_response['success'] is True
        assert 'user' in registration_response
        
        # Verify user was created in database
        user = User.query.filter_by(username='newtrader').first()
        assert user is not None
        assert user.email == 'newtrader@example.com'
        
        # Step 2: User Login
        login_data = {
            'username': 'newtrader',
            'password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        login_response = json.loads(response.data)
        assert 'access_token' in login_response
        assert 'refresh_token' in login_response
        
        access_token = login_response['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 3: Get User Profile
        response = client.get('/api/auth/profile', headers=headers)
        assert response.status_code == 200
        profile_data = json.loads(response.data)
        assert profile_data['user']['username'] == 'newtrader'
        
        # Step 4: Add API Key
        api_key_data = {
            'exchange': 'binance',
            'key_name': 'My Trading Key',
            'api_key': 'test_api_key_123',
            'api_secret': 'test_api_secret_456'
        }
        
        with patch('app.services.trading_service.TradingService._validate_api_key', return_value=True):
            response = client.post('/api/api-keys',
                                 data=json.dumps(api_key_data),
                                 content_type='application/json',
                                 headers=headers)
        
        assert response.status_code == 201
        api_key_response = json.loads(response.data)
        assert api_key_response['success'] is True
        api_key_id = api_key_response['api_key']['id']
        
        # Step 5: Create First Bot
        bot_data = {
            'name': 'My First Bot',
            'strategy': 'scalping',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'initial_balance': '1000.00',
            'api_key_id': api_key_id,
            'parameters': {
                'take_profit': 2.0,
                'stop_loss': 1.0,
                'trade_amount': 10.0
            }
        }
        
        with patch('app.services.trading_service.TradingService._validate_api_key', return_value=True):
            response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=headers)
        
        assert response.status_code == 201
        bot_response = json.loads(response.data)
        assert bot_response['success'] is True
        bot_id = bot_response['bot']['id']
        
        # Verify bot was created
        bot = Bot.query.get(bot_id)
        assert bot is not None
        assert bot.name == 'My First Bot'
        assert bot.user_id == user.id
        
        # Step 6: View Bot List
        response = client.get('/api/bots', headers=headers)
        assert response.status_code == 200
        bots_data = json.loads(response.data)
        assert len(bots_data['bots']) == 1
        assert bots_data['bots'][0]['name'] == 'My First Bot'
        
        # Step 7: Get Bot Details
        response = client.get(f'/api/bots/{bot_id}', headers=headers)
        assert response.status_code == 200
        bot_details = json.loads(response.data)
        assert bot_details['bot']['name'] == 'My First Bot'
        assert bot_details['bot']['strategy'] == 'scalping'
        
        # Step 8: Start Bot
        with patch('app.services.trading_service.TradingService._validate_bot_configuration', return_value=True), \
             patch('app.services.trading_service.TradingService._initialize_exchange_connection', return_value=True):
            
            response = client.post(f'/api/bots/{bot_id}/start', headers=headers)
        
        assert response.status_code == 200
        start_response = json.loads(response.data)
        assert start_response['success'] is True
        
        # Verify bot is active
        bot = Bot.query.get(bot_id)
        assert bot.is_active is True
        
        # Step 9: Execute Manual Trade
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
            'cost': 50.00,
            'fee': {'cost': 0.05, 'currency': 'USDT'}
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
        
        # Step 10: View Trade History
        response = client.get(f'/api/bots/{bot_id}/trades', headers=headers)
        assert response.status_code == 200
        trades_data = json.loads(response.data)
        assert len(trades_data['trades']) >= 1
        assert trades_data['trades'][0]['symbol'] == 'BTCUSDT'
        
        # Step 11: Check Bot Performance
        response = client.get(f'/api/analytics/bots/{bot_id}/performance', headers=headers)
        assert response.status_code == 200
        performance_data = json.loads(response.data)
        assert 'performance' in performance_data
        assert performance_data['performance']['total_trades'] >= 1
        
        # Step 12: Get Portfolio Summary
        response = client.get('/api/analytics/portfolio', headers=headers)
        assert response.status_code == 200
        portfolio_data = json.loads(response.data)
        assert 'portfolio' in portfolio_data
        assert portfolio_data['portfolio']['active_bots'] == 1
        
        # Step 13: Get Market Data
        mock_ticker = {
            'symbol': 'BTCUSDT',
            'last': 50000.00,
            'bid': 49999.00,
            'ask': 50001.00,
            'high': 51000.00,
            'low': 49000.00,
            'volume': 1000.0
        }
        
        with patch('app.services.trading_service.TradingService._get_exchange_client') as mock_exchange:
            mock_exchange.return_value.fetch_ticker.return_value = mock_ticker
            
            response = client.get('/api/market/BTCUSDT?exchange=binance', headers=headers)
        
        assert response.status_code == 200
        market_data = json.loads(response.data)
        assert market_data['success'] is True
        
        # Step 14: Update Bot Configuration
        update_data = {
            'parameters': {
                'take_profit': 3.0,  # Updated take profit
                'stop_loss': 1.5,    # Updated stop loss
                'trade_amount': 15.0  # Updated trade amount
            }
        }
        
        response = client.put(f'/api/bots/{bot_id}',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=headers)
        
        assert response.status_code == 200
        update_response = json.loads(response.data)
        assert update_response['success'] is True
        
        # Step 15: Stop Bot
        with patch('app.services.trading_service.TradingService._close_open_positions'):
            response = client.post(f'/api/bots/{bot_id}/stop', headers=headers)
        
        assert response.status_code == 200
        stop_response = json.loads(response.data)
        assert stop_response['success'] is True
        
        # Verify bot is inactive
        bot = Bot.query.get(bot_id)
        assert bot.is_active is False
        
        # Step 16: Update Profile
        profile_update = {
            'email': 'updated.trader@example.com',
            'preferences': {
                'notifications': True,
                'theme': 'dark'
            }
        }
        
        response = client.put('/api/auth/profile',
                            data=json.dumps(profile_update),
                            content_type='application/json',
                            headers=headers)
        
        assert response.status_code == 200
        profile_response = json.loads(response.data)
        assert profile_response['success'] is True
        
        # Step 17: Logout
        response = client.post('/api/auth/logout', headers=headers)
        assert response.status_code == 200
        logout_response = json.loads(response.data)
        assert logout_response['success'] is True
    
    def test_premium_user_journey(self, client, app_context):
        """Test premium user journey with subscription features."""
        # Step 1: Register and login
        registration_data = {
            'username': 'premiumuser',
            'email': 'premium@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(registration_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        
        login_data = {
            'username': 'premiumuser',
            'password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        user = User.query.filter_by(username='premiumuser').first()
        
        # Step 2: Upgrade to Premium
        subscription = Subscription(
            user_id=user.id,
            plan='premium',
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
        db.session.commit()
        
        # Step 3: Create Multiple Bots (Premium Feature)
        api_key = APIKey(
            user_id=user.id,
            exchange='binance',
            key_name='Premium API Key',
            api_key='premium_api_key',
            api_secret='premium_api_secret'
        )
        db.session.add(api_key)
        db.session.commit()
        
        # Create 5 bots (more than free tier limit)
        bot_configs = [
            {'name': f'Premium Bot {i}', 'strategy': 'scalping', 'symbol': f'BTC{i}USDT'}
            for i in range(1, 6)
        ]
        
        bot_ids = []
        
        with patch('app.services.trading_service.TradingService._validate_api_key', return_value=True):
            for config in bot_configs:
                bot_data = {
                    'name': config['name'],
                    'strategy': config['strategy'],
                    'exchange': 'binance',
                    'symbol': config['symbol'],
                    'initial_balance': '2000.00',
                    'api_key_id': api_key.id
                }
                
                response = client.post('/api/bots',
                                     data=json.dumps(bot_data),
                                     content_type='application/json',
                                     headers=headers)
                
                assert response.status_code == 201
                bot_response = json.loads(response.data)
                bot_ids.append(bot_response['bot']['id'])
        
        # Verify all 5 bots were created
        assert len(bot_ids) == 5
        
        # Step 4: Use Advanced Analytics (Premium Feature)
        response = client.get('/api/analytics/advanced', headers=headers)
        assert response.status_code == 200
        analytics_data = json.loads(response.data)
        assert 'advanced_metrics' in analytics_data
        
        # Step 5: Access Premium Market Data
        response = client.get('/api/market/premium-data', headers=headers)
        assert response.status_code == 200
        premium_data = json.loads(response.data)
        assert 'premium_indicators' in premium_data
    
    def test_error_scenarios_journey(self, client, app_context):
        """Test user journey with various error scenarios."""
        # Step 1: Invalid Registration
        invalid_registration = {
            'username': 'u',  # Too short
            'email': 'invalid-email',  # Invalid format
            'password': '123',  # Too weak
            'confirm_password': '456'  # Doesn't match
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(invalid_registration),
                             content_type='application/json')
        
        assert response.status_code == 400
        error_response = json.loads(response.data)
        assert 'error' in error_response
        
        # Step 2: Valid Registration
        valid_registration = {
            'username': 'erroruser',
            'email': 'error@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(valid_registration),
                             content_type='application/json')
        
        assert response.status_code == 201
        
        # Step 3: Invalid Login
        invalid_login = {
            'username': 'erroruser',
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(invalid_login),
                             content_type='application/json')
        
        assert response.status_code == 401
        
        # Step 4: Valid Login
        valid_login = {
            'username': 'erroruser',
            'password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(valid_login),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 5: Invalid API Key
        invalid_api_key = {
            'exchange': 'binance',
            'key_name': 'Invalid Key',
            'api_key': 'invalid_key',
            'api_secret': 'invalid_secret'
        }
        
        with patch('app.services.trading_service.TradingService._validate_api_key', return_value=False):
            response = client.post('/api/api-keys',
                                 data=json.dumps(invalid_api_key),
                                 content_type='application/json',
                                 headers=headers)
        
        assert response.status_code == 400
        
        # Step 6: Access Non-existent Bot
        response = client.get('/api/bots/99999', headers=headers)
        assert response.status_code == 404
        
        # Step 7: Unauthorized Access (Invalid Token)
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        response = client.get('/api/bots', headers=invalid_headers)
        assert response.status_code == 401
    
    def test_concurrent_user_operations(self, client, app_context):
        """Test concurrent operations by multiple users."""
        # Create two users
        users_data = [
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!'
            },
            {
                'username': 'user2',
                'email': 'user2@example.com',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!'
            }
        ]
        
        tokens = []
        
        # Register and login both users
        for user_data in users_data:
            # Register
            response = client.post('/api/auth/register',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            assert response.status_code == 201
            
            # Login
            login_data = {
                'username': user_data['username'],
                'password': user_data['password']
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            access_token = json.loads(response.data)['access_token']
            tokens.append(access_token)
        
        # Both users create bots simultaneously
        for i, token in enumerate(tokens):
            headers = {'Authorization': f'Bearer {token}'}
            
            # Create API key
            api_key_data = {
                'exchange': 'binance',
                'key_name': f'User {i+1} Key',
                'api_key': f'user{i+1}_api_key',
                'api_secret': f'user{i+1}_api_secret'
            }
            
            with patch('app.services.trading_service.TradingService._validate_api_key', return_value=True):
                response = client.post('/api/api-keys',
                                     data=json.dumps(api_key_data),
                                     content_type='application/json',
                                     headers=headers)
            
            api_key_id = json.loads(response.data)['api_key']['id']
            
            # Create bot
            bot_data = {
                'name': f'User {i+1} Bot',
                'strategy': 'scalping',
                'exchange': 'binance',
                'symbol': 'BTCUSDT',
                'initial_balance': '1000.00',
                'api_key_id': api_key_id
            }
            
            with patch('app.services.trading_service.TradingService._validate_api_key', return_value=True):
                response = client.post('/api/bots',
                                     data=json.dumps(bot_data),
                                     content_type='application/json',
                                     headers=headers)
            
            assert response.status_code == 201
        
        # Verify each user can only see their own bots
        for i, token in enumerate(tokens):
            headers = {'Authorization': f'Bearer {token}'}
            
            response = client.get('/api/bots', headers=headers)
            assert response.status_code == 200
            
            bots_data = json.loads(response.data)
            assert len(bots_data['bots']) == 1
            assert bots_data['bots'][0]['name'] == f'User {i+1} Bot'
        
        # Verify users cannot access each other's bots
        user1_headers = {'Authorization': f'Bearer {tokens[0]}'}
        user2_headers = {'Authorization': f'Bearer {tokens[1]}'}
        
        # Get user2's bot ID
        response = client.get('/api/bots', headers=user2_headers)
        user2_bot_id = json.loads(response.data)['bots'][0]['id']
        
        # User1 tries to access user2's bot
        response = client.get(f'/api/bots/{user2_bot_id}', headers=user1_headers)
        assert response.status_code == 404  # Should not find bot belonging to another user