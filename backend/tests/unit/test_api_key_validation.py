"""Unit tests for API key validation and error handling."""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask

from models.user import User
from models.api_key import APIKey
from bot_engine.trading_engine import TradingEngine


class TestAPIKeyValidation:
    """Test API key validation and error handling."""
    
    def test_missing_api_keys_error(self, client, auth_headers, test_user):
        """Test ValueError handling for missing API keys."""
        with patch('flask_jwt_extended.get_jwt_identity', return_value=test_user.id), \
             patch('api.trading_routes.get_trading_engine') as mock_get_engine:
            
            # Mock the ValueError for missing API keys
            mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
            
            response = client.get('/api/trading/realtime-data/BTCUSDT', 
                                headers=auth_headers)
            
            assert response.status_code == 422
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'API keys not configured' in data['message']
    
    def test_missing_api_keys_market_data(self, client, auth_headers, test_user):
        """Test ValueError handling for missing API keys in market data endpoint."""
        with patch('flask_jwt_extended.get_jwt_identity', return_value=test_user.id), \
             patch('api.trading_routes.get_trading_engine') as mock_get_engine:
            
            mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
            
            response = client.get('/api/trading/market-data/BTCUSDT', 
                                headers=auth_headers)
            
            assert response.status_code == 422
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'API keys not configured' in data['message']
    
    def test_missing_api_keys_account_balance(self, client, auth_headers, test_user):
        """Test ValueError handling for missing API keys in account balance endpoint."""
        with patch('flask_jwt_extended.get_jwt_identity', return_value=test_user.id), \
             patch('api.trading_routes.get_trading_engine') as mock_get_engine:
            
            mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
            
            response = client.get('/api/trading/account/balance', 
                                headers=auth_headers)
            
            assert response.status_code == 422
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'API keys not configured' in data['message']
    
    def test_missing_api_keys_bot_creation(self, client, auth_headers, test_user):
        """Test ValueError handling for missing API keys in bot creation."""
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'scalping',
            'symbol': 'BTCUSDT',
            'base_amount': 100.0
        }
        
        with patch('flask_jwt_extended.get_jwt_identity', return_value=test_user.id), \
             patch('api.trading_routes.get_trading_engine') as mock_get_engine:
            
            mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
            
            response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 422
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'API keys not configured' in data['message']
    
    def test_valid_api_keys_success(self, client, auth_headers, test_user):
        """Test successful operation with valid API keys."""
        mock_engine = MagicMock()
        mock_engine.get_realtime_data.return_value = {
            'symbol': 'BTCUSDT',
            'price': 45000.0,
            'timestamp': '2024-01-01T00:00:00Z'
        }
        
        with patch('flask_jwt_extended.get_jwt_identity', return_value=test_user.id), \
             patch('api.trading_routes.get_trading_engine', return_value=mock_engine):
            
            response = client.get('/api/trading/realtime-data/BTCUSDT', 
                                headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['symbol'] == 'BTCUSDT'
    
    def test_other_value_error_handling(self, client, auth_headers, test_user):
        """Test handling of other ValueError exceptions."""
        with patch('flask_jwt_extended.get_jwt_identity', return_value=test_user.id), \
             patch('api.trading_routes.get_trading_engine') as mock_get_engine:
            
            # Mock a different ValueError
            mock_get_engine.side_effect = ValueError("Invalid symbol format")
            
            response = client.get('/api/trading/realtime-data/INVALID', 
                                headers=auth_headers)
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'An error occurred' in data['message']
    
    def test_general_exception_handling(self, client, auth_headers, test_user):
        """Test handling of general exceptions."""
        with patch('flask_jwt_extended.get_jwt_identity', return_value=test_user.id), \
             patch('api.trading_routes.get_trading_engine') as mock_get_engine:
            
            # Mock a general exception
            mock_get_engine.side_effect = Exception("Network error")
            
            response = client.get('/api/trading/realtime-data/BTCUSDT', 
                                headers=auth_headers)
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'An error occurred' in data['message']


class TestTradingEngineInitialization:
    """Test trading engine initialization and API key validation."""
    
    def test_trading_engine_missing_keys(self, app_context):
        """Test TradingEngine raises ValueError when API keys are missing."""
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            with pytest.raises(ValueError, match="MISSING_API_KEYS"):
                TradingEngine(user_id=1)
    
    def test_trading_engine_inactive_keys(self, app_context):
        """Test TradingEngine raises ValueError when API keys are inactive."""
        mock_api_key = MagicMock()
        mock_api_key.is_active = False
        
        with patch('bot_engine.trading_engine.APIKey.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = mock_api_key
            
            with pytest.raises(ValueError, match="MISSING_API_KEYS"):
                TradingEngine(user_id=1)
    
    def test_trading_engine_valid_keys(self, app_context):
        """Test TradingEngine initializes successfully with valid API keys."""
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
            assert engine is not None
            assert engine.exchange == mock_exchange_instance


class TestAPIKeyRoutes:
    """Test API key management routes."""
    
    def test_create_api_key_validation(self, client, auth_headers, test_user):
        """Test API key creation with validation."""
        api_key_data = {
            'key_name': 'Test Key',
            'exchange': 'binance',
            'api_key': 'test_api_key_12345',
            'api_secret': 'test_api_secret_12345',
            'testnet': True,
            'permissions': ['read', 'trade']
        }
        
        with patch('api.api_key_routes.get_current_user', return_value=test_user), \
             patch('api.api_key_routes.TradingEngine') as mock_engine_class:
            
            mock_engine = MagicMock()
            mock_engine.get_account_balance.return_value = {'USDT': 1000.0}
            mock_engine_class.return_value = mock_engine
            
            response = client.post('/api/keys',
                                 data=json.dumps(api_key_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_create_api_key_invalid_credentials(self, client, auth_headers, test_user):
        """Test API key creation with invalid credentials."""
        api_key_data = {
            'key_name': 'Invalid Key',
            'exchange': 'binance',
            'api_key': 'invalid_key',
            'api_secret': 'invalid_secret',
            'testnet': True,
            'permissions': ['read']
        }
        
        with patch('api.api_key_routes.get_current_user', return_value=test_user), \
             patch('api.api_key_routes.TradingEngine') as mock_engine_class:
            
            mock_engine = MagicMock()
            mock_engine.get_account_balance.return_value = None
            mock_engine_class.return_value = mock_engine
            
            response = client.post('/api/keys',
                                 data=json.dumps(api_key_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Invalid API credentials' in data['error']