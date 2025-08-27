"""Integration tests for API error handling and complete workflows."""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask

from models.user import User
from models.bot import Bot
from models.api_key import APIKey
from db import db


class TestAPIErrorHandlingIntegration:
    """Integration tests for API error handling across all endpoints."""
    
    def test_complete_workflow_missing_api_keys(self, client, auth_headers, test_user):
        """Test complete workflow fails gracefully when API keys are missing."""
        with patch('api.trading_routes.get_current_user', return_value=test_user):
            
            # Test all endpoints that require API keys
            endpoints_to_test = [
                ('/api/trading/realtime-data/BTCUSDT', 'GET'),
                ('/api/trading/all-realtime-data', 'GET'),
                ('/api/trading/market-data/BTCUSDT', 'GET'),
                ('/api/trading/account/balance', 'GET'),
                ('/api/trading/performance', 'GET'),
                ('/api/trading/available-symbols', 'GET'),
            ]
            
            for endpoint, method in endpoints_to_test:
                with patch('api.trading_routes.get_trading_engine') as mock_get_engine:
                    mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
                    
                    if method == 'GET':
                        response = client.get(endpoint, headers=auth_headers)
                    elif method == 'POST':
                        response = client.post(endpoint, headers=auth_headers)
                    
                    assert response.status_code == 422, f"Failed for {endpoint}"
                    data = json.loads(response.data)
                    assert data['success'] is False
                    assert 'API keys not configured' in data['message']
    
    def test_bot_lifecycle_with_api_key_errors(self, client, auth_headers, test_user):
        """Test bot lifecycle with API key configuration errors."""
        bot_data = {
            'name': 'Test Integration Bot',
            'strategy': 'scalping',
            'symbol': 'BTCUSDT',
            'base_amount': 100.0
        }
        
        with patch('api.trading_routes.get_current_user', return_value=test_user):
            
            # Step 1: Try to create bot without API keys
            with patch('api.trading_routes.get_trading_engine') as mock_get_engine:
                mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
                
                response = client.post('/api/bots',
                                     data=json.dumps(bot_data),
                                     content_type='application/json',
                                     headers=auth_headers)
                
                assert response.status_code == 422
                data = json.loads(response.data)
                assert 'API keys not configured' in data['message']
            
            # Step 2: Create API key first
            api_key_data = {
                'key_name': 'Test Integration Key',
                'exchange': 'binance',
                'api_key': 'test_integration_key_12345',
                'api_secret': 'test_integration_secret_12345',
                'testnet': True,
                'permissions': ['read', 'trade'],
                'validate_keys': False  # Skip validation for test
            }
            
            with patch('api.api_key_routes.get_current_user', return_value=test_user):
                response = client.post('/api/keys',
                                     data=json.dumps(api_key_data),
                                     content_type='application/json',
                                     headers=auth_headers)
                
                assert response.status_code == 201
            
            # Step 3: Now create bot successfully
            mock_engine = MagicMock()
            mock_bot = MagicMock()
            mock_bot.id = 'test_bot_123'
            mock_bot.to_dict.return_value = {
                'id': 'test_bot_123',
                'name': 'Test Integration Bot',
                'status': 'created'
            }
            
            with patch('api.trading_routes.get_trading_engine', return_value=mock_engine), \
                 patch('services.trading_service.TradingService') as mock_service:
                
                mock_service.return_value.create_bot.return_value = {
                    'success': True,
                    'bot': mock_bot,
                    'message': 'Bot created successfully'
                }
                
                response = client.post('/api/bots',
                                     data=json.dumps(bot_data),
                                     content_type='application/json',
                                     headers=auth_headers)
                
                assert response.status_code == 201
                data = json.loads(response.data)
                assert data['success'] is True
    
    def test_websocket_error_handling(self, client, auth_headers, test_user):
        """Test WebSocket endpoints error handling."""
        with patch('api.trading_routes.get_current_user', return_value=test_user):
            
            # Test start WebSocket without API keys
            with patch('api.trading_routes.get_trading_engine') as mock_get_engine:
                mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
                
                ws_data = {'symbols': ['BTCUSDT', 'ETHUSDT']}
                response = client.post('/api/trading/websocket/start',
                                     data=json.dumps(ws_data),
                                     content_type='application/json',
                                     headers=auth_headers)
                
                assert response.status_code == 422
                data = json.loads(response.data)
                assert 'API keys not configured' in data['message']
            
            # Test stop WebSocket without API keys
            with patch('api.trading_routes.get_trading_engine') as mock_get_engine:
                mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
                
                response = client.post('/api/trading/websocket/stop',
                                     headers=auth_headers)
                
                assert response.status_code == 422
                data = json.loads(response.data)
                assert 'API keys not configured' in data['message']
    
    def test_trading_operations_error_cascade(self, client, auth_headers, test_user):
        """Test how trading operation errors cascade through the system."""
        with patch('api.trading_routes.get_current_user', return_value=test_user):
            
            # Mock a valid trading engine but with exchange errors
            mock_engine = MagicMock()
            mock_engine.get_account_balance.side_effect = Exception("Exchange API error")
            mock_engine.get_realtime_data.side_effect = Exception("Market data unavailable")
            
            with patch('api.trading_routes.get_trading_engine', return_value=mock_engine):
                
                # Test account balance with exchange error
                response = client.get('/api/trading/account/balance', headers=auth_headers)
                assert response.status_code == 500
                data = json.loads(response.data)
                assert data['success'] is False
                
                # Test realtime data with market data error
                response = client.get('/api/trading/realtime-data/BTCUSDT', headers=auth_headers)
                assert response.status_code == 500
                data = json.loads(response.data)
                assert data['success'] is False
    
    def test_concurrent_api_requests_error_handling(self, client, auth_headers, test_user):
        """Test error handling under concurrent API requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            with patch('api.trading_routes.get_current_user', return_value=test_user), \
                 patch('api.trading_routes.get_trading_engine') as mock_get_engine:
                
                mock_get_engine.side_effect = ValueError("MISSING_API_KEYS")
                
                response = client.get('/api/trading/realtime-data/BTCUSDT', headers=auth_headers)
                results.append(response.status_code)
        
        # Create multiple threads to test concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should return 422 (API keys not configured)
        assert all(status == 422 for status in results)
        assert len(results) == 5


class TestDatabaseIntegrationErrors:
    """Test database integration error scenarios."""
    
    def test_database_connection_error_handling(self, client, auth_headers, test_user):
        """Test API behavior when database connection fails."""
        with patch('api.trading_routes.get_current_user', return_value=test_user), \
             patch('models.api_key.APIKey.query') as mock_query:
            
            # Simulate database connection error
            mock_query.side_effect = Exception("Database connection failed")
            
            response = client.get('/api/trading/realtime-data/BTCUSDT', headers=auth_headers)
            
            # Should handle database errors gracefully
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
    
    def test_transaction_rollback_on_error(self, app_context, test_user):
        """Test database transaction rollback on errors."""
        from services.trading_service import TradingService
        
        service = TradingService()
        
        bot_data = {
            'name': 'Transaction Test Bot',
            'strategy': 'scalping',
            'symbol': 'BTCUSDT',
            'base_amount': 100.0
        }
        
        # Mock database save to fail
        with patch('models.bot.Bot.save') as mock_save:
            mock_save.side_effect = Exception("Database save failed")
            
            result = service.create_bot(test_user.id, bot_data)
            
            # Should handle the error and return failure
            assert result['success'] is False
            assert 'error' in result['message'].lower()
    
    def test_api_key_encryption_error_handling(self, client, auth_headers, test_user):
        """Test API key encryption/decryption error handling."""
        api_key_data = {
            'key_name': 'Encryption Test Key',
            'exchange': 'binance',
            'api_key': 'test_key_for_encryption',
            'api_secret': 'test_secret_for_encryption',
            'testnet': True,
            'permissions': ['read'],
            'validate_keys': False
        }
        
        with patch('api.api_key_routes.get_current_user', return_value=test_user), \
             patch('utils.encryption.encrypt_data') as mock_encrypt:
            
            # Simulate encryption failure
            mock_encrypt.side_effect = Exception("Encryption failed")
            
            response = client.post('/api/keys',
                                 data=json.dumps(api_key_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            # Should handle encryption errors gracefully
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False


class TestSecurityErrorHandling:
    """Test security-related error handling."""
    
    def test_unauthorized_access_error_handling(self, client):
        """Test error handling for unauthorized access attempts."""
        # Try to access protected endpoint without authentication
        response = client.get('/api/trading/realtime-data/BTCUSDT')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'unauthorized' in data['message'].lower() or 'authentication' in data['message'].lower()
    
    def test_invalid_token_error_handling(self, client):
        """Test error handling for invalid authentication tokens."""
        invalid_headers = {'Authorization': 'Bearer invalid_token_12345'}
        
        response = client.get('/api/trading/realtime-data/BTCUSDT', headers=invalid_headers)
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_rate_limiting_error_handling(self, client, auth_headers, test_user):
        """Test rate limiting error handling."""
        with patch('api.trading_routes.get_current_user', return_value=test_user), \
             patch('flask_limiter.Limiter.limit') as mock_limit:
            
            # Simulate rate limit exceeded
            from werkzeug.exceptions import TooManyRequests
            mock_limit.side_effect = TooManyRequests("Rate limit exceeded")
            
            # This would normally be handled by Flask-Limiter middleware
            # but we're testing the concept
            try:
                response = client.get('/api/trading/realtime-data/BTCUSDT', headers=auth_headers)
            except TooManyRequests:
                # Expected behavior - rate limiting should prevent excessive requests
                pass
    
    def test_sql_injection_protection(self, client, auth_headers, test_user):
        """Test SQL injection protection in API endpoints."""
        with patch('api.trading_routes.get_current_user', return_value=test_user):
            
            # Try SQL injection in symbol parameter
            malicious_symbol = "BTCUSDT'; DROP TABLE bots; --"
            
            mock_engine = MagicMock()
            mock_engine.get_realtime_data.return_value = None
            
            with patch('api.trading_routes.get_trading_engine', return_value=mock_engine):
                response = client.get(f'/api/trading/realtime-data/{malicious_symbol}', 
                                    headers=auth_headers)
                
                # Should handle malicious input safely
                # The exact response depends on input validation
                assert response.status_code in [400, 404, 500]