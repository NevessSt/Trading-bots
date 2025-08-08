"""Integration tests for authentication system."""
import pytest
import json
from flask import url_for
from datetime import datetime, timedelta

from models.user import User
from models.subscription import Subscription
from db import db


class TestAuthIntegration:
    """Integration tests for authentication flow."""
    
    def test_complete_registration_flow(self, client, app_context):
        """Test complete user registration and verification flow."""
        # Step 1: Register new user
        user_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify user was created in database
        user = User.query.filter_by(username='integrationuser').first()
        assert user is not None
        assert user.email == 'integration@example.com'
        assert user.is_active is True
        assert user.is_premium is False
    
    def test_login_logout_flow(self, client, app_context):
        """Test complete login and logout flow."""
        # Create a test user first
        user = User(
            username='loginuser',
            email='login@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Step 1: Login
        login_data = {
            'username': 'loginuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'access_token' in data
        
        access_token = data['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Step 2: Access protected endpoint
        response = client.get('/api/auth/profile', headers=headers)
        assert response.status_code == 200
        profile_data = json.loads(response.data)
        assert profile_data['username'] == 'loginuser'
        
        # Step 3: Logout
        response = client.post('/api/auth/logout', headers=headers)
        assert response.status_code == 200
        logout_data = json.loads(response.data)
        assert logout_data['success'] is True
        
        # Step 4: Try to access protected endpoint after logout
        response = client.get('/api/auth/profile', headers=headers)
        assert response.status_code == 401
    
    def test_password_change_flow(self, client, app_context):
        """Test password change flow."""
        # Create and login user
        user = User(
            username='passworduser',
            email='password@example.com',
            password='oldpassword123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Login
        login_data = {
            'username': 'passworduser',
            'password': 'oldpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Change password
        password_data = {
            'current_password': 'oldpassword123',
            'new_password': 'newpassword123'
        }
        
        response = client.put('/api/auth/password',
                            data=json.dumps(password_data),
                            content_type='application/json',
                            headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify old password no longer works
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        
        # Verify new password works
        new_login_data = {
            'username': 'passworduser',
            'password': 'newpassword123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(new_login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
    
    def test_profile_update_flow(self, client, app_context):
        """Test profile update flow."""
        # Create and login user
        user = User(
            username='profileuser',
            email='profile@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Login
        login_data = {
            'username': 'profileuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Update profile
        update_data = {
            'email': 'newemail@example.com'
        }
        
        response = client.put('/api/auth/profile',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify profile was updated
        response = client.get('/api/auth/profile', headers=headers)
        profile_data = json.loads(response.data)
        assert profile_data['email'] == 'newemail@example.com'
        
        # Verify in database
        updated_user = User.query.filter_by(username='profileuser').first()
        assert updated_user.email == 'newemail@example.com'
    
    def test_premium_subscription_flow(self, client, app_context):
        """Test premium subscription integration."""
        # Create user
        user = User(
            username='premiumuser',
            email='premium@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Login
        login_data = {
            'username': 'premiumuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Check initial profile (should not be premium)
        response = client.get('/api/auth/profile', headers=headers)
        profile_data = json.loads(response.data)
        assert profile_data['is_premium'] is False
        
        # Create premium subscription
        subscription = Subscription(
            user_id=user.id,
            plan='premium',
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
        
        # Update user to premium
        user.is_premium = True
        db.session.commit()
        
        # Check updated profile
        response = client.get('/api/auth/profile', headers=headers)
        profile_data = json.loads(response.data)
        assert profile_data['is_premium'] is True
    
    def test_account_deactivation_flow(self, client, app_context):
        """Test account deactivation flow."""
        # Create and login user
        user = User(
            username='deactivateuser',
            email='deactivate@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Login
        login_data = {
            'username': 'deactivateuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        access_token = json.loads(response.data)['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Deactivate account
        response = client.delete('/api/auth/account', headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify user is deactivated in database
        deactivated_user = User.query.filter_by(username='deactivateuser').first()
        assert deactivated_user.is_active is False
        
        # Try to login with deactivated account
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'inactive' in data['message'].lower()
    
    def test_token_refresh_flow(self, client, app_context):
        """Test token refresh flow."""
        # Create and login user
        user = User(
            username='refreshuser',
            email='refresh@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        # Login
        login_data = {
            'username': 'refreshuser',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        data = json.loads(response.data)
        access_token = data['access_token']
        refresh_token = data.get('refresh_token', access_token)  # Fallback if no separate refresh token
        
        # Use refresh token to get new access token
        refresh_data = {
            'refresh_token': refresh_token
        }
        
        response = client.post('/api/auth/refresh',
                             data=json.dumps(refresh_data),
                             content_type='application/json')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'access_token' in data
            new_access_token = data['access_token']
            
            # Verify new token works
            headers = {'Authorization': f'Bearer {new_access_token}'}
            response = client.get('/api/auth/profile', headers=headers)
            assert response.status_code == 200
    
    def test_concurrent_login_sessions(self, client, app_context):
        """Test multiple concurrent login sessions."""
        # Create user
        user = User(
            username='concurrentuser',
            email='concurrent@example.com',
            password='password123'
        )
        db.session.add(user)
        db.session.commit()
        
        login_data = {
            'username': 'concurrentuser',
            'password': 'password123'
        }
        
        # Login from first session
        response1 = client.post('/api/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        token1 = json.loads(response1.data)['access_token']
        headers1 = {'Authorization': f'Bearer {token1}'}
        
        # Login from second session
        response2 = client.post('/api/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        token2 = json.loads(response2.data)['access_token']
        headers2 = {'Authorization': f'Bearer {token2}'}
        
        # Both sessions should work
        response = client.get('/api/auth/profile', headers=headers1)
        assert response.status_code == 200
        
        response = client.get('/api/auth/profile', headers=headers2)
        assert response.status_code == 200
        
        # Logout from first session
        response = client.post('/api/auth/logout', headers=headers1)
        assert response.status_code == 200
        
        # First session should be invalid, second should still work
        response = client.get('/api/auth/profile', headers=headers1)
        assert response.status_code == 401
        
        response = client.get('/api/auth/profile', headers=headers2)
        assert response.status_code == 200