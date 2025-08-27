import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from flask import Flask
from api.auth_routes import auth_bp
from api.trading_routes import trading_bp
from api.api_key_routes import api_key_bp


class TestCompleteWorkflow:
    """Integration test for complete trading bot workflow."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app with all blueprints."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(trading_bp, url_prefix='/api')
        app.register_blueprint(api_key_bp, url_prefix='/api')
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @pytest.fixture
    def auth_token(self):
        """Mock JWT token for authentication."""
        return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Authentication headers with JWT token."""
        return {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    @patch('api.auth_routes.AuthService')
    @patch('api.auth_routes.create_access_token')
    def test_user_registration_and_login(self, mock_create_token, mock_auth_service, client):
        """Test user registration and login workflow."""
        # Mock successful registration
        mock_auth_service.return_value.register_user.return_value = {
            'status': 'success',
            'user_id': 1,
            'message': 'User registered successfully'
        }
        
        # Mock successful login
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_auth_service.return_value.authenticate_user.return_value = mock_user
        mock_create_token.return_value = 'test_jwt_token'
        
        # Register user
        register_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        
        register_response = client.post('/api/auth/register', 
                                      json=register_data)
        assert register_response.status_code == 201
        
        # Login user
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        login_response = client.post('/api/auth/login', 
                                   json=login_data)
        assert login_response.status_code == 200
        
        login_result = json.loads(login_response.data)
        assert 'access_token' in login_result
    
    @patch('api.api_key_routes.APIKeyService')
    @patch('api.api_key_routes.jwt_required')
    @patch('api.api_key_routes.get_jwt_identity')
    def test_api_key_management_workflow(self, mock_jwt_identity, mock_jwt_required, 
                                       mock_api_service, client, auth_headers):
        """Test API key creation, retrieval, and validation workflow."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        
        # Mock API key creation
        mock_api_service.return_value.create_api_key.return_value = {
            'id': 1,
            'exchange': 'binance',
            'status': 'active'
        }
        
        # Mock API key retrieval
        mock_api_service.return_value.get_api_keys.return_value = {
            'id': 1,
            'exchange': 'binance',
            'api_key': 'abcd****5678',  # Masked
            'status': 'active'
        }
        
        # Create API key
        api_key_data = {
            'exchange': 'binance',
            'api_key': 'test_api_key_12345',
            'api_secret': 'test_api_secret_67890'
        }
        
        create_response = client.post('/api/api-keys', 
                                    json=api_key_data,
                                    headers=auth_headers)
        assert create_response.status_code == 201
        
        # Retrieve API keys
        get_response = client.get('/api/api-keys', headers=auth_headers)
        assert get_response.status_code == 200
        
        keys_data = json.loads(get_response.data)
        assert keys_data['exchange'] == 'binance'
        assert '****' in keys_data['api_key']  # Should be masked
    
    @patch('api.trading_routes.TradingService')
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_complete_bot_trading_workflow(self, mock_jwt_identity, mock_jwt_required,
                                         mock_get_engine, mock_trading_service, 
                                         client, auth_headers):
        """Test complete bot creation, start, trading, and stop workflow."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        
        # Mock trading engine
        mock_engine = Mock()
        mock_engine.get_account_balance.return_value = {
            'USDT': {'free': 1000.0, 'used': 0.0, 'total': 1000.0}
        }
        mock_engine.get_market_data.return_value = {
            'symbol': 'BTC/USDT',
            'last': 45000.0,
            'bid': 44999.0,
            'ask': 45001.0
        }
        mock_get_engine.return_value = mock_engine
        
        # Mock trading service
        mock_service = mock_trading_service.return_value
        
        # Mock bot creation
        mock_service.create_bot.return_value = {
            'id': 1,
            'name': 'Test Bot',
            'symbol': 'BTCUSDT',
            'strategy': 'moving_average',
            'status': 'inactive'
        }
        
        # Mock bot start
        mock_service.start_bot.return_value = {
            'status': 'success',
            'message': 'Bot started successfully'
        }
        
        # Mock bot performance
        mock_service.get_bot_performance.return_value = {
            'total_return': 0.05,
            'win_rate': 0.60,
            'total_trades': 10,
            'profit_loss': 50.0
        }
        
        # Mock bot stop
        mock_service.stop_bot.return_value = {
            'status': 'success',
            'message': 'Bot stopped successfully'
        }
        
        # Step 1: Check account balance
        balance_response = client.get('/api/account-balance', headers=auth_headers)
        assert balance_response.status_code == 200
        
        balance_data = json.loads(balance_response.data)
        assert balance_data['USDT']['free'] == 1000.0
        
        # Step 2: Get market data
        market_response = client.get('/api/market-data/BTCUSDT', headers=auth_headers)
        assert market_response.status_code == 200
        
        market_data = json.loads(market_response.data)
        assert market_data['symbol'] == 'BTC/USDT'
        assert market_data['last'] == 45000.0
        
        # Step 3: Create bot
        bot_data = {
            'name': 'Test Bot',
            'symbol': 'BTCUSDT',
            'strategy': 'moving_average',
            'parameters': {
                'period': 20,
                'threshold': 0.02
            }
        }
        
        create_bot_response = client.post('/api/bots', 
                                        json=bot_data,
                                        headers=auth_headers)
        assert create_bot_response.status_code == 201
        
        bot_result = json.loads(create_bot_response.data)
        bot_id = bot_result['id']
        assert bot_result['name'] == 'Test Bot'
        assert bot_result['status'] == 'inactive'
        
        # Step 4: Start bot
        start_response = client.post(f'/api/bots/{bot_id}/start', 
                                   headers=auth_headers)
        assert start_response.status_code == 200
        
        start_result = json.loads(start_response.data)
        assert start_result['status'] == 'success'
        
        # Step 5: Check bot performance (after some trading)
        performance_response = client.get(f'/api/bots/{bot_id}/performance', 
                                        headers=auth_headers)
        assert performance_response.status_code == 200
        
        performance_data = json.loads(performance_response.data)
        assert performance_data['total_return'] == 0.05
        assert performance_data['total_trades'] == 10
        
        # Step 6: Stop bot
        stop_response = client.post(f'/api/bots/{bot_id}/stop', 
                                  headers=auth_headers)
        assert stop_response.status_code == 200
        
        stop_result = json.loads(stop_response.data)
        assert stop_result['status'] == 'success'
    
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_error_handling_missing_api_keys_workflow(self, mock_jwt_identity, 
                                                    mock_jwt_required, mock_get_engine,
                                                    client, auth_headers):
        """Test error handling when API keys are missing throughout workflow."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
        
        # Test various endpoints that should return 422 for missing API keys
        endpoints_to_test = [
            ('/api/account-balance', 'GET'),
            ('/api/market-data/BTCUSDT', 'GET'),
            ('/api/realtime-data/BTCUSDT', 'GET'),
            ('/api/performance', 'GET'),
            ('/api/available-symbols', 'GET')
        ]
        
        for endpoint, method in endpoints_to_test:
            if method == 'GET':
                response = client.get(endpoint, headers=auth_headers)
            elif method == 'POST':
                response = client.post(endpoint, headers=auth_headers)
            
            assert response.status_code == 422
            error_data = json.loads(response.data)
            assert 'API keys not configured' in error_data['error']
    
    def test_unauthorized_access_workflow(self, client):
        """Test that endpoints properly reject unauthorized requests."""
        # Test endpoints without authentication headers
        endpoints_to_test = [
            '/api/account-balance',
            '/api/bots',
            '/api/api-keys',
            '/api/performance'
        }
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should return 401 Unauthorized or 422 Unprocessable Entity
            assert response.status_code in [401, 422]