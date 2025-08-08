"""Unit tests for API routes."""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for

from app import create_app
from models.user import User
from models.bot import Bot
from models.trade import Trade


class TestAuthRoutes:
    """Test cases for authentication routes."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        }
        
        with patch('app.routes.auth.AuthService') as mock_auth_service:
            mock_auth_service.return_value.register_user.return_value = {
                'success': True,
                'message': 'User registered successfully',
                'user': {'id': 1, 'username': 'newuser', 'email': 'newuser@example.com'}
            }
            
            response = client.post('/api/auth/register', 
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == 'User registered successfully'
    
    def test_register_validation_error(self, client):
        """Test registration with validation errors."""
        user_data = {
            'username': '',  # Empty username
            'email': 'invalid-email',  # Invalid email
            'password': '123'  # Weak password
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'errors' in data
    
    def test_register_duplicate_user(self, client):
        """Test registration with duplicate user."""
        user_data = {
            'username': 'existinguser',
            'email': 'existing@example.com',
            'password': 'password123'
        }
        
        with patch('app.routes.auth.AuthService') as mock_auth_service:
            mock_auth_service.return_value.register_user.return_value = {
                'success': False,
                'message': 'Username already exists'
            }
            
            response = client.post('/api/auth/register',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            
            assert response.status_code == 409
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'already exists' in data['message']
    
    def test_login_success(self, client):
        """Test successful user login."""
        login_data = {
            'username': 'testuser',
            'password': 'password123'
        }
        
        with patch('app.routes.auth.AuthService') as mock_auth_service:
            mock_auth_service.return_value.login_user.return_value = {
                'success': True,
                'message': 'Login successful',
                'access_token': 'test_token',
                'user': {'id': 1, 'username': 'testuser'}
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'access_token' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        with patch('app.routes.auth.AuthService') as mock_auth_service:
            mock_auth_service.return_value.login_user.return_value = {
                'success': False,
                'message': 'Invalid username or password'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data['success'] is False
    
    def test_logout_success(self, client, auth_headers):
        """Test successful user logout."""
        with patch('app.routes.auth.AuthService') as mock_auth_service:
            mock_auth_service.return_value.logout_user.return_value = {
                'success': True,
                'message': 'Logged out successfully'
            }
            
            response = client.post('/api/auth/logout', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_profile_get(self, client, auth_headers, test_user):
        """Test getting user profile."""
        with patch('app.routes.auth.get_current_user', return_value=test_user):
            response = client.get('/api/auth/profile', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['username'] == test_user.username
            assert data['email'] == test_user.email
    
    def test_profile_update(self, client, auth_headers, test_user):
        """Test updating user profile."""
        update_data = {
            'email': 'newemail@example.com'
        }
        
        with patch('app.routes.auth.get_current_user', return_value=test_user), \
             patch('app.routes.auth.AuthService') as mock_auth_service:
            
            mock_auth_service.return_value.update_user_profile.return_value = {
                'success': True,
                'message': 'Profile updated successfully'
            }
            
            response = client.put('/api/auth/profile',
                                data=json.dumps(update_data),
                                content_type='application/json',
                                headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True


class TestBotRoutes:
    """Test cases for bot management routes."""
    
    def test_create_bot_success(self, client, auth_headers, test_user):
        """Test successful bot creation."""
        bot_data = {
            'name': 'Test Bot',
            'strategy': 'scalping',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'initial_balance': '1000.00'
        }
        
        with patch('app.routes.bots.get_current_user', return_value=test_user), \
             patch('app.routes.bots.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.create_bot.return_value = {
                'success': True,
                'message': 'Bot created successfully',
                'bot': {'id': 1, 'name': 'Test Bot'}
            }
            
            response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_get_bots_list(self, client, auth_headers, test_user):
        """Test getting user's bots list."""
        mock_bots = [
            {'id': 1, 'name': 'Bot 1', 'strategy': 'scalping'},
            {'id': 2, 'name': 'Bot 2', 'strategy': 'grid_trading'}
        ]
        
        with patch('app.routes.bots.get_current_user', return_value=test_user), \
             patch.object(Bot, 'query') as mock_query:
            
            mock_query.filter_by.return_value.all.return_value = [
                MagicMock(to_dict=lambda: mock_bots[0]),
                MagicMock(to_dict=lambda: mock_bots[1])
            ]
            
            response = client.get('/api/bots', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['bots']) == 2
    
    def test_get_bot_details(self, client, auth_headers, test_user, test_bot):
        """Test getting specific bot details."""
        with patch('app.routes.bots.get_current_user', return_value=test_user), \
             patch.object(Bot, 'query') as mock_query:
            
            mock_query.filter_by.return_value.first.return_value = test_bot
            
            response = client.get(f'/api/bots/{test_bot.id}', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == test_bot.id
    
    def test_start_bot(self, client, auth_headers, test_user, test_bot):
        """Test starting a bot."""
        with patch('app.routes.bots.get_current_user', return_value=test_user), \
             patch('app.routes.bots.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.start_bot.return_value = {
                'success': True,
                'message': 'Bot started successfully'
            }
            
            response = client.post(f'/api/bots/{test_bot.id}/start', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_stop_bot(self, client, auth_headers, test_user, test_bot):
        """Test stopping a bot."""
        with patch('app.routes.bots.get_current_user', return_value=test_user), \
             patch('app.routes.bots.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.stop_bot.return_value = {
                'success': True,
                'message': 'Bot stopped successfully'
            }
            
            response = client.post(f'/api/bots/{test_bot.id}/stop', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_delete_bot(self, client, auth_headers, test_user, test_bot):
        """Test deleting a bot."""
        with patch('app.routes.bots.get_current_user', return_value=test_user), \
             patch('app.routes.bots.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.delete_bot.return_value = {
                'success': True,
                'message': 'Bot deleted successfully'
            }
            
            response = client.delete(f'/api/bots/{test_bot.id}', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_bot_unauthorized_access(self, client, test_bot):
        """Test accessing bot without authentication."""
        response = client.get(f'/api/bots/{test_bot.id}')
        
        assert response.status_code == 401


class TestTradingRoutes:
    """Test cases for trading routes."""
    
    def test_execute_trade(self, client, auth_headers, test_user, test_bot):
        """Test trade execution."""
        trade_data = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': '0.001',
            'price': '50000.00',
            'trade_type': 'limit'
        }
        
        with patch('app.routes.trading.get_current_user', return_value=test_user), \
             patch('app.routes.trading.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.execute_trade.return_value = {
                'success': True,
                'message': 'Trade executed successfully',
                'trade': {'id': 1, 'symbol': 'BTCUSDT'}
            }
            
            response = client.post(f'/api/bots/{test_bot.id}/trade',
                                 data=json.dumps(trade_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_get_trade_history(self, client, auth_headers, test_user, test_bot):
        """Test getting trade history."""
        with patch('app.routes.trading.get_current_user', return_value=test_user), \
             patch('app.routes.trading.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.get_trade_history.return_value = {
                'success': True,
                'trades': [
                    {'id': 1, 'symbol': 'BTCUSDT', 'side': 'buy'},
                    {'id': 2, 'symbol': 'BTCUSDT', 'side': 'sell'}
                ]
            }
            
            response = client.get(f'/api/bots/{test_bot.id}/trades', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['trades']) == 2
    
    def test_get_market_data(self, client, auth_headers):
        """Test getting market data."""
        with patch('app.routes.trading.TradingService') as mock_trading_service:
            mock_trading_service.return_value.get_market_data.return_value = {
                'success': True,
                'data': {
                    'symbol': 'BTCUSDT',
                    'last': 50000.00,
                    'bid': 49999.00,
                    'ask': 50001.00
                }
            }
            
            response = client.get('/api/market/BTCUSDT?exchange=binance', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['symbol'] == 'BTCUSDT'


class TestAnalyticsRoutes:
    """Test cases for analytics routes."""
    
    def test_get_bot_performance(self, client, auth_headers, test_user, test_bot):
        """Test getting bot performance analytics."""
        with patch('app.routes.analytics.get_current_user', return_value=test_user), \
             patch('app.routes.analytics.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.get_bot_performance.return_value = {
                'success': True,
                'performance': {
                    'total_trades': 10,
                    'profit_loss': '150.00',
                    'win_rate': 70.0
                }
            }
            
            response = client.get(f'/api/analytics/bots/{test_bot.id}/performance', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'performance' in data
    
    def test_get_portfolio_summary(self, client, auth_headers, test_user):
        """Test getting portfolio summary."""
        with patch('app.routes.analytics.get_current_user', return_value=test_user), \
             patch('app.routes.analytics.TradingService') as mock_trading_service:
            
            mock_trading_service.return_value.get_portfolio_summary.return_value = {
                'success': True,
                'portfolio': {
                    'total_balance': '2000.00',
                    'total_profit_loss': '200.00',
                    'active_bots': 2
                }
            }
            
            response = client.get('/api/analytics/portfolio', headers=auth_headers)
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'portfolio' in data


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_500_error(self, client):
        """Test 500 error handling."""
        with patch('app.routes.auth.AuthService') as mock_auth_service:
            mock_auth_service.side_effect = Exception('Internal server error')
            
            response = client.post('/api/auth/login',
                                 data=json.dumps({'username': 'test', 'password': 'test'}),
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_validation_error(self, client):
        """Test validation error handling."""
        # Send invalid JSON
        response = client.post('/api/auth/register',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data