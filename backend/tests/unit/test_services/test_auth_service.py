"""Unit tests for AuthService."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt

from services.auth_service import AuthService
from models.user import User


@pytest.mark.unit
class TestAuthService:
    """Test AuthService functionality."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = 'password123'
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert AuthService.verify_password(password, hashed) is True
        assert AuthService.verify_password('wrongpassword', hashed) is False
    
    def test_verify_password(self):
        """Test password verification."""
        password = 'testpassword'
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(password, hashed) is True
        assert AuthService.verify_password('wrong', hashed) is False
        assert AuthService.verify_password('', hashed) is False
        assert AuthService.verify_password(None, hashed) is False
    
    def test_generate_jwt_token(self, app):
        """Test JWT token generation."""
        with app.app_context():
            user_id = 123
            token = AuthService.generate_jwt_token(user_id)
            
            assert token is not None
            assert len(token) > 0
            
            # Decode token to verify contents
            decoded = jwt.decode(
                token, 
                app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256']
            )
            
            assert decoded['user_id'] == user_id
            assert 'exp' in decoded
            assert 'iat' in decoded
    
    def test_verify_jwt_token(self, app):
        """Test JWT token verification."""
        with app.app_context():
            user_id = 123
            token = AuthService.generate_jwt_token(user_id)
            
            # Valid token
            decoded_user_id = AuthService.verify_jwt_token(token)
            assert decoded_user_id == user_id
            
            # Invalid token
            invalid_token = 'invalid.token.here'
            assert AuthService.verify_jwt_token(invalid_token) is None
            
            # Empty token
            assert AuthService.verify_jwt_token('') is None
            assert AuthService.verify_jwt_token(None) is None
    
    def test_expired_jwt_token(self, app):
        """Test expired JWT token handling."""
        with app.app_context():
            # Create expired token
            payload = {
                'user_id': 123,
                'exp': datetime.utcnow() - timedelta(hours=1),
                'iat': datetime.utcnow() - timedelta(hours=2)
            }
            
            expired_token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            # Should return None for expired token
            assert AuthService.verify_jwt_token(expired_token) is None
    
    def test_generate_refresh_token(self, app):
        """Test refresh token generation."""
        with app.app_context():
            user_id = 123
            refresh_token = AuthService.generate_refresh_token(user_id)
            
            assert refresh_token is not None
            assert len(refresh_token) > 0
            
            # Verify refresh token
            decoded_user_id = AuthService.verify_refresh_token(refresh_token)
            assert decoded_user_id == user_id
    
    def test_authenticate_user(self, session, test_user):
        """Test user authentication."""
        # Successful authentication
        authenticated_user = AuthService.authenticate_user(
            test_user.email, 
            'password123'
        )
        assert authenticated_user == test_user
        
        # Wrong password
        assert AuthService.authenticate_user(
            test_user.email, 
            'wrongpassword'
        ) is None
        
        # Non-existent user
        assert AuthService.authenticate_user(
            'nonexistent@example.com', 
            'password123'
        ) is None
        
        # Empty credentials
        assert AuthService.authenticate_user('', '') is None
        assert AuthService.authenticate_user(None, None) is None
    
    def test_authenticate_locked_user(self, session):
        """Test authentication of locked user."""
        # Create locked user
        locked_user = User(
            email='locked@example.com',
            username='locked',
            password_hash=AuthService.hash_password('password123'),
            failed_login_attempts=5,
            locked_until=datetime.utcnow() + timedelta(minutes=30)
        )
        session.add(locked_user)
        session.commit()
        
        # Should not authenticate locked user
        assert AuthService.authenticate_user(
            locked_user.email, 
            'password123'
        ) is None
    
    def test_authenticate_unverified_user(self, session, unverified_user):
        """Test authentication of unverified user."""
        # Should not authenticate unverified user
        assert AuthService.authenticate_user(
            unverified_user.email, 
            'password123'
        ) is None
    
    def test_register_user(self, session):
        """Test user registration."""
        user_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'password123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        user = AuthService.register_user(user_data)
        
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert user.username == 'newuser'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.is_verified is False
        assert user.check_password('password123') is True
    
    def test_register_duplicate_user(self, session, test_user):
        """Test registration with duplicate email/username."""
        # Duplicate email
        user_data = {
            'email': test_user.email,
            'username': 'different',
            'password': 'password123'
        }
        
        with pytest.raises(ValueError, match="Email already exists"):
            AuthService.register_user(user_data)
        
        # Duplicate username
        user_data = {
            'email': 'different@example.com',
            'username': test_user.username,
            'password': 'password123'
        }
        
        with pytest.raises(ValueError, match="Username already exists"):
            AuthService.register_user(user_data)
    
    def test_register_invalid_data(self, session):
        """Test registration with invalid data."""
        # Missing required fields
        with pytest.raises(ValueError):
            AuthService.register_user({})
        
        # Invalid email
        with pytest.raises(ValueError, match="Invalid email"):
            AuthService.register_user({
                'email': 'invalid-email',
                'username': 'user',
                'password': 'password123'
            })
        
        # Weak password
        with pytest.raises(ValueError, match="Password too weak"):
            AuthService.register_user({
                'email': 'user@example.com',
                'username': 'user',
                'password': '123'
            })
    
    def test_change_password(self, session, test_user):
        """Test password change."""
        old_password = 'password123'
        new_password = 'newpassword456'
        
        # Successful password change
        success = AuthService.change_password(
            test_user, 
            old_password, 
            new_password
        )
        
        assert success is True
        assert test_user.check_password(new_password) is True
        assert test_user.check_password(old_password) is False
        
        # Wrong old password
        success = AuthService.change_password(
            test_user, 
            'wrongpassword', 
            'anotherpassword'
        )
        
        assert success is False
        assert test_user.check_password(new_password) is True
    
    def test_reset_password(self, session, test_user):
        """Test password reset."""
        new_password = 'resetpassword789'
        
        # Generate reset token
        token = AuthService.generate_password_reset_token(test_user)
        assert token is not None
        
        # Reset password with token
        success = AuthService.reset_password_with_token(token, new_password)
        assert success is True
        
        # Verify new password works
        session.refresh(test_user)
        assert test_user.check_password(new_password) is True
        
        # Invalid token
        success = AuthService.reset_password_with_token(
            'invalid_token', 
            'anotherpassword'
        )
        assert success is False
    
    def test_verify_email(self, session, unverified_user):
        """Test email verification."""
        # Generate verification token
        token = AuthService.generate_email_verification_token(unverified_user)
        assert token is not None
        
        # Verify email with token
        success = AuthService.verify_email_with_token(token)
        assert success is True
        
        # Check user is now verified
        session.refresh(unverified_user)
        assert unverified_user.is_verified is True
        
        # Invalid token
        success = AuthService.verify_email_with_token('invalid_token')
        assert success is False
    
    def test_login_attempt_tracking(self, session, test_user):
        """Test failed login attempt tracking."""
        # Successful login resets attempts
        test_user.failed_login_attempts = 2
        session.commit()
        
        AuthService.record_login_attempt(test_user, success=True)
        session.refresh(test_user)
        
        assert test_user.failed_login_attempts == 0
        assert test_user.last_login is not None
        
        # Failed login increments attempts
        AuthService.record_login_attempt(test_user, success=False)
        session.refresh(test_user)
        
        assert test_user.failed_login_attempts == 1
    
    def test_account_lockout(self, session, test_user):
        """Test account lockout after failed attempts."""
        # Simulate multiple failed attempts
        for i in range(5):
            AuthService.record_login_attempt(test_user, success=False)
        
        session.refresh(test_user)
        
        assert test_user.is_locked() is True
        assert test_user.locked_until is not None
        
        # Should not authenticate locked user
        authenticated = AuthService.authenticate_user(
            test_user.email, 
            'password123'
        )
        assert authenticated is None
    
    def test_unlock_account(self, session, test_user):
        """Test account unlocking."""
        # Lock account
        test_user.failed_login_attempts = 5
        test_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        session.commit()
        
        # Unlock account
        AuthService.unlock_account(test_user)
        session.refresh(test_user)
        
        assert test_user.failed_login_attempts == 0
        assert test_user.locked_until is None
        assert test_user.is_locked() is False
    
    def test_session_management(self, session, test_user):
        """Test session management."""
        # Create session
        session_id = AuthService.create_session(test_user.id)
        assert session_id is not None
        
        # Validate session
        user_id = AuthService.validate_session(session_id)
        assert user_id == test_user.id
        
        # Invalidate session
        AuthService.invalidate_session(session_id)
        
        # Should not validate invalidated session
        user_id = AuthService.validate_session(session_id)
        assert user_id is None
    
    def test_two_factor_authentication(self, session, test_user):
        """Test 2FA functionality."""
        # Enable 2FA
        secret = AuthService.enable_2fa(test_user)
        assert secret is not None
        assert test_user.two_factor_enabled is True
        
        # Generate TOTP code
        with patch('pyotp.TOTP') as mock_totp:
            mock_totp_instance = Mock()
            mock_totp.return_value = mock_totp_instance
            mock_totp_instance.now.return_value = '123456'
            
            # Verify TOTP code
            mock_totp_instance.verify.return_value = True
            assert AuthService.verify_2fa_code(test_user, '123456') is True
            
            # Invalid code
            mock_totp_instance.verify.return_value = False
            assert AuthService.verify_2fa_code(test_user, '000000') is False
        
        # Disable 2FA
        AuthService.disable_2fa(test_user)
        assert test_user.two_factor_enabled is False
    
    def test_api_key_authentication(self, session, test_user, test_api_key):
        """Test API key authentication."""
        # Valid API key
        user = AuthService.authenticate_api_key('test_api_key_value')
        assert user == test_user
        
        # Invalid API key
        user = AuthService.authenticate_api_key('invalid_key')
        assert user is None
        
        # Disabled API key
        test_api_key.is_active = False
        session.commit()
        
        user = AuthService.authenticate_api_key('test_api_key_value')
        assert user is None
    
    def test_rate_limiting(self, session, test_user):
        """Test authentication rate limiting."""
        with patch('services.auth_service.redis_client') as mock_redis:
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True
            
            # First attempt should be allowed
            allowed = AuthService.check_rate_limit(test_user.email)
            assert allowed is True
            
            # Simulate rate limit exceeded
            mock_redis.get.return_value = b'10'  # 10 attempts
            
            allowed = AuthService.check_rate_limit(test_user.email)
            assert allowed is False
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        # Strong password
        assert AuthService.validate_password_strength('StrongP@ssw0rd123') is True
        
        # Weak passwords
        assert AuthService.validate_password_strength('weak') is False
        assert AuthService.validate_password_strength('12345678') is False
        assert AuthService.validate_password_strength('password') is False
        assert AuthService.validate_password_strength('PASSWORD') is False
        assert AuthService.validate_password_strength('Password') is False
        assert AuthService.validate_password_strength('Password123') is False  # No special char
    
    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        assert AuthService.validate_email('user@example.com') is True
        assert AuthService.validate_email('test.email+tag@domain.co.uk') is True
        
        # Invalid emails
        assert AuthService.validate_email('invalid-email') is False
        assert AuthService.validate_email('@domain.com') is False
        assert AuthService.validate_email('user@') is False
        assert AuthService.validate_email('') is False
        assert AuthService.validate_email(None) is False
    
    def test_username_validation(self):
        """Test username validation."""
        # Valid usernames
        assert AuthService.validate_username('validuser') is True
        assert AuthService.validate_username('user123') is True
        assert AuthService.validate_username('user_name') is True
        
        # Invalid usernames
        assert AuthService.validate_username('ab') is False  # Too short
        assert AuthService.validate_username('a' * 51) is False  # Too long
        assert AuthService.validate_username('user@name') is False  # Invalid chars
        assert AuthService.validate_username('123user') is False  # Starts with number
        assert AuthService.validate_username('') is False
        assert AuthService.validate_username(None) is False