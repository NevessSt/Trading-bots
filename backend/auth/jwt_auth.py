import jwt
import datetime
from functools import wraps
from flask import current_app, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class JWTAuth:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.config.setdefault('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', datetime.timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', datetime.timedelta(days=30))
        
    def generate_tokens(self, user_id, email, role='user'):
        """Generate access and refresh tokens"""
        now = datetime.datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': now,
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user_id,
            'exp': now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            'iat': now,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
        }
    
    def verify_token(self, token, token_type='access'):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            if payload.get('type') != token_type:
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token):
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
            
        # Get user info from database to ensure user still exists
        from models.user import User
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return None
            
        return self.generate_tokens(user.id, user.email, user.role)
    
    def hash_password(self, password):
        """Hash password securely"""
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        return check_password_hash(password_hash, password)

# Global instance
jwt_auth = JWTAuth()