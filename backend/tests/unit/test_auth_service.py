"""Unit tests for authentication service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token, decode_token

from services.auth_service import AuthService
from models.user import User
from models import db


class TestAuthService:
    """Test cases for AuthService."""
    
    def test_register_user_success(self, app_context):
        """Test successful user registration."""
        auth_service = AuthService()
        
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        }
        
        with patch.object(db.session, 'add') as mock_add, \
             patch.object(db.session, 'commit') as mock_commit:
            
            result = auth_service.register_user(user_data)
            
            assert result['success'] is True
            assert result['message'] == 'User registered successfully'
            assert 'user' in result
            assert result['user']['username'] == 'newuser'
            assert result['user']['email'] == 'newuser@example.com'
            
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
    
    def test_register_user_duplicate_username(self, app_context, test_user):
        """Test registration with duplicate username."""
        auth_service = AuthService()
        
        user_data = {
            'username': test_user.username,
            'email': 'different@example.com',
            'password': 'password123'
        }
        
        with patch.object(User, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = test_user
            
            result = auth_service.register_user(user_data)
            
            assert result['success'] is False
            assert 'Username already exists' in result['message']
    
    def test_register_user_duplicate_email(self, app_context, test_user):
        """Test registration with duplicate email."""
        auth_service = AuthService()
        
        user_data = {
            'username': 'differentuser',
            'email': test_user.email,
            'password': 'password123'
        }
        
        with patch.object(User, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = test_user
            
            result = auth_service.register_user(user_data)
            
            assert result['success'] is False
            assert 'Email already exists' in result['message']
    
    def test_register_user_invalid_data(self, app_context):
        """Test registration with invalid data."""
        auth_service = AuthService()
        
        # Missing required fields
        user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com'
            # Missing password
        }
        
        result = auth_service.register_user(user_data)
        
        assert result['success'] is False
        assert 'Missing required fields' in result['message']
    
    def test_login_user_success(self, app_context, test_user):
        """Test successful user login."""
        auth_service = AuthService()
        
        login_data = {
            'username': test_user.username,
            'password': 'password123'
        }
        
        with patch.object(User, 'query') as mock_query, \
             patch.object(test_user, 'check_password', return_value=True), \
             patch('app.services.auth_service.create_access_token') as mock_create_token:
            
            mock_query.filter_by.return_value.first.return_value = test_user
            mock_create_token.return_value = 'test_token'
            
            result = auth_service.login_user(login_data)
            
            assert result['success'] is True
            assert result['message'] == 'Login successful'
            assert result['access_token'] == 'test_token'
            assert 'user' in result
    
    def test_login_user_invalid_username(self, app_context):
        """Test login with invalid username."""
        auth_service = AuthService()
        
        login_data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        
        with patch.object(User, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            result = auth_service.login_user(login_data)
            
            assert result['success'] is False
            assert 'Invalid username or password' in result['message']
    
    def test_login_user_invalid_password(self, app_context, test_user):
        """Test login with invalid password."""
        auth_service = AuthService()
        
        login_data = {
            'username': test_user.username,
            'password': 'wrongpassword'
        }
        
        with patch.object(User, 'query') as mock_query, \
             patch.object(test_user, 'check_password', return_value=False):
            
            mock_query.filter_by.return_value.first.return_value = test_user
            
            result = auth_service.login_user(login_data)
            
            assert result['success'] is False
            assert 'Invalid username or password' in result['message']
    
    def test_login_user_inactive_account(self, app_context, test_user):
        """Test login with inactive account."""
        auth_service = AuthService()
        test_user.is_active = False
        
        login_data = {
            'username': test_user.username,
            'password': 'password123'
        }
        
        with patch.object(User, 'query') as mock_query, \
             patch.object(test_user, 'check_password', return_value=True):
            
            mock_query.filter_by.return_value.first.return_value = test_user
            
            result = auth_service.login_user(login_data)
            
            assert result['success'] is False
            assert 'Account is inactive' in result['message']
    
    def test_validate_token_success(self, app_context, test_user):
        """Test successful token validation."""
        auth_service = AuthService()
        
        with patch('app.services.auth_service.decode_token') as mock_decode, \
             patch.object(User, 'query') as mock_query:
            
            mock_decode.return_value = {'sub': test_user.id}
            mock_query.get.return_value = test_user
            
            result = auth_service.validate_token('test_token')
            
            assert result['valid'] is True
            assert result['user'] == test_user
    
    def test_validate_token_invalid(self, app_context):
        """Test validation of invalid token."""
        auth_service = AuthService()
        
        with patch('app.services.auth_service.decode_token') as mock_decode:
            mock_decode.side_effect = Exception('Invalid token')
            
            result = auth_service.validate_token('invalid_token')
            
            assert result['valid'] is False
            assert 'Invalid token' in result['message']
    
    def test_validate_token_user_not_found(self, app_context):
        """Test validation when user not found."""
        auth_service = AuthService()
        
        with patch('app.services.auth_service.decode_token') as mock_decode, \
             patch.object(User, 'query') as mock_query:
            
            mock_decode.return_value = {'sub': 999}
            mock_query.get.return_value = None
            
            result = auth_service.validate_token('test_token')
            
            assert result['valid'] is False
            assert 'User not found' in result['message']
    
    def test_refresh_token_success(self, app_context, test_user):
        """Test successful token refresh."""
        auth_service = AuthService()
        
        with patch('app.services.auth_service.decode_token') as mock_decode, \
             patch.object(User, 'query') as mock_query, \
             patch('app.services.auth_service.create_access_token') as mock_create:
            
            mock_decode.return_value = {'sub': test_user.id}
            mock_query.get.return_value = test_user
            mock_create.return_value = 'new_token'
            
            result = auth_service.refresh_token('refresh_token')
            
            assert result['success'] is True
            assert result['access_token'] == 'new_token'
    
    def test_change_password_success(self, app_context, test_user):
        """Test successful password change."""
        auth_service = AuthService()
        
        password_data = {
            'current_password': 'password123',
            'new_password': 'newpassword123'
        }
        
        with patch.object(test_user, 'check_password', return_value=True), \
             patch.object(db.session, 'commit') as mock_commit:
            
            result = auth_service.change_password(test_user, password_data)
            
            assert result['success'] is True
            assert result['message'] == 'Password changed successfully'
            mock_commit.assert_called_once()
    
    def test_change_password_invalid_current(self, app_context, test_user):
        """Test password change with invalid current password."""
        auth_service = AuthService()
        
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }
        
        with patch.object(test_user, 'check_password', return_value=False):
            
            result = auth_service.change_password(test_user, password_data)
            
            assert result['success'] is False
            assert 'Current password is incorrect' in result['message']
    
    def test_reset_password_request(self, app_context, test_user):
        """Test password reset request."""
        auth_service = AuthService()
        
        with patch.object(User, 'query') as mock_query, \
             patch('app.services.auth_service.send_reset_email') as mock_send:
            
            mock_query.filter_by.return_value.first.return_value = test_user
            
            result = auth_service.request_password_reset('test@example.com')
            
            assert result['success'] is True
            assert result['message'] == 'Password reset email sent'
            mock_send.assert_called_once()
    
    def test_reset_password_request_user_not_found(self, app_context):
        """Test password reset request for non-existent user."""
        auth_service = AuthService()
        
        with patch.object(User, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None
            
            result = auth_service.request_password_reset('nonexistent@example.com')
            
            assert result['success'] is False
            assert 'User not found' in result['message']
    
    def test_logout_user(self, app_context):
        """Test user logout (token blacklisting)."""
        auth_service = AuthService()
        
        with patch('app.services.auth_service.blacklist_token') as mock_blacklist:
            
            result = auth_service.logout_user('test_token')
            
            assert result['success'] is True
            assert result['message'] == 'Logged out successfully'
            mock_blacklist.assert_called_once_with('test_token')
    
    def test_get_user_profile(self, app_context, test_user):
        """Test getting user profile."""
        auth_service = AuthService()
        
        profile = auth_service.get_user_profile(test_user)
        
        assert profile['id'] == test_user.id
        assert profile['username'] == test_user.username
        assert profile['email'] == test_user.email
        assert profile['is_active'] == test_user.is_active
        assert profile['is_premium'] == test_user.is_premium
        assert 'password_hash' not in profile
    
    def test_update_user_profile(self, app_context, test_user):
        """Test updating user profile."""
        auth_service = AuthService()
        
        update_data = {
            'email': 'newemail@example.com'
        }
        
        with patch.object(db.session, 'commit') as mock_commit:
            
            result = auth_service.update_user_profile(test_user, update_data)
            
            assert result['success'] is True
            assert result['message'] == 'Profile updated successfully'
            assert test_user.email == 'newemail@example.com'
            mock_commit.assert_called_once()
    
    def test_deactivate_user(self, app_context, test_user):
        """Test user account deactivation."""
        auth_service = AuthService()
        
        with patch.object(db.session, 'commit') as mock_commit:
            
            result = auth_service.deactivate_user(test_user)
            
            assert result['success'] is True
            assert result['message'] == 'Account deactivated successfully'
            assert test_user.is_active is False
            mock_commit.assert_called_once()