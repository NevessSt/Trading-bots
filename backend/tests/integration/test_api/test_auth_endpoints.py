"""Integration tests for authentication API endpoints."""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch

from models.user import User
from services.auth_service import AuthService


@pytest.mark.integration
@pytest.mark.api
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_register_success(self, client, session):
        """Test successful user registration."""
        user_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'StrongP@ssw0rd123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['email'] == 'newuser@example.com'
        assert data['user']['username'] == 'newuser'
        assert 'verification_token' in data
        
        # Verify user was created in database
        user = session.query(User).filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.is_verified is False
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            'email': test_user.email,
            'username': 'different',
            'password': 'StrongP@ssw0rd123'
        }
        
        response = client.post('/api/auth/register', json=user_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Email already exists' in data['message']
    
    def test_register_invalid_data(self, client):
        """Test registration with invalid data."""
        # Missing required fields
        response = client.post('/api/auth/register', json={})
        assert response.status_code == 400
        
        # Invalid email
        user_data = {
            'email': 'invalid-email',
            'username': 'user',
            'password': 'StrongP@ssw0rd123'
        }
        response = client.post('/api/auth/register', json=user_data)
        assert response.status_code == 400
        
        # Weak password
        user_data = {
            'email': 'user@example.com',
            'username': 'user',
            'password': '123'
        }
        response = client.post('/api/auth/register', json=user_data)
        assert response.status_code == 400
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data
        assert data['user']['id'] == test_user.id
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        # Wrong password
        login_data = {
            'email': test_user.email,
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid credentials' in data['message']
        
        # Non-existent user
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 401
    
    def test_login_unverified_user(self, client, unverified_user):
        """Test login with unverified user."""
        login_data = {
            'email': unverified_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert 'Email not verified' in data['message']
    
    def test_login_locked_user(self, client, session):
        """Test login with locked user."""
        # Create locked user
        locked_user = User(
            email='locked@example.com',
            username='locked',
            password_hash=AuthService.hash_password('password123'),
            is_verified=True,
            failed_login_attempts=5,
            locked_until=datetime.utcnow() + timedelta(minutes=30)
        )
        session.add(locked_user)
        session.commit()
        
        login_data = {
            'email': locked_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 423
        data = response.get_json()
        assert data['success'] is False
        assert 'Account locked' in data['message']
    
    def test_refresh_token(self, client, test_user):
        """Test token refresh."""
        # First login to get refresh token
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        login_response = client.post('/api/auth/login', json=login_data)
        login_data = login_response.get_json()
        refresh_token = login_data['refresh_token']
        
        # Use refresh token to get new access token
        refresh_data = {'refresh_token': refresh_token}
        response = client.post('/api/auth/refresh', json=refresh_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        refresh_data = {'refresh_token': 'invalid_token'}
        response = client.post('/api/auth/refresh', json=refresh_data)
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_logout(self, client, auth_headers):
        """Test user logout."""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Logged out successfully'
    
    def test_logout_without_auth(self, client):
        """Test logout without authentication."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401
    
    def test_verify_email(self, client, session, unverified_user):
        """Test email verification."""
        # Generate verification token
        token = AuthService.generate_email_verification_token(unverified_user)
        
        response = client.post(f'/api/auth/verify-email/{token}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Email verified successfully'
        
        # Check user is now verified
        session.refresh(unverified_user)
        assert unverified_user.is_verified is True
    
    def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token."""
        response = client.post('/api/auth/verify-email/invalid_token')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_resend_verification(self, client, unverified_user):
        """Test resending verification email."""
        with patch('services.email_service.send_verification_email') as mock_send:
            mock_send.return_value = True
            
            data = {'email': unverified_user.email}
            response = client.post('/api/auth/resend-verification', json=data)
            
            assert response.status_code == 200
            response_data = response.get_json()
            assert response_data['success'] is True
            assert mock_send.called
    
    def test_forgot_password(self, client, test_user):
        """Test forgot password request."""
        with patch('services.email_service.send_password_reset_email') as mock_send:
            mock_send.return_value = True
            
            data = {'email': test_user.email}
            response = client.post('/api/auth/forgot-password', json=data)
            
            assert response.status_code == 200
            response_data = response.get_json()
            assert response_data['success'] is True
            assert mock_send.called
    
    def test_forgot_password_nonexistent_user(self, client):
        """Test forgot password for non-existent user."""
        data = {'email': 'nonexistent@example.com'}
        response = client.post('/api/auth/forgot-password', json=data)
        
        # Should return success for security reasons
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['success'] is True
    
    def test_reset_password(self, client, session, test_user):
        """Test password reset."""
        # Generate reset token
        token = AuthService.generate_password_reset_token(test_user)
        
        reset_data = {
            'token': token,
            'new_password': 'NewStrongP@ssw0rd456'
        }
        
        response = client.post('/api/auth/reset-password', json=reset_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify password was changed
        session.refresh(test_user)
        assert test_user.check_password('NewStrongP@ssw0rd456') is True
        assert test_user.check_password('password123') is False
    
    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token."""
        reset_data = {
            'token': 'invalid_token',
            'new_password': 'NewStrongP@ssw0rd456'
        }
        
        response = client.post('/api/auth/reset-password', json=reset_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_change_password(self, client, session, test_user, auth_headers):
        """Test password change."""
        change_data = {
            'current_password': 'password123',
            'new_password': 'NewStrongP@ssw0rd789'
        }
        
        response = client.post('/api/auth/change-password', 
                             json=change_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify password was changed
        session.refresh(test_user)
        assert test_user.check_password('NewStrongP@ssw0rd789') is True
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password."""
        change_data = {
            'current_password': 'wrongpassword',
            'new_password': 'NewStrongP@ssw0rd789'
        }
        
        response = client.post('/api/auth/change-password', 
                             json=change_data, 
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Current password is incorrect' in data['message']
    
    def test_get_profile(self, client, test_user, auth_headers):
        """Test getting user profile."""
        response = client.get('/api/auth/profile', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['id'] == test_user.id
        assert data['user']['email'] == test_user.email
        assert 'password_hash' not in data['user']  # Should not expose password
    
    def test_update_profile(self, client, session, test_user, auth_headers):
        """Test updating user profile."""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'timezone': 'America/New_York'
        }
        
        response = client.put('/api/auth/profile', 
                            json=update_data, 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify profile was updated
        session.refresh(test_user)
        assert test_user.first_name == 'Updated'
        assert test_user.last_name == 'Name'
        assert test_user.timezone == 'America/New_York'
    
    def test_enable_2fa(self, client, test_user, auth_headers):
        """Test enabling 2FA."""
        with patch('services.auth_service.pyotp.random_base32') as mock_secret:
            mock_secret.return_value = 'TESTSECRET123456'
            
            response = client.post('/api/auth/enable-2fa', headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'secret' in data
            assert 'qr_code' in data
    
    def test_verify_2fa(self, client, session, test_user, auth_headers):
        """Test verifying 2FA setup."""
        # Enable 2FA first
        test_user.two_factor_secret = 'TESTSECRET123456'
        session.commit()
        
        with patch('services.auth_service.pyotp.TOTP') as mock_totp:
            mock_totp_instance = mock_totp.return_value
            mock_totp_instance.verify.return_value = True
            
            verify_data = {'code': '123456'}
            response = client.post('/api/auth/verify-2fa', 
                                 json=verify_data, 
                                 headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_disable_2fa(self, client, session, test_user, auth_headers):
        """Test disabling 2FA."""
        # Enable 2FA first
        test_user.two_factor_enabled = True
        test_user.two_factor_secret = 'TESTSECRET123456'
        session.commit()
        
        disable_data = {'password': 'password123'}
        response = client.post('/api/auth/disable-2fa', 
                             json=disable_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify 2FA is disabled
        session.refresh(test_user)
        assert test_user.two_factor_enabled is False
        assert test_user.two_factor_secret is None
    
    def test_rate_limiting(self, client, test_user):
        """Test authentication rate limiting."""
        login_data = {
            'email': test_user.email,
            'password': 'wrongpassword'
        }
        
        # Make multiple failed login attempts
        for i in range(6):  # Assuming rate limit is 5 attempts
            response = client.post('/api/auth/login', json=login_data)
            if i < 5:
                assert response.status_code == 401
            else:
                # Should be rate limited
                assert response.status_code == 429
                data = response.get_json()
                assert 'rate limit' in data['message'].lower()
    
    def test_session_management(self, client, test_user, auth_headers):
        """Test session management endpoints."""
        # Get active sessions
        response = client.get('/api/auth/sessions', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'sessions' in data
        assert len(data['sessions']) > 0
    
    def test_revoke_session(self, client, test_user, auth_headers):
        """Test revoking a session."""
        # Get sessions first
        sessions_response = client.get('/api/auth/sessions', headers=auth_headers)
        sessions_data = sessions_response.get_json()
        session_id = sessions_data['sessions'][0]['id']
        
        # Revoke session
        response = client.delete(f'/api/auth/sessions/{session_id}', 
                               headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_api_key_authentication(self, client, test_user, test_api_key):
        """Test API key authentication."""
        headers = {'X-API-Key': 'test_api_key_value'}
        
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['user']['id'] == test_user.id
    
    def test_invalid_api_key(self, client):
        """Test authentication with invalid API key."""
        headers = {'X-API-Key': 'invalid_key'}
        
        response = client.get('/api/auth/profile', headers=headers)
        
        assert response.status_code == 401
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options('/api/auth/login')
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
    
    def test_security_headers(self, client, test_user):
        """Test security headers are present."""
        login_data = {
            'email': test_user.email,
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers