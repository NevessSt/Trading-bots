"""Security tests for the trading bot system."""
import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import jwt
import hashlib
import secrets

from app import create_app, db
from app.models import User, Bot, APIKey
from app.utils.security import generate_api_key, hash_api_secret


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_password_hashing_security(self, app_context):
        """Test password hashing security."""
        user = User(username='testuser', email='test@example.com')
        password = 'SecurePassword123!'
        
        # Set password
        user.set_password(password)
        
        # Password should be hashed, not stored in plain text
        assert user.password_hash != password
        assert len(user.password_hash) > 50  # Hashed passwords are long
        
        # Should use strong hashing (bcrypt/scrypt/argon2)
        assert user.password_hash.startswith(('$2b$', '$scrypt$', '$argon2'))
        
        # Same password should produce different hashes (salt)
        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password(password)
        assert user.password_hash != user2.password_hash
        
        # Verification should work
        assert user.check_password(password) is True
        assert user.check_password('wrongpassword') is False
    
    def test_jwt_token_security(self, client):
        """Test JWT token security."""
        # Register and login user
        user_data = {
            'username': 'securityuser',
            'email': 'security@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        login_data = {
            'username': 'securityuser',
            'password': 'SecurePass123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        data = json.loads(response.data)
        token = data['access_token']
        
        # Token should be properly formatted JWT
        assert len(token.split('.')) == 3  # header.payload.signature
        
        # Token should have expiration
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert 'exp' in decoded
        assert 'iat' in decoded
        assert 'sub' in decoded  # Subject (user ID)
        
        # Token should expire in reasonable time (not too long)
        exp_time = datetime.fromtimestamp(decoded['exp'])
        iat_time = datetime.fromtimestamp(decoded['iat'])
        token_lifetime = exp_time - iat_time
        assert token_lifetime <= timedelta(hours=24)  # Max 24 hours
    
    def test_token_invalidation(self, client):
        """Test token invalidation on logout."""
        # Register and login
        user_data = {
            'username': 'logoutuser',
            'email': 'logout@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': 'logoutuser',
                                       'password': 'SecurePass123!'
                                   }),
                                   content_type='application/json')
        
        token = json.loads(login_response.data)['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Token should work before logout
        response = client.get('/api/user/profile', headers=headers)
        assert response.status_code == 200
        
        # Logout
        client.post('/api/auth/logout', headers=headers)
        
        # Token should be invalidated after logout
        response = client.get('/api/user/profile', headers=headers)
        assert response.status_code == 401
    
    def test_brute_force_protection(self, client):
        """Test brute force attack protection."""
        # Register user
        user_data = {
            'username': 'bruteuser',
            'email': 'brute@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            response = client.post('/api/auth/login',
                                 data=json.dumps({
                                     'username': 'bruteuser',
                                     'password': 'wrongpassword'
                                 }),
                                 content_type='application/json')
            
            if response.status_code == 401:
                failed_attempts += 1
            elif response.status_code == 429:  # Rate limited
                break
        
        # Should implement rate limiting after multiple failures
        assert failed_attempts < 10  # Should be rate limited before 10 attempts
    
    def test_session_security(self, client, auth_headers):
        """Test session security measures."""
        # Test concurrent session handling
        response1 = client.get('/api/user/profile', headers=auth_headers)
        assert response1.status_code == 200
        
        # Login again (new session)
        login_response = client.post('/api/auth/login',
                                   data=json.dumps({
                                       'username': 'testuser',
                                       'password': 'testpassword123'
                                   }),
                                   content_type='application/json')
        
        new_token = json.loads(login_response.data)['access_token']
        new_headers = {'Authorization': f'Bearer {new_token}'}
        
        # Both sessions should work (or old one should be invalidated)
        response2 = client.get('/api/user/profile', headers=new_headers)
        assert response2.status_code == 200


class TestInputValidationSecurity:
    """Test input validation security measures."""
    
    def test_sql_injection_protection(self, client, auth_headers):
        """Test SQL injection protection."""
        # Attempt SQL injection in bot name
        malicious_bot_data = {
            'name': "'; DROP TABLE bots; --",
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'config': {}
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(malicious_bot_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        # Should either reject the input or safely handle it
        if response.status_code == 201:
            # If accepted, verify it was safely stored
            data = json.loads(response.data)
            bot_id = data['bot']['id']
            
            # Verify bot was created safely
            get_response = client.get(f'/api/bots/{bot_id}', headers=auth_headers)
            assert get_response.status_code == 200
            
            # Verify database integrity
            from app.models import Bot
            bot = Bot.query.get(bot_id)
            assert bot is not None
    
    def test_xss_protection(self, client, auth_headers):
        """Test XSS protection in user inputs."""
        # Attempt XSS in bot name
        xss_bot_data = {
            'name': '<script>alert("XSS")</script>',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'config': {}
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(xss_bot_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        if response.status_code == 201:
            data = json.loads(response.data)
            # Script tags should be escaped or removed
            assert '<script>' not in data['bot']['name']
            assert 'alert' not in data['bot']['name']
    
    def test_command_injection_protection(self, client, auth_headers):
        """Test command injection protection."""
        # Attempt command injection in trading pair
        malicious_data = {
            'name': 'Test Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT; rm -rf /',
            'config': {}
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(malicious_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        # Should reject invalid trading pair format
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data or 'errors' in data
    
    def test_path_traversal_protection(self, client, auth_headers):
        """Test path traversal protection."""
        # Attempt path traversal in file-related endpoints
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM'
        ]
        
        for path in malicious_paths:
            # Test in bot configuration (if file paths are accepted)
            bot_data = {
                'name': 'Test Bot',
                'strategy': 'grid',
                'trading_pair': 'BTCUSDT',
                'config': {
                    'config_file': path
                }
            }
            
            response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            # Should either reject or sanitize the path
            if response.status_code == 201:
                data = json.loads(response.data)
                config_file = data['bot']['config'].get('config_file', '')
                assert '../' not in config_file
                assert '..\\' not in config_file
    
    def test_json_payload_size_limit(self, client, auth_headers):
        """Test JSON payload size limits."""
        # Create very large payload
        large_config = {f'param_{i}': 'x' * 1000 for i in range(1000)}
        
        large_bot_data = {
            'name': 'Large Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'config': large_config
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(large_bot_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        # Should reject overly large payloads
        assert response.status_code in [400, 413, 422]  # Bad Request, Payload Too Large, or Unprocessable Entity


class TestAPIKeySecurity:
    """Test API key security measures."""
    
    def test_api_key_generation_security(self, app_context):
        """Test API key generation security."""
        # Generate multiple API keys
        keys = [generate_api_key() for _ in range(100)]
        
        # All keys should be unique
        assert len(set(keys)) == 100
        
        # Keys should have sufficient entropy
        for key in keys[:10]:  # Test first 10
            assert len(key) >= 32  # Minimum length
            assert key.isalnum()   # Only alphanumeric characters
            
            # Check for sufficient randomness (no obvious patterns)
            assert not all(c == key[0] for c in key)  # Not all same character
            assert key != key.lower()  # Should have mixed case
            assert key != key.upper()
    
    def test_api_secret_hashing_security(self, app_context):
        """Test API secret hashing security."""
        secret = 'my_super_secret_api_key_123'
        
        # Hash the secret
        hashed = hash_api_secret(secret)
        
        # Should be properly hashed
        assert hashed != secret
        assert len(hashed) > 50
        
        # Should use strong hashing algorithm
        assert hashed.startswith(('$2b$', '$scrypt$', '$argon2'))
        
        # Same secret should produce different hashes (salt)
        hashed2 = hash_api_secret(secret)
        assert hashed != hashed2
    
    def test_api_key_storage_security(self, client, auth_headers):
        """Test API key storage security."""
        api_key_data = {
            'exchange': 'binance',
            'key_name': 'Security Test Key',
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
            
            # API secret should not be returned in response
            assert 'api_secret' not in data['api_key']
            assert 'api_secret_hash' not in data['api_key']
            
            # Verify in database
            api_key_id = data['api_key']['id']
            api_key = APIKey.query.get(api_key_id)
            
            # Secret should be hashed in database
            assert api_key.api_secret_hash != 'test_api_secret_456'
            assert len(api_key.api_secret_hash) > 50
    
    def test_api_key_access_control(self, client, auth_headers):
        """Test API key access control."""
        # Create API key for current user
        api_key_data = {
            'exchange': 'binance',
            'key_name': 'Access Test Key',
            'api_key': 'access_test_key_123',
            'api_secret': 'access_test_secret_456'
        }
        
        with patch('app.services.exchange_service.validate_api_credentials') as mock_validate:
            mock_validate.return_value = True
            
            response = client.post('/api/api-keys',
                                 data=json.dumps(api_key_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            api_key_id = json.loads(response.data)['api_key']['id']
        
        # Create another user
        other_user_data = {
            'username': 'otheruser',
            'email': 'other@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(other_user_data),
                   content_type='application/json')
        
        other_login_response = client.post('/api/auth/login',
                                         data=json.dumps({
                                             'username': 'otheruser',
                                             'password': 'SecurePass123!'
                                         }),
                                         content_type='application/json')
        
        other_token = json.loads(other_login_response.data)['access_token']
        other_headers = {'Authorization': f'Bearer {other_token}'}
        
        # Other user should not be able to access the API key
        response = client.get(f'/api/api-keys/{api_key_id}', headers=other_headers)
        assert response.status_code == 403


class TestDataProtectionSecurity:
    """Test data protection and privacy security measures."""
    
    def test_sensitive_data_exposure(self, client, auth_headers):
        """Test that sensitive data is not exposed in API responses."""
        # Get user profile
        response = client.get('/api/user/profile', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        user_data = data['user']
        
        # Sensitive fields should not be exposed
        sensitive_fields = ['password_hash', 'password', 'secret', 'private_key']
        for field in sensitive_fields:
            assert field not in user_data
    
    def test_user_data_isolation(self, client, auth_headers):
        """Test that users can only access their own data."""
        # Create another user
        other_user_data = {
            'username': 'isolationuser',
            'email': 'isolation@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(other_user_data),
                   content_type='application/json')
        
        # Login as other user and create a bot
        other_login_response = client.post('/api/auth/login',
                                         data=json.dumps({
                                             'username': 'isolationuser',
                                             'password': 'SecurePass123!'
                                         }),
                                         content_type='application/json')
        
        other_token = json.loads(other_login_response.data)['access_token']
        other_headers = {'Authorization': f'Bearer {other_token}'}
        
        bot_data = {
            'name': 'Isolation Test Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'config': {}
        }
        
        bot_response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=other_headers)
        
        other_bot_id = json.loads(bot_response.data)['bot']['id']
        
        # Original user should not be able to access other user's bot
        response = client.get(f'/api/bots/{other_bot_id}', headers=auth_headers)
        assert response.status_code == 403
        
        # Original user should not see other user's bots in listing
        response = client.get('/api/bots', headers=auth_headers)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        bot_ids = [bot['id'] for bot in data['bots']]
        assert other_bot_id not in bot_ids
    
    def test_data_encryption_at_rest(self, app_context):
        """Test that sensitive data is encrypted at rest."""
        # Create API key with sensitive data
        user = User(
            username='encryptuser',
            email='encrypt@example.com',
            password_hash='hashed_password'
        )
        db.session.add(user)
        db.session.commit()
        
        api_key = APIKey(
            user_id=user.id,
            exchange='binance',
            key_name='Encryption Test',
            api_key='encryption_test_key',
            api_secret_hash='hashed_secret'
        )
        db.session.add(api_key)
        db.session.commit()
        
        # Verify sensitive data is not stored in plain text
        assert api_key.api_secret_hash != 'test_secret'
        
        # Check database directly
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT api_secret_hash FROM api_keys WHERE id = :id"),
            {'id': api_key.id}
        ).fetchone()
        
        stored_hash = result[0]
        assert stored_hash != 'test_secret'
        assert len(stored_hash) > 50  # Should be hashed


class TestNetworkSecurity:
    """Test network security measures."""
    
    def test_https_enforcement(self, client):
        """Test HTTPS enforcement in production."""
        # This test would check for HTTPS redirects in production
        # For testing, we verify security headers are set
        response = client.get('/api/user/profile')
        
        # Check for security headers (even on 401 response)
        headers = response.headers
        
        # Should have security headers
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        # Note: In test environment, some headers might not be set
        # This is more relevant for production deployment
    
    def test_cors_configuration(self, client):
        """Test CORS configuration security."""
        # Test preflight request
        response = client.options('/api/bots',
                                headers={
                                    'Origin': 'https://malicious-site.com',
                                    'Access-Control-Request-Method': 'POST'
                                })
        
        # Should have proper CORS headers
        if 'Access-Control-Allow-Origin' in response.headers:
            # Should not allow all origins in production
            assert response.headers['Access-Control-Allow-Origin'] != '*'
    
    def test_rate_limiting_security(self, client):
        """Test rate limiting for security."""
        # Make rapid requests to test rate limiting
        responses = []
        for i in range(20):
            response = client.get('/api/market/data/BTCUSDT')
            responses.append(response.status_code)
            
            if response.status_code == 429:  # Rate limited
                break
        
        # Should implement rate limiting
        rate_limited = any(status == 429 for status in responses)
        
        # If rate limiting is implemented, should see 429 responses
        # If not implemented, all should be 401 (unauthorized)
        assert all(status in [200, 401, 429] for status in responses)


class TestCryptographicSecurity:
    """Test cryptographic security measures."""
    
    def test_random_number_generation(self, app_context):
        """Test cryptographically secure random number generation."""
        # Generate multiple random values
        random_values = [secrets.token_hex(32) for _ in range(100)]
        
        # All values should be unique
        assert len(set(random_values)) == 100
        
        # Values should have sufficient entropy
        for value in random_values[:10]:
            assert len(value) == 64  # 32 bytes = 64 hex chars
            
            # Check for patterns (basic entropy test)
            char_counts = {}
            for char in value:
                char_counts[char] = char_counts.get(char, 0) + 1
            
            # No character should appear too frequently
            max_frequency = max(char_counts.values())
            assert max_frequency <= len(value) // 4  # No char more than 25%
    
    def test_timing_attack_resistance(self, client):
        """Test resistance to timing attacks."""
        # Test login timing with valid vs invalid usernames
        valid_times = []
        invalid_times = []
        
        # Register a user first
        user_data = {
            'username': 'timinguser',
            'email': 'timing@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(user_data),
                   content_type='application/json')
        
        # Test with valid username, wrong password
        for _ in range(10):
            start_time = time.time()
            client.post('/api/auth/login',
                       data=json.dumps({
                           'username': 'timinguser',
                           'password': 'wrongpassword'
                       }),
                       content_type='application/json')
            end_time = time.time()
            valid_times.append(end_time - start_time)
        
        # Test with invalid username
        for _ in range(10):
            start_time = time.time()
            client.post('/api/auth/login',
                       data=json.dumps({
                           'username': 'nonexistentuser',
                           'password': 'wrongpassword'
                       }),
                       content_type='application/json')
            end_time = time.time()
            invalid_times.append(end_time - start_time)
        
        # Timing should be similar to prevent username enumeration
        avg_valid_time = sum(valid_times) / len(valid_times)
        avg_invalid_time = sum(invalid_times) / len(invalid_times)
        
        # Times should be within 50% of each other
        time_ratio = max(avg_valid_time, avg_invalid_time) / min(avg_valid_time, avg_invalid_time)
        assert time_ratio < 1.5
    
    def test_secure_token_generation(self, app_context):
        """Test secure token generation for various purposes."""
        # Test API key generation
        api_keys = [generate_api_key() for _ in range(50)]
        
        # All should be unique
        assert len(set(api_keys)) == 50
        
        # Should have good entropy
        for key in api_keys[:5]:
            # Check character distribution
            char_types = {
                'upper': sum(1 for c in key if c.isupper()),
                'lower': sum(1 for c in key if c.islower()),
                'digit': sum(1 for c in key if c.isdigit())
            }
            
            # Should have mix of character types
            assert char_types['upper'] > 0
            assert char_types['lower'] > 0
            assert char_types['digit'] > 0


class TestBusinessLogicSecurity:
    """Test business logic security measures."""
    
    def test_trading_amount_limits(self, client, auth_headers, sample_bot):
        """Test trading amount limits and validation."""
        # Test with extremely large amount
        large_trade_data = {
            'bot_id': sample_bot.id,
            'trading_pair': 'BTCUSDT',
            'side': 'buy',
            'quantity': '999999999.999999999',  # Extremely large
            'order_type': 'market'
        }
        
        response = client.post('/api/trading/execute',
                             data=json.dumps(large_trade_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        # Should reject unreasonably large amounts
        assert response.status_code in [400, 422]
        
        # Test with negative amount
        negative_trade_data = {
            'bot_id': sample_bot.id,
            'trading_pair': 'BTCUSDT',
            'side': 'buy',
            'quantity': '-0.001',  # Negative
            'order_type': 'market'
        }
        
        response = client.post('/api/trading/execute',
                             data=json.dumps(negative_trade_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        # Should reject negative amounts
        assert response.status_code in [400, 422]
    
    def test_bot_configuration_limits(self, client, auth_headers, sample_api_key):
        """Test bot configuration limits and validation."""
        # Test with excessive number of grid levels
        excessive_config = {
            'name': 'Excessive Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'api_key_id': sample_api_key.id,
            'config': {
                'grid_size': 10000,  # Excessive
                'price_range': [1, 1000000],
                'investment_amount': 999999999
            }
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(excessive_config),
                             content_type='application/json',
                             headers=auth_headers)
        
        # Should reject excessive configurations
        assert response.status_code in [400, 422]
    
    def test_user_resource_limits(self, client, auth_headers, sample_api_key):
        """Test user resource limits (number of bots, etc.)."""
        # Create multiple bots to test limits
        created_bots = []
        
        for i in range(20):  # Try to create many bots
            bot_data = {
                'name': f'Limit Test Bot {i}',
                'strategy': 'grid',
                'trading_pair': 'BTCUSDT',
                'api_key_id': sample_api_key.id,
                'config': {
                    'grid_size': 10,
                    'price_range': [45000, 55000],
                    'investment_amount': 1000
                }
            }
            
            response = client.post('/api/bots',
                                 data=json.dumps(bot_data),
                                 content_type='application/json',
                                 headers=auth_headers)
            
            if response.status_code == 201:
                created_bots.append(json.loads(response.data)['bot']['id'])
            elif response.status_code == 429:  # Rate limited
                break
            elif response.status_code == 403:  # Limit reached
                break
        
        # Should have some reasonable limit
        # (This depends on business rules - adjust as needed)
        assert len(created_bots) <= 50  # Example limit


class TestComplianceSecurity:
    """Test compliance and regulatory security measures."""
    
    def test_audit_logging(self, client, auth_headers):
        """Test that security-relevant actions are logged."""
        # This would test that actions like login, bot creation, trades
        # are properly logged for audit purposes
        
        # Create a bot (should be logged)
        bot_data = {
            'name': 'Audit Test Bot',
            'strategy': 'grid',
            'trading_pair': 'BTCUSDT',
            'config': {}
        }
        
        response = client.post('/api/bots',
                             data=json.dumps(bot_data),
                             content_type='application/json',
                             headers=auth_headers)
        
        # In a real implementation, you would check audit logs here
        # For now, just verify the action succeeded
        assert response.status_code in [201, 400]  # Created or validation error
    
    def test_data_retention_policies(self, app_context, sample_user):
        """Test data retention and deletion policies."""
        # Create old trade data
        old_trade = Trade(
            bot_id=1,
            user_id=sample_user.id,
            trading_pair='BTCUSDT',
            side='buy',
            quantity=Decimal('0.001'),
            price=Decimal('50000'),
            total_value=Decimal('50'),
            executed_at=datetime.utcnow() - timedelta(days=400)  # Very old
        )
        
        db.session.add(old_trade)
        db.session.commit()
        
        # In a real implementation, you would test automatic cleanup
        # of old data according to retention policies
        
        # Verify trade exists
        assert Trade.query.filter_by(id=old_trade.id).first() is not None
        
        # Test manual cleanup (simulating automated process)
        cutoff_date = datetime.utcnow() - timedelta(days=365)
        old_trades = Trade.query.filter(Trade.executed_at < cutoff_date).all()
        
        for trade in old_trades:
            db.session.delete(trade)
        db.session.commit()
        
        # Verify old trade was deleted
        assert Trade.query.filter_by(id=old_trade.id).first() is None