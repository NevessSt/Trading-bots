import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from api.trading_routes import trading_bp
from services.trading_service import TradingService


class TestTradingRoutesErrorHandling:
    """Test error handling in trading routes, specifically ValueError for missing API keys."""
    
    @pytest.fixture
    def app(self):
        """Create a test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(trading_bp, url_prefix='/api')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {'Authorization': 'Bearer test_token'}
    
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_start_trading_missing_api_keys(self, mock_jwt_identity, mock_jwt_required, mock_get_engine, client, auth_headers):
        """Test start_trading route returns 422 when API keys are missing."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
        
        # Make request
        response = client.post('/api/start-trading', 
                             json={'symbol': 'BTCUSDT', 'strategy': 'test'},
                             headers=auth_headers)
        
        # Assertions
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'API keys not configured' in data['error']
    
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_get_realtime_data_missing_api_keys(self, mock_jwt_identity, mock_jwt_required, mock_get_engine, client, auth_headers):
        """Test get_realtime_data route returns 422 when API keys are missing."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
        
        # Make request
        response = client.get('/api/realtime-data/BTCUSDT', headers=auth_headers)
        
        # Assertions
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'API keys not configured' in data['error']
    
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_get_account_balance_missing_api_keys(self, mock_jwt_identity, mock_jwt_required, mock_get_engine, client, auth_headers):
        """Test get_account_balance route returns 422 when API keys are missing."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
        
        # Make request
        response = client.get('/api/account-balance', headers=auth_headers)
        
        # Assertions
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'API keys not configured' in data['error']
    
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_start_bot_missing_api_keys(self, mock_jwt_identity, mock_jwt_required, mock_get_engine, client, auth_headers):
        """Test start_bot route returns 422 when API keys are missing."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
        
        # Make request
        response = client.post('/api/bots/1/start', headers=auth_headers)
        
        # Assertions
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'API keys not configured' in data['error']
    
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_delete_bot_missing_api_keys(self, mock_jwt_identity, mock_jwt_required, mock_get_engine, client, auth_headers):
        """Test delete_bot route returns 422 when API keys are missing."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
        
        # Make request
        response = client.delete('/api/bots/1', headers=auth_headers)
        
        # Assertions
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'API keys not configured' in data['error']
    
    @patch('api.trading_routes.get_trading_engine')
    @patch('api.trading_routes.jwt_required')
    @patch('api.trading_routes.get_jwt_identity')
    def test_get_performance_missing_api_keys(self, mock_jwt_identity, mock_jwt_required, mock_get_engine, client, auth_headers):
        """Test get_performance route returns 422 when API keys are missing."""
        # Setup mocks
        mock_jwt_identity.return_value = 1
        mock_jwt_required.return_value = None
        mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
        
        # Make request
        response = client.get('/api/performance', headers=auth_headers)
        
        # Assertions
        assert response.status_code == 422
        data = json.loads(response.data)
        assert 'API keys not configured' in data['error']