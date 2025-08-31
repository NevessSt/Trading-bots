"""OAuth2 service for social authentication integration."""

import requests
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from flask import current_app, url_for
from models import User, db
from .auth_service import AuthService
from .license_service import LicenseType
from .logging_service import get_logger, LogCategory
from .error_handler import handle_errors, ErrorCategory


class OAuthService:
    """Service for handling OAuth2 authentication with various providers."""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.logger = get_logger(LogCategory.AUTHENTICATION)
        
        # OAuth2 provider configurations
        self.providers = {
            'google': {
                'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
                'client_secret': current_app.config.get('GOOGLE_CLIENT_SECRET'),
                'auth_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scope': 'openid email profile'
            },
            'github': {
                'client_id': current_app.config.get('GITHUB_CLIENT_ID'),
                'client_secret': current_app.config.get('GITHUB_CLIENT_SECRET'),
                'auth_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'user_info_url': 'https://api.github.com/user',
                'scope': 'user:email'
            },
            'microsoft': {
                'client_id': current_app.config.get('MICROSOFT_CLIENT_ID'),
                'client_secret': current_app.config.get('MICROSOFT_CLIENT_SECRET'),
                'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'user_info_url': 'https://graph.microsoft.com/v1.0/me',
                'scope': 'openid email profile'
            }
        }
    
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def get_authorization_url(self, provider: str, redirect_uri: str) -> str:
        """Generate OAuth2 authorization URL for the specified provider."""
        if provider not in self.providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        config = self.providers[provider]
        state = secrets.token_urlsafe(32)
        
        # Store state in session or cache for validation
        # In production, you'd want to store this in Redis or similar
        current_app.config['OAUTH_STATES'] = current_app.config.get('OAUTH_STATES', {})
        current_app.config['OAUTH_STATES'][state] = {
            'provider': provider,
            'created_at': datetime.utcnow(),
            'redirect_uri': redirect_uri
        }
        
        params = {
            'client_id': config['client_id'],
            'redirect_uri': redirect_uri,
            'scope': config['scope'],
            'response_type': 'code',
            'state': state
        }
        
        # Add provider-specific parameters
        if provider == 'microsoft':
            params['response_mode'] = 'query'
        
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        self.logger.info(f"Generated OAuth authorization URL for {provider}")
        
        return auth_url
    
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def handle_callback(self, provider: str, code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and authenticate user."""
        if provider not in self.providers:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        # Validate state parameter
        stored_states = current_app.config.get('OAUTH_STATES', {})
        if state not in stored_states:
            raise ValueError("Invalid or expired OAuth state")
        
        state_data = stored_states[state]
        if state_data['provider'] != provider:
            raise ValueError("OAuth state provider mismatch")
        
        # Clean up used state
        del stored_states[state]
        
        # Exchange code for access token
        access_token = self._exchange_code_for_token(provider, code, redirect_uri)
        
        # Get user info from provider
        user_info = self._get_user_info(provider, access_token)
        
        # Find or create user
        user = self._find_or_create_oauth_user(provider, user_info)
        
        # Generate JWT tokens
        tokens = self.auth_service.create_tokens(user)
        
        self.logger.info(f"OAuth authentication successful for {provider}: {user.email}")
        
        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'oauth_provider': provider
            },
            'tokens': tokens
        }
    
    def _exchange_code_for_token(self, provider: str, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token."""
        config = self.providers[provider]
        
        data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        headers = {'Accept': 'application/json'}
        
        response = requests.post(config['token_url'], data=data, headers=headers)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data['access_token']
    
    def _get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider."""
        config = self.providers[provider]
        
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(config['user_info_url'], headers=headers)
        response.raise_for_status()
        
        user_data = response.json()
        
        # Normalize user data across providers
        if provider == 'google':
            return {
                'email': user_data.get('email'),
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'avatar_url': user_data.get('picture'),
                'provider_id': user_data.get('id')
            }
        elif provider == 'github':
            # GitHub might not provide email in user endpoint
            email = user_data.get('email')
            if not email:
                # Fetch email from separate endpoint
                email_response = requests.get(
                    'https://api.github.com/user/emails',
                    headers=headers
                )
                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next((e['email'] for e in emails if e['primary']), None)
                    email = primary_email or emails[0]['email'] if emails else None
            
            name_parts = (user_data.get('name') or '').split(' ', 1)
            return {
                'email': email,
                'first_name': name_parts[0] if name_parts else '',
                'last_name': name_parts[1] if len(name_parts) > 1 else '',
                'avatar_url': user_data.get('avatar_url'),
                'provider_id': str(user_data.get('id'))
            }
        elif provider == 'microsoft':
            return {
                'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                'first_name': user_data.get('givenName', ''),
                'last_name': user_data.get('surname', ''),
                'avatar_url': None,  # Microsoft Graph requires separate call
                'provider_id': user_data.get('id')
            }
        
        return user_data
    
    def _find_or_create_oauth_user(self, provider: str, user_info: Dict[str, Any]) -> User:
        """Find existing user or create new one from OAuth data."""
        email = user_info.get('email')
        if not email:
            raise ValueError("Email is required for OAuth authentication")
        
        # Try to find existing user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Update OAuth provider info if not set
            if not user.oauth_provider:
                user.oauth_provider = provider
                user.oauth_provider_id = user_info.get('provider_id')
                user.updated_at = datetime.utcnow()
                db.session.commit()
            
            self.logger.info(f"Existing user found for OAuth login: {email}")
            return user
        
        # Create new user
        username = self._generate_username_from_email(email)
        
        user = User(
            username=username,
            email=email,
            first_name=user_info.get('first_name', ''),
            last_name=user_info.get('last_name', ''),
            is_verified=True,  # OAuth users are pre-verified
            oauth_provider=provider,
            oauth_provider_id=user_info.get('provider_id'),
            avatar_url=user_info.get('avatar_url')
        )
        
        # Generate demo license for new OAuth users
        license_data = self.auth_service.license_service.generate_license(
            user_email=email,
            license_type=LicenseType.DEMO,
            duration_days=30
        )
        
        user.license_key = license_data.license_key
        
        db.session.add(user)
        db.session.commit()
        
        # Activate license
        self.auth_service.license_service.activate_license(license_data.license_key, str(user.id))
        
        self.logger.info(f"New OAuth user created: {email} via {provider}")
        return user
    
    def _generate_username_from_email(self, email: str) -> str:
        """Generate unique username from email."""
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    @handle_errors(ErrorCategory.AUTHENTICATION_ERROR)
    def unlink_oauth_provider(self, user: User) -> bool:
        """Unlink OAuth provider from user account."""
        if not user.oauth_provider:
            raise ValueError("User does not have linked OAuth provider")
        
        # Ensure user has a password set before unlinking
        if not user.password_hash:
            raise ValueError("Cannot unlink OAuth provider without setting a password first")
        
        user.oauth_provider = None
        user.oauth_provider_id = None
        user.avatar_url = None
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        self.logger.info(f"OAuth provider unlinked for user: {user.email}")
        return True
    
    def cleanup_expired_states(self) -> int:
        """Clean up expired OAuth states."""
        states = current_app.config.get('OAUTH_STATES', {})
        expired_count = 0
        current_time = datetime.utcnow()
        
        expired_states = [
            state for state, data in states.items()
            if current_time - data['created_at'] > timedelta(minutes=10)
        ]
        
        for state in expired_states:
            del states[state]
            expired_count += 1
        
        if expired_count > 0:
            self.logger.info(f"Cleaned up {expired_count} expired OAuth states")
        
        return expired_count