"""Unit tests for User model."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from models.user import User
from services.auth_service import AuthService


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self, session):
        """Test creating a new user."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash=AuthService.hash_password('password123')
        )
        session.add(user)
        session.commit()
        
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.is_verified is False
        assert user.role == 'user'
        assert user.subscription_plan == 'free'
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_email_unique(self, session):
        """Test that user email must be unique."""
        user1 = User(
            email='test@example.com',
            username='user1',
            password_hash='hash1'
        )
        user2 = User(
            email='test@example.com',
            username='user2',
            password_hash='hash2'
        )
        
        session.add(user1)
        session.commit()
        
        session.add(user2)
        with pytest.raises(IntegrityError):
            session.commit()
    
    def test_user_username_unique(self, session):
        """Test that username must be unique."""
        user1 = User(
            email='user1@example.com',
            username='testuser',
            password_hash='hash1'
        )
        user2 = User(
            email='user2@example.com',
            username='testuser',
            password_hash='hash2'
        )
        
        session.add(user1)
        session.commit()
        
        session.add(user2)
        with pytest.raises(IntegrityError):
            session.commit()
    
    def test_check_password(self, session):
        """Test password verification."""
        password = 'password123'
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash=AuthService.hash_password(password)
        )
        session.add(user)
        session.commit()
        
        assert user.check_password(password) is True
        assert user.check_password('wrongpassword') is False
    
    def test_set_password(self, session):
        """Test setting a new password."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='old_hash'
        )
        session.add(user)
        session.commit()
        
        new_password = 'newpassword123'
        user.set_password(new_password)
        session.commit()
        
        assert user.check_password(new_password) is True
        assert user.check_password('old_password') is False
    
    def test_user_repr(self, session):
        """Test user string representation."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash'
        )
        session.add(user)
        session.commit()
        
        assert repr(user) == f'<User {user.username}>'
    
    def test_user_to_dict(self, session):
        """Test user dictionary representation."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash',
            is_verified=True,
            role='admin',
            subscription_plan='premium'
        )
        session.add(user)
        session.commit()
        
        user_dict = user.to_dict()
        
        assert user_dict['id'] == user.id
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['username'] == 'testuser'
        assert user_dict['is_verified'] is True
        assert user_dict['role'] == 'admin'
        assert user_dict['subscription_plan'] == 'premium'
        assert 'password_hash' not in user_dict
        assert 'created_at' in user_dict
        assert 'updated_at' in user_dict
    
    def test_user_is_admin(self, session):
        """Test admin role checking."""
        admin_user = User(
            email='admin@example.com',
            username='admin',
            password_hash='hash',
            role='admin'
        )
        regular_user = User(
            email='user@example.com',
            username='user',
            password_hash='hash',
            role='user'
        )
        
        session.add_all([admin_user, regular_user])
        session.commit()
        
        assert admin_user.is_admin() is True
        assert regular_user.is_admin() is False
    
    def test_user_subscription_limits(self, session):
        """Test subscription plan limits."""
        free_user = User(
            email='free@example.com',
            username='free',
            password_hash='hash',
            subscription_plan='free'
        )
        basic_user = User(
            email='basic@example.com',
            username='basic',
            password_hash='hash',
            subscription_plan='basic'
        )
        premium_user = User(
            email='premium@example.com',
            username='premium',
            password_hash='hash',
            subscription_plan='premium'
        )
        
        session.add_all([free_user, basic_user, premium_user])
        session.commit()
        
        # Test bot limits
        assert free_user.get_bot_limit() == 1
        assert basic_user.get_bot_limit() == 5
        assert premium_user.get_bot_limit() == 20
        
        # Test API call limits
        assert free_user.get_api_limit() == 100
        assert basic_user.get_api_limit() == 1000
        assert premium_user.get_api_limit() == 10000
    
    def test_user_verification_token(self, session):
        """Test email verification token generation."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash'
        )
        session.add(user)
        session.commit()
        
        token = user.generate_verification_token()
        assert token is not None
        assert len(token) > 0
        
        # Test token verification
        assert user.verify_email_token(token) is True
        assert user.verify_email_token('invalid_token') is False
    
    def test_user_password_reset_token(self, session):
        """Test password reset token generation."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash'
        )
        session.add(user)
        session.commit()
        
        token = user.generate_reset_token()
        assert token is not None
        assert len(token) > 0
        
        # Test token verification
        assert user.verify_reset_token(token) is True
        assert user.verify_reset_token('invalid_token') is False
    
    def test_user_last_login_update(self, session):
        """Test last login timestamp update."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash'
        )
        session.add(user)
        session.commit()
        
        assert user.last_login is None
        
        user.update_last_login()
        session.commit()
        
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
    
    def test_user_failed_login_attempts(self, session):
        """Test failed login attempt tracking."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash'
        )
        session.add(user)
        session.commit()
        
        assert user.failed_login_attempts == 0
        assert user.is_locked() is False
        
        # Increment failed attempts
        for i in range(5):
            user.increment_failed_login()
            session.commit()
        
        assert user.failed_login_attempts == 5
        assert user.is_locked() is True
        
        # Reset failed attempts
        user.reset_failed_login()
        session.commit()
        
        assert user.failed_login_attempts == 0
        assert user.is_locked() is False
    
    def test_user_subscription_status(self, session):
        """Test subscription status checking."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash',
            subscription_plan='premium',
            subscription_end_date=datetime.utcnow() + timedelta(days=30)
        )
        session.add(user)
        session.commit()
        
        assert user.has_active_subscription() is True
        
        # Expire subscription
        user.subscription_end_date = datetime.utcnow() - timedelta(days=1)
        session.commit()
        
        assert user.has_active_subscription() is False
    
    def test_user_api_usage_tracking(self, session):
        """Test API usage tracking."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash',
            subscription_plan='basic'
        )
        session.add(user)
        session.commit()
        
        # Test initial usage
        assert user.api_calls_today == 0
        assert user.can_make_api_call() is True
        
        # Increment usage
        for i in range(500):
            user.increment_api_usage()
        
        session.commit()
        assert user.api_calls_today == 500
        assert user.can_make_api_call() is True
        
        # Exceed limit
        for i in range(600):
            user.increment_api_usage()
        
        session.commit()
        assert user.api_calls_today == 1100
        assert user.can_make_api_call() is False
    
    def test_user_profile_completion(self, session):
        """Test profile completion checking."""
        incomplete_user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash'
        )
        
        complete_user = User(
            email='complete@example.com',
            username='completeuser',
            password_hash='hash',
            first_name='John',
            last_name='Doe',
            phone='1234567890'
        )
        
        session.add_all([incomplete_user, complete_user])
        session.commit()
        
        assert incomplete_user.is_profile_complete() is False
        assert complete_user.is_profile_complete() is True
    
    def test_user_timezone_handling(self, session):
        """Test timezone handling."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash',
            timezone='America/New_York'
        )
        session.add(user)
        session.commit()
        
        # Test timezone conversion
        utc_time = datetime.utcnow()
        local_time = user.to_local_time(utc_time)
        
        assert local_time is not None
        # Note: Actual timezone conversion would require pytz library
    
    def test_user_preferences(self, session):
        """Test user preferences handling."""
        user = User(
            email='test@example.com',
            username='testuser',
            password_hash='hash',
            preferences={
                'email_notifications': True,
                'sms_notifications': False,
                'theme': 'dark',
                'language': 'en'
            }
        )
        session.add(user)
        session.commit()
        
        assert user.get_preference('email_notifications') is True
        assert user.get_preference('sms_notifications') is False
        assert user.get_preference('theme') == 'dark'
        assert user.get_preference('nonexistent', 'default') == 'default'
        
        # Update preference
        user.set_preference('theme', 'light')
        session.commit()
        
        assert user.get_preference('theme') == 'light'