"""End-to-end tests for complete user workflows."""
import pytest
import time
from unittest.mock import patch, Mock
from decimal import Decimal

from models.user import User
from models.bot import Bot
from services.auth_service import AuthService


@pytest.mark.e2e
class TestUserWorkflows:
    """Test complete user workflows end-to-end."""
    
    def test_complete_user_registration_workflow(self, client, session):
        """Test complete user registration and verification workflow."""
        # Step 1: Register new user
        user_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'StrongP@ssw0rd123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        response = client.post('/api/auth/register', json=user_data)
        assert response.status_code == 201
        
        registration_data = response.get_json()
        verification_token = registration_data['verification_token']
        
        # Step 2: Verify email
        response = client.post(f'/api/auth/verify-email/{verification_token}')
        assert response.status_code == 200
        
        # Step 3: Login with verified account
        login_data = {
            'email': 'newuser@example.com',
            'password': 'StrongP@ssw0rd123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        
        login_response = response.get_json()
        access_token = login_response['access_token']
        user_id = login_response['user']['id']
        
        # Step 4: Update profile
        auth_headers = {'Authorization': f'Bearer {access_token}'}
        profile_data = {
            'timezone': 'America/New_York',
            'phone': '+1234567890'
        }
        
        response = client.put('/api/auth/profile', 
                            json=profile_data, 
                            headers=auth_headers)
        assert response.status_code == 200
        
        # Step 5: Verify complete profile
        response = client.get('/api/auth/profile', headers=auth_headers)
        assert response.status_code == 200
        
        profile = response.get_json()['user']
        assert profile['email'] == 'newuser@example.com'
        assert profile['timezone'] == 'America/New_York'
        assert profile['is_verified'] is True
    
    def test_complete_bot_trading_workflow(self, client, session, test_user):
        """Test complete bot creation and trading workflow."""
        # Step 1: Login
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        
        access_token = response.get_json()['access_token']
        auth_headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Create API key for trading
        api_key_data = {
            'name': 'Trading API Key',
            'permissions': ['read', 'trade']
        }
        
        response = client.post('/api/api-keys', 
                             json=api_key_data, 
                             headers=auth_headers)
        assert response.status_code == 201
        
        # Step 3: Create trading bot
        bot_data = {
            'name': 'E2E Test Bot',
            'strategy': 'grid_trading',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'config': {
                'grid_size': 10,
                'investment_amount': 1000,
                'grid_spacing': 0.5,
                'stop_loss': 5.0,
                'take_profit': 10.0
            }
        }
        
        response = client.post('/api/bots', 
                             json=bot_data, 
                             headers=auth_headers)
        assert response.status_code == 201
        
        bot = response.get_json()['bot']
        bot_id = bot['id']
        
        # Step 4: Start the bot
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.get_account_balance.return_value = {'USDT': 2000}
            mock_exchange.get_symbol_info.return_value = {
                'min_qty': 0.001,
                'max_qty': 1000,
                'step_size': 0.001
            }
            
            response = client.post(f'/api/bots/{bot_id}/start', 
                                 headers=auth_headers)
            assert response.status_code == 200
        
        # Step 5: Simulate some trading activity
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.place_order.return_value = {
                'order_id': 'test_order_123',
                'status': 'filled',
                'filled_qty': 0.001,
                'avg_price': 50000
            }
            
            # Execute a trade
            trade_data = {
                'symbol': 'BTCUSDT',
                'side': 'buy',
                'quantity': 0.001,
                'order_type': 'market'
            }
            
            response = client.post(f'/api/bots/{bot_id}/trades', 
                                 json=trade_data, 
                                 headers=auth_headers)
            assert response.status_code == 201
        
        # Step 6: Check bot performance
        response = client.get(f'/api/bots/{bot_id}/performance', 
                            headers=auth_headers)
        assert response.status_code == 200
        
        performance = response.get_json()['performance']
        assert 'total_trades' in performance
        
        # Step 7: Get trade history
        response = client.get(f'/api/bots/{bot_id}/trades', 
                            headers=auth_headers)
        assert response.status_code == 200
        
        trades = response.get_json()['trades']
        assert len(trades) >= 1
        
        # Step 8: Stop the bot
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.cancel_all_orders.return_value = True
            
            response = client.post(f'/api/bots/{bot_id}/stop', 
                                 headers=auth_headers)
            assert response.status_code == 200
        
        # Step 9: Verify bot is stopped
        response = client.get(f'/api/bots/{bot_id}', headers=auth_headers)
        assert response.status_code == 200
        
        bot_status = response.get_json()['bot']
        assert bot_status['status'] == 'stopped'
    
    def test_subscription_upgrade_workflow(self, client, session, test_user):
        """Test subscription upgrade workflow."""
        # Step 1: Login
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        access_token = response.get_json()['access_token']
        auth_headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Check current subscription
        response = client.get('/api/subscriptions/current', headers=auth_headers)
        assert response.status_code == 200
        
        current_sub = response.get_json()['subscription']
        assert current_sub['plan'] == 'free'  # Default plan
        
        # Step 3: Get available plans
        response = client.get('/api/subscriptions/plans', headers=auth_headers)
        assert response.status_code == 200
        
        plans = response.get_json()['plans']
        premium_plan = next(plan for plan in plans if plan['name'] == 'premium')
        
        # Step 4: Upgrade to premium
        with patch('services.stripe_service.create_checkout_session') as mock_stripe:
            mock_stripe.return_value = {
                'id': 'cs_test_123',
                'url': 'https://checkout.stripe.com/pay/cs_test_123'
            }
            
            upgrade_data = {
                'plan': 'premium',
                'billing_cycle': 'monthly'
            }
            
            response = client.post('/api/subscriptions/upgrade', 
                                 json=upgrade_data, 
                                 headers=auth_headers)
            assert response.status_code == 200
            
            checkout_data = response.get_json()
            assert 'checkout_url' in checkout_data
        
        # Step 5: Simulate successful payment (webhook)
        with patch('services.stripe_service.verify_webhook') as mock_verify:
            mock_verify.return_value = True
            
            webhook_data = {
                'type': 'checkout.session.completed',
                'data': {
                    'object': {
                        'id': 'cs_test_123',
                        'customer': 'cus_test_123',
                        'subscription': 'sub_test_123',
                        'metadata': {
                            'user_id': str(test_user.id),
                            'plan': 'premium'
                        }
                    }
                }
            }
            
            response = client.post('/api/webhooks/stripe', 
                                 json=webhook_data,
                                 headers={'Stripe-Signature': 'test_signature'})
            assert response.status_code == 200
        
        # Step 6: Verify subscription upgrade
        response = client.get('/api/subscriptions/current', headers=auth_headers)
        assert response.status_code == 200
        
        updated_sub = response.get_json()['subscription']
        assert updated_sub['plan'] == 'premium'
        assert updated_sub['status'] == 'active'
    
    def test_password_reset_workflow(self, client, session):
        """Test complete password reset workflow."""
        # Step 1: Create user
        user = User(
            email='reset@example.com',
            username='resetuser',
            password_hash=AuthService.hash_password('oldpassword123'),
            is_verified=True
        )
        session.add(user)
        session.commit()
        
        # Step 2: Request password reset
        with patch('services.email_service.send_password_reset_email') as mock_email:
            mock_email.return_value = True
            
            reset_request = {'email': 'reset@example.com'}
            response = client.post('/api/auth/forgot-password', json=reset_request)
            assert response.status_code == 200
            
            # Verify email was sent
            assert mock_email.called
        
        # Step 3: Generate reset token (simulate email link)
        reset_token = AuthService.generate_password_reset_token(user)
        
        # Step 4: Reset password with token
        reset_data = {
            'token': reset_token,
            'new_password': 'NewStrongP@ssw0rd456'
        }
        
        response = client.post('/api/auth/reset-password', json=reset_data)
        assert response.status_code == 200
        
        # Step 5: Login with new password
        login_data = {
            'email': 'reset@example.com',
            'password': 'NewStrongP@ssw0rd456'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        
        # Step 6: Verify old password doesn't work
        old_login_data = {
            'email': 'reset@example.com',
            'password': 'oldpassword123'
        }
        
        response = client.post('/api/auth/login', json=old_login_data)
        assert response.status_code == 401
    
    def test_two_factor_authentication_workflow(self, client, session, test_user):
        """Test 2FA setup and login workflow."""
        # Step 1: Login
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        access_token = response.get_json()['access_token']
        auth_headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Enable 2FA
        with patch('services.auth_service.pyotp.random_base32') as mock_secret:
            mock_secret.return_value = 'TESTSECRET123456'
            
            response = client.post('/api/auth/enable-2fa', headers=auth_headers)
            assert response.status_code == 200
            
            setup_data = response.get_json()
            assert 'secret' in setup_data
            assert 'qr_code' in setup_data
        
        # Step 3: Verify 2FA setup
        with patch('services.auth_service.pyotp.TOTP') as mock_totp:
            mock_totp_instance = Mock()
            mock_totp.return_value = mock_totp_instance
            mock_totp_instance.verify.return_value = True
            
            verify_data = {'code': '123456'}
            response = client.post('/api/auth/verify-2fa', 
                                 json=verify_data, 
                                 headers=auth_headers)
            assert response.status_code == 200
        
        # Step 4: Logout
        response = client.post('/api/auth/logout', headers=auth_headers)
        assert response.status_code == 200
        
        # Step 5: Login with 2FA
        with patch('services.auth_service.pyotp.TOTP') as mock_totp:
            mock_totp_instance = Mock()
            mock_totp.return_value = mock_totp_instance
            mock_totp_instance.verify.return_value = True
            
            # First login step (username/password)
            response = client.post('/api/auth/login', json=login_data)
            assert response.status_code == 200
            
            login_response = response.get_json()
            assert login_response.get('requires_2fa') is True
            temp_token = login_response['temp_token']
            
            # Second login step (2FA code)
            twofa_data = {
                'temp_token': temp_token,
                'code': '123456'
            }
            
            response = client.post('/api/auth/verify-2fa-login', json=twofa_data)
            assert response.status_code == 200
            
            final_login = response.get_json()
            assert 'access_token' in final_login
    
    def test_api_key_management_workflow(self, client, session, test_user):
        """Test API key creation and usage workflow."""
        # Step 1: Login
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        access_token = response.get_json()['access_token']
        auth_headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Create API key
        api_key_data = {
            'name': 'Test API Key',
            'permissions': ['read', 'trade'],
            'expires_at': '2024-12-31T23:59:59Z'
        }
        
        response = client.post('/api/api-keys', 
                             json=api_key_data, 
                             headers=auth_headers)
        assert response.status_code == 201
        
        api_key_response = response.get_json()
        api_key_value = api_key_response['api_key']['key']
        api_key_id = api_key_response['api_key']['id']
        
        # Step 3: Use API key for authentication
        api_headers = {'X-API-Key': api_key_value}
        
        response = client.get('/api/auth/profile', headers=api_headers)
        assert response.status_code == 200
        
        profile = response.get_json()['user']
        assert profile['id'] == test_user.id
        
        # Step 4: List API keys
        response = client.get('/api/api-keys', headers=auth_headers)
        assert response.status_code == 200
        
        api_keys = response.get_json()['api_keys']
        assert len(api_keys) >= 1
        assert any(key['id'] == api_key_id for key in api_keys)
        
        # Step 5: Update API key permissions
        update_data = {
            'permissions': ['read']  # Remove trade permission
        }
        
        response = client.put(f'/api/api-keys/{api_key_id}', 
                            json=update_data, 
                            headers=auth_headers)
        assert response.status_code == 200
        
        # Step 6: Test restricted permissions
        # This would fail if trying to perform trade operations
        
        # Step 7: Deactivate API key
        response = client.delete(f'/api/api-keys/{api_key_id}', 
                               headers=auth_headers)
        assert response.status_code == 200
        
        # Step 8: Verify API key no longer works
        response = client.get('/api/auth/profile', headers=api_headers)
        assert response.status_code == 401
    
    def test_error_handling_and_recovery_workflow(self, client, session, test_user):
        """Test error handling and recovery scenarios."""
        # Step 1: Login
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        access_token = response.get_json()['access_token']
        auth_headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Create bot
        bot_data = {
            'name': 'Error Test Bot',
            'strategy': 'grid_trading',
            'exchange': 'binance',
            'symbol': 'BTCUSDT',
            'config': {
                'grid_size': 10,
                'investment_amount': 1000
            }
        }
        
        response = client.post('/api/bots', 
                             json=bot_data, 
                             headers=auth_headers)
        bot_id = response.get_json()['bot']['id']
        
        # Step 3: Simulate exchange API error during bot start
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.get_account_balance.side_effect = Exception("API Error")
            
            response = client.post(f'/api/bots/{bot_id}/start', 
                                 headers=auth_headers)
            assert response.status_code == 500
            
            error_data = response.get_json()
            assert 'error' in error_data
        
        # Step 4: Check bot status after error
        response = client.get(f'/api/bots/{bot_id}', headers=auth_headers)
        bot_status = response.get_json()['bot']
        assert bot_status['status'] == 'error'
        
        # Step 5: Retry bot start after fixing issue
        with patch('services.trading_service.ExchangeAPI') as mock_api:
            mock_exchange = Mock()
            mock_api.return_value = mock_exchange
            mock_exchange.get_account_balance.return_value = {'USDT': 2000}
            mock_exchange.get_symbol_info.return_value = {
                'min_qty': 0.001,
                'max_qty': 1000,
                'step_size': 0.001
            }
            
            response = client.post(f'/api/bots/{bot_id}/start', 
                                 headers=auth_headers)
            assert response.status_code == 200
        
        # Step 6: Verify bot recovered
        response = client.get(f'/api/bots/{bot_id}', headers=auth_headers)
        bot_status = response.get_json()['bot']
        assert bot_status['status'] == 'running'
    
    def test_concurrent_user_operations(self, client, session):
        """Test concurrent operations by multiple users."""
        # Create multiple users
        users = []
        for i in range(3):
            user_data = {
                'email': f'concurrent{i}@example.com',
                'username': f'concurrent{i}',
                'password': 'StrongP@ssw0rd123'
            }
            
            response = client.post('/api/auth/register', json=user_data)
            assert response.status_code == 201
            
            # Verify and login
            verification_token = response.get_json()['verification_token']
            client.post(f'/api/auth/verify-email/{verification_token}')
            
            login_response = client.post('/api/auth/login', json={
                'email': user_data['email'],
                'password': user_data['password']
            })
            
            access_token = login_response.get_json()['access_token']
            users.append({
                'email': user_data['email'],
                'token': access_token,
                'headers': {'Authorization': f'Bearer {access_token}'}
            })
        
        # Simulate concurrent bot creation
        bot_ids = []
        for i, user in enumerate(users):
            bot_data = {
                'name': f'Concurrent Bot {i}',
                'strategy': 'grid_trading',
                'exchange': 'binance',
                'symbol': 'BTCUSDT',
                'config': {'grid_size': 10 + i}
            }
            
            response = client.post('/api/bots', 
                                 json=bot_data, 
                                 headers=user['headers'])
            assert response.status_code == 201
            
            bot_ids.append(response.get_json()['bot']['id'])
        
        # Verify each user can only see their own bots
        for i, user in enumerate(users):
            response = client.get('/api/bots', headers=user['headers'])
            assert response.status_code == 200
            
            user_bots = response.get_json()['bots']
            assert len(user_bots) == 1
            assert user_bots[0]['name'] == f'Concurrent Bot {i}'
            
            # Verify user cannot access other users' bots
            other_bot_id = bot_ids[(i + 1) % len(bot_ids)]
            response = client.get(f'/api/bots/{other_bot_id}', 
                                headers=user['headers'])
            assert response.status_code == 403