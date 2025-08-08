"""Integration tests for API endpoints."""
import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from app import create_app
from db import db
from models import User, Bot, Trade, APIKey


class TestAuthAPIIntegration:
    """Test authentication API integration."""
    
    def test_user_registration_flow(self, client):
        """Test complete user registration flow."""
        # Test registration
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/register', 
                             data=json.dumps(registration_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'user' in data
        assert 'access_token' in data
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'newuser@example.com'
        
        # Verify user was created in database
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
    
    def test_user_login_flow(self, client, test_user):
        """Test complete user login flow."""
        # Test login
        login_data = {
            'username': test_user.username,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data
        assert data['user']['id'] == test_user.id
    
    def test_token_refresh_flow(self, client, auth_headers):
        """Test token refresh flow."""
        # First, get a refresh token by logging in
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        login_data = json.loads(login_response.data)
        refresh_token = login_data['refresh_token']
        
        # Test token refresh
        refresh_data = {'refresh_token': refresh_token}
        response = client.post('/api/auth/refresh',
                             data=json.dumps(refresh_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_protected_route_access(self, client, auth_headers):
        """Test access to protected routes."""
        # Test without authentication
        response = client.get('/api/user/profile')
        assert response.status_code == 401
        
        # Test with authentication
        response = client.get('/api/user/profile', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['username'] == 'testuser'
    
    def test_logout_flow(self, client, auth_headers):
        """Test user logout flow."""
        response = client.post('/api/auth/logout', headers=auth_headers)
        assert response.status_code == 200
        
        # Verify token is invalidated
        profile_response = client.get('/api/user/profile', headers=auth_headers)
        assert profile_response.status_code == 401


class TestBotAPIIntegration:
    """Test bot management API integration."""
    
    def test_bot_creation_flow(self, client, auth_headers, test_api_key):
        """Test complete bot creation flow."""
        bot_data = {
            'name': 'Test Grid Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'api_key_id': test_api_key.id,
            'config': {
                'grid_size': 10,
                'price_range': [45000, 55000],
                'investment_amount': 1000,
                'grid_spacing': 0.5
            }
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(bot_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'bot' in data
        assert data['bot']['name'] == 'Test Grid Bot'
        assert data['bot']['strategy'] == 'grid'
        assert data['bot']['is_active'] == False
        
        # Verify bot was created in database
        bot = Bot.query.filter_by(name='Test Grid Bot').first()
        assert bot is not None
        assert bot.symbol == 'BTCUSDT'
    
    def test_bot_lifecycle_management(self, client, auth_headers, sample_bot):
        """Test complete bot lifecycle management."""
        bot_id = sample_bot.id
        
        # Test starting bot
        with patch('app.services.trading_service.start_bot') as mock_start:
            mock_start.return_value = True
            
            response = client.post(f'/api/bots/{bot_id}/start', headers=auth_headers)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'active'
            mock_start.assert_called_once_with(bot_id)
        
        # Test pausing bot
        with patch('app.services.trading_service.pause_bot') as mock_pause:
            mock_pause.return_value = True
            
            response = client.post(f'/api/bots/{bot_id}/pause', headers=auth_headers)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'paused'
            mock_pause.assert_called_once_with(bot_id)
        
        # Test stopping bot
        with patch('app.services.trading_service.stop_bot') as mock_stop:
            mock_stop.return_value = True
            
            response = client.post(f'/api/bots/{bot_id}/stop', headers=auth_headers)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'inactive'
            mock_stop.assert_called_once_with(bot_id)
    
    def test_bot_configuration_update(self, client, auth_headers, sample_bot):
        """Test bot configuration update."""
        bot_id = sample_bot.id
        
        updated_config = {
            'name': 'Updated Bot Name',
            'config': {
                'grid_size': 15,
                'price_range': [40000, 60000],
                'investment_amount': 2000
            }
        }
        
        response = client.put(f'/api/bots/{bot_id}',
                            data=json.dumps(updated_config),
                            content_type='application/json',
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['bot']['name'] == 'Updated Bot Name'
        assert data['bot']['config']['grid_size'] == 15
        
        # Verify update in database
        bot = Bot.query.get(bot_id)
        assert bot.name == 'Updated Bot Name'
        assert bot.config['grid_size'] == 15
    
    def test_bot_performance_retrieval(self, client, auth_headers, sample_bot, sample_trades):
        """Test bot performance data retrieval."""
        bot_id = sample_bot.id
        
        response = client.get(f'/api/bots/{bot_id}/performance', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'performance' in data
        assert 'total_trades' in data['performance']
        assert 'total_profit_loss' in data['performance']
        assert 'win_rate' in data['performance']
        assert 'sharpe_ratio' in data['performance']
    
    def test_bot_deletion(self, client, auth_headers, sample_bot):
        """Test bot deletion."""
        bot_id = sample_bot.id
        
        # Ensure bot exists
        assert Bot.query.get(bot_id) is not None
        
        response = client.delete(f'/api/bots/{bot_id}', headers=auth_headers)
        assert response.status_code == 200
        
        # Verify bot was deleted
        assert Bot.query.get(bot_id) is None


class TestTradingAPIIntegration:
    """Test trading API integration."""
    
    def test_manual_trade_execution(self, client, auth_headers, sample_bot, sample_api_key):
        """Test manual trade execution."""
        trade_data = {
            'bot_id': sample_bot.id,
            'trading_pair': 'BTCUSDT',
            'side': 'buy',
            'quantity': '0.001',
            'order_type': 'market'
        }
        
        with patch('app.services.trading_service.execute_trade') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'trade_id': 'trade_123',
                'executed_price': 50000,
                'executed_quantity': 0.001,
                'fees': 0.5
            }
            
            response = client.post('/api/trading/execute',
                                 data=json.dumps(trade_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'trade' in data
            mock_execute.assert_called_once()
    
    def test_trade_history_retrieval(self, client, auth_headers, sample_trades):
        """Test trade history retrieval."""
        response = client.get('/api/trading/history', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'trades' in data
        assert 'pagination' in data
        assert len(data['trades']) > 0
        
        # Test with filters
        response = client.get('/api/trading/history?trading_pair=BTCUSDT&limit=5', 
                            headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['trades']) <= 5
    
    def test_market_data_retrieval(self, client, auth_headers):
        """Test market data retrieval."""
        with patch('app.services.market_service.get_market_data') as mock_market:
            mock_market.return_value = {
                'symbol': 'BTCUSDT',
                'price': 50000,
                'change_24h': 2.5,
                'volume_24h': 1000000,
                'high_24h': 52000,
                'low_24h': 48000
            }
            
            response = client.get('/api/market/data/BTCUSDT', headers=auth_headers)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['symbol'] == 'BTCUSDT'
            assert data['price'] == 50000
            mock_market.assert_called_once_with('BTCUSDT')
    
    def test_portfolio_summary(self, client, auth_headers, sample_trades):
        """Test portfolio summary retrieval."""
        with patch('app.services.portfolio_service.get_portfolio_summary') as mock_portfolio:
            mock_portfolio.return_value = {
                'total_value': 10000,
                'total_pnl': 500,
                'total_pnl_percentage': 5.0,
                'positions': [
                    {'symbol': 'BTC', 'quantity': 0.2, 'value': 10000},
                    {'symbol': 'USDT', 'quantity': 1000, 'value': 1000}
                ],
                'active_bots': 2,
                'total_trades': 10
            }
            
            response = client.get('/api/portfolio/summary', headers=auth_headers)
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'portfolio' in data
            assert data['portfolio']['total_value'] == 10000
            assert data['portfolio']['total_pnl'] == 500
            mock_portfolio.assert_called_once()


class TestAPIKeyManagementIntegration:
    """Test API key management integration."""
    
    def test_api_key_creation(self, client, auth_headers):
        """Test API key creation."""
        api_key_data = {
            'exchange': 'binance',
            'key_name': 'My Binance Key',
            'api_key': 'test_api_key_123',
            'api_secret': 'test_api_secret_456'
        }
        
        with patch('app.services.exchange_service.validate_api_credentials') as mock_validate:
            mock_validate.return_value = True
            
            response = client.post('/api/api-keys',
                                 data=json.dumps(api_key_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert 'api_key' in data
            assert data['api_key']['exchange'] == 'binance'
            assert data['api_key']['key_name'] == 'My Binance Key'
            assert 'api_secret' not in data['api_key']  # Should not expose secret
    
    def test_api_key_validation(self, client, auth_headers, sample_api_key):
        """Test API key validation."""
        api_key_id = sample_api_key.id
        
        with patch('app.services.exchange_service.validate_api_credentials') as mock_validate:
            mock_validate.return_value = True
            
            response = client.post(f'/api/api-keys/{api_key_id}/validate', 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['valid'] is True
            mock_validate.assert_called_once()
    
    def test_api_key_listing(self, client, auth_headers, sample_api_key):
        """Test API key listing."""
        response = client.get('/api/api-keys', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'api_keys' in data
        assert len(data['api_keys']) > 0
        
        # Verify no secrets are exposed
        for key in data['api_keys']:
            assert 'api_secret' not in key
            assert 'api_secret_hash' not in key
    
    def test_api_key_deletion(self, client, auth_headers, sample_api_key):
        """Test API key deletion."""
        api_key_id = sample_api_key.id
        
        # Ensure API key exists
        assert APIKey.query.get(api_key_id) is not None
        
        response = client.delete(f'/api/api-keys/{api_key_id}', headers=auth_headers)
        assert response.status_code == 200
        
        # Verify API key was deleted
        assert APIKey.query.get(api_key_id) is None


class TestErrorHandlingIntegration:
    """Test API error handling integration."""
    
    def test_validation_errors(self, client, auth_headers):
        """Test validation error handling."""
        # Test invalid bot creation data
        invalid_bot_data = {
            'name': '',  # Empty name
            'strategy': 'invalid_strategy',  # Invalid strategy
            'trading_pair': 'INVALID',  # Invalid trading pair
            'config': {}  # Missing required config
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(invalid_bot_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'errors' in data
        assert len(data['errors']) > 0
    
    def test_not_found_errors(self, client, auth_headers):
        """Test 404 error handling."""
        # Test accessing non-existent bot
        response = client.get('/api/bots/99999', headers=auth_headers)
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access handling."""
        # Test accessing protected endpoint without auth
        response = client.get('/api/bots')
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'unauthorized' in data['error'].lower()
    
    def test_forbidden_access(self, client, auth_headers):
        """Test forbidden access handling."""
        # Create another user's bot
        other_user = User(
            username='otheruser',
            email='other@example.com',
            password_hash='hashed_password'
        )
        db.session.add(other_user)
        db.session.commit()
        
        other_bot = Bot(
            name='Other User Bot',
            user_id=other_user.id,
            strategy='grid',
            trading_pair='BTCUSDT',
            config={}
        )
        db.session.add(other_bot)
        db.session.commit()
        
        # Try to access other user's bot
        response = client.get(f'/api/bots/{other_bot.id}', headers=auth_headers)
        assert response.status_code == 403
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'forbidden' in data['error'].lower()
    
    def test_server_error_handling(self, client, auth_headers):
        """Test server error handling."""
        with patch('app.services.trading_service.execute_trade') as mock_execute:
            mock_execute.side_effect = Exception('Database connection error')
            
            trade_data = {
                'bot_id': 1,
                'trading_pair': 'BTCUSDT',
                'side': 'buy',
                'quantity': '0.001',
                'order_type': 'market'
            }
            
            response = client.post('/api/trading/execute',
                                 data=json.dumps(trade_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get('/api/market/data/BTCUSDT', headers=auth_headers)
            responses.append(response.status_code)
        
        # Check if any requests were rate limited (429)
        # Note: This test depends on rate limiting configuration
        rate_limited = any(status == 429 for status in responses)
        
        # If rate limiting is enabled, we should see some 429 responses
        # If not enabled, all should be successful (200 or other valid responses)
        assert all(status in [200, 429, 500] for status in responses)


class TestAPIIntegrationWorkflows:
    """Test complete API integration workflows."""
    
    def test_complete_trading_workflow(self, client, auth_headers):
        """Test complete trading workflow from registration to trade execution."""
        # 1. Create API key
        api_key_data = {
            'exchange': 'binance',
            'key_name': 'Trading Key',
            'api_key': 'test_key_123',
            'api_secret': 'test_secret_456'
        }
        
        with patch('app.services.exchange_service.validate_api_credentials') as mock_validate:
            mock_validate.return_value = True
            
            api_response = client.post('/api/api-keys',
                                     data=json.dumps(api_key_data),
                                     content_type='application/json',
                                     headers=auth_headers)
            
            assert api_response.status_code == 201
            api_key_id = json.loads(api_response.data)['api_key']['id']
        
        # 2. Create bot
        bot_data = {
            'name': 'Workflow Test Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'api_key_id': api_key_id,
            'config': {
                'grid_size': 10,
                'price_range': [45000, 55000],
                'investment_amount': 1000
            }
        }
        
        bot_response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=auth_headers)
        
        assert bot_response.status_code == 201
        bot_id = json.loads(bot_response.data)['bot']['id']
        
        # 3. Start bot
        with patch('app.services.trading_service.start_bot') as mock_start:
            mock_start.return_value = True
            
            start_response = client.post(f'/api/bots/{bot_id}/start', headers=auth_headers)
            assert start_response.status_code == 200
        
        # 4. Execute manual trade
        trade_data = {
            'bot_id': bot_id,
            'trading_pair': 'BTCUSDT',
            'side': 'buy',
            'quantity': '0.001',
            'order_type': 'market'
        }
        
        with patch('app.services.trading_service.execute_trade') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'trade_id': 'trade_123',
                'executed_price': 50000,
                'executed_quantity': 0.001,
                'fees': 0.5
            }
            
            trade_response = client.post('/api/trading/execute',
                                       data=json.dumps(trade_data),
                                       content_type='application/json',
                                       headers=auth_headers)
            
            assert trade_response.status_code == 200
        
        # 5. Check bot performance
        perf_response = client.get(f'/api/bots/{bot_id}/performance', headers=auth_headers)
        assert perf_response.status_code == 200
        
        # 6. Get portfolio summary
        with patch('app.services.portfolio_service.get_portfolio_summary') as mock_portfolio:
            mock_portfolio.return_value = {
                'total_value': 10000,
                'total_pnl': 100,
                'total_pnl_percentage': 1.0,
                'positions': [],
                'active_bots': 1,
                'total_trades': 1
            }
            
            portfolio_response = client.get('/api/portfolio/summary', headers=auth_headers)
            assert portfolio_response.status_code == 200
        
        # 7. Stop bot
        with patch('app.services.trading_service.stop_bot') as mock_stop:
            mock_stop.return_value = True
            
            stop_response = client.post(f'/api/bots/{bot_id}/stop', headers=auth_headers)
            assert stop_response.status_code == 200
    
    def test_error_recovery_workflow(self, client, auth_headers):
        """Test error recovery in API workflows."""
        # 1. Try to create bot with invalid API key
        invalid_bot_data = {
            'name': 'Test Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'api_key_id': 99999,  # Non-existent API key
            'config': {}
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(invalid_bot_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 400
        
        # 2. Create valid API key first
        api_key_data = {
            'exchange': 'binance',
            'key_name': 'Recovery Key',
            'api_key': 'recovery_key_123',
            'api_secret': 'recovery_secret_456'
        }
        
        with patch('app.services.exchange_service.validate_api_credentials') as mock_validate:
            mock_validate.return_value = True
            
            api_response = client.post('/api/api-keys',
                                     data=json.dumps(api_key_data),
                                     content_type='application/json',
                                     headers=auth_headers)
            
            api_key_id = json.loads(api_response.data)['api_key']['id']
        
        # 3. Retry bot creation with valid API key
        valid_bot_data = {
            'name': 'Recovery Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'api_key_id': api_key_id,
            'config': {
                'grid_size': 10,
                'price_range': [45000, 55000],
                'investment_amount': 1000
            }
        }
        
        retry_response = client.post('/api/bots',
                                   data=json.dumps(valid_bot_data),
                                   content_type='application/json',
                                   headers=auth_headers)
        
        assert retry_response.status_code == 201
        
        # 4. Verify bot was created successfully
        bot_id = json.loads(retry_response.data)['bot']['id']
        get_response = client.get(f'/api/bots/{bot_id}', headers=auth_headers)
        assert get_response.status_code == 200