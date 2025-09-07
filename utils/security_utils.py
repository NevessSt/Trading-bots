"""Security utilities for trading bot operations.

This module provides encryption, API key management, authentication,
and other security-related functionality for the trading bot.
"""

import os
import hashlib
import hmac
import secrets
import base64
import json
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import jwt
import logging
from functools import wraps
import time
from threading import Lock

class SecurityError(Exception):
    """Security-related errors"""
    pass

@dataclass
class APICredentials:
    """Secure API credentials storage"""
    exchange: str
    api_key: str
    api_secret: str
    api_passphrase: Optional[str] = None
    sandbox: bool = True
    encrypted: bool = False
    created_at: datetime = None
    last_used: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert to dictionary, optionally excluding secrets"""
        data = {
            'exchange': self.exchange,
            'sandbox': self.sandbox,
            'encrypted': self.encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
        
        if include_secrets:
            data.update({
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                'api_passphrase': self.api_passphrase
            })
        else:
            # Only show partial key for identification
            data['api_key_preview'] = self.api_key[:8] + '...' if self.api_key else None
        
        return data

class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""
    
    def __init__(self, key: Optional[bytes] = None, key_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self._fernet = None
        
        if key:
            self._fernet = Fernet(key)
        elif key_file and Path(key_file).exists():
            with open(key_file, 'rb') as f:
                self._fernet = Fernet(f.read())
        else:
            # Generate new key
            self._generate_new_key(key_file)
    
    def _generate_new_key(self, key_file: Optional[str] = None):
        """Generate new encryption key"""
        key = Fernet.generate_key()
        self._fernet = Fernet(key)
        
        if key_file:
            # Save key to file
            key_path = Path(key_file)
            key_path.parent.mkdir(exist_ok=True)
            
            with open(key_path, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions (Unix-like systems)
            try:
                os.chmod(key_path, 0o600)
            except (OSError, AttributeError):
                pass  # Windows or permission error
            
            self.logger.info(f"New encryption key generated and saved to {key_file}")
    
    def encrypt(self, data: Union[str, bytes, Dict[str, Any]]) -> str:
        """Encrypt data and return base64 encoded string"""
        if not self._fernet:
            raise SecurityError("Encryption not initialized")
        
        # Convert to bytes if necessary
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self._fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> bytes:
        """Decrypt base64 encoded encrypted data"""
        if not self._fernet:
            raise SecurityError("Encryption not initialized")
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            return self._fernet.decrypt(encrypted_bytes)
        except Exception as e:
            raise SecurityError(f"Decryption failed: {e}")
    
    def decrypt_to_string(self, encrypted_data: str) -> str:
        """Decrypt and return as string"""
        return self.decrypt(encrypted_data).decode('utf-8')
    
    def decrypt_to_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt and return as dictionary"""
        decrypted_str = self.decrypt_to_string(encrypted_data)
        return json.loads(decrypted_str)

class APIKeyManager:
    """Secure API key management"""
    
    def __init__(self, encryption_manager: EncryptionManager, 
                 storage_file: str = "credentials.enc"):
        self.encryption_manager = encryption_manager
        self.storage_file = storage_file
        self.logger = logging.getLogger(__name__)
        self._credentials: Dict[str, APICredentials] = {}
        self._lock = Lock()
        
        # Load existing credentials
        self._load_credentials()
    
    def add_credentials(self, exchange: str, api_key: str, api_secret: str,
                      api_passphrase: Optional[str] = None, sandbox: bool = True) -> bool:
        """Add or update API credentials for an exchange"""
        try:
            with self._lock:
                credentials = APICredentials(
                    exchange=exchange.lower(),
                    api_key=api_key,
                    api_secret=api_secret,
                    api_passphrase=api_passphrase,
                    sandbox=sandbox,
                    encrypted=True
                )
                
                self._credentials[exchange.lower()] = credentials
                self._save_credentials()
                
                self.logger.info(f"API credentials added/updated for {exchange}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add credentials for {exchange}: {e}")
            return False
    
    def get_credentials(self, exchange: str) -> Optional[APICredentials]:
        """Get API credentials for an exchange"""
        with self._lock:
            credentials = self._credentials.get(exchange.lower())
            if credentials:
                credentials.last_used = datetime.utcnow()
                self._save_credentials()
            return credentials
    
    def remove_credentials(self, exchange: str) -> bool:
        """Remove API credentials for an exchange"""
        try:
            with self._lock:
                if exchange.lower() in self._credentials:
                    del self._credentials[exchange.lower()]
                    self._save_credentials()
                    self.logger.info(f"API credentials removed for {exchange}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to remove credentials for {exchange}: {e}")
            return False
    
    def list_exchanges(self) -> List[str]:
        """List all exchanges with stored credentials"""
        with self._lock:
            return list(self._credentials.keys())
    
    def get_credentials_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about stored credentials (without secrets)"""
        with self._lock:
            return {exchange: creds.to_dict(include_secrets=False) 
                   for exchange, creds in self._credentials.items()}
    
    def _load_credentials(self):
        """Load credentials from encrypted storage"""
        storage_path = Path(self.storage_file)
        if not storage_path.exists():
            return
        
        try:
            with open(storage_path, 'r') as f:
                encrypted_data = f.read()
            
            if encrypted_data.strip():
                decrypted_data = self.encryption_manager.decrypt_to_dict(encrypted_data)
                
                for exchange, cred_data in decrypted_data.items():
                    # Convert datetime strings back to datetime objects
                    if 'created_at' in cred_data and cred_data['created_at']:
                        cred_data['created_at'] = datetime.fromisoformat(cred_data['created_at'])
                    if 'last_used' in cred_data and cred_data['last_used']:
                        cred_data['last_used'] = datetime.fromisoformat(cred_data['last_used'])
                    
                    self._credentials[exchange] = APICredentials(**cred_data)
                
                self.logger.info(f"Loaded credentials for {len(self._credentials)} exchanges")
                
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
    
    def _save_credentials(self):
        """Save credentials to encrypted storage"""
        try:
            # Convert credentials to dictionary format
            data_to_encrypt = {}
            for exchange, credentials in self._credentials.items():
                data_to_encrypt[exchange] = credentials.to_dict(include_secrets=True)
            
            # Encrypt and save
            encrypted_data = self.encryption_manager.encrypt(data_to_encrypt)
            
            storage_path = Path(self.storage_file)
            storage_path.parent.mkdir(exist_ok=True)
            
            with open(storage_path, 'w') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            try:
                os.chmod(storage_path, 0o600)
            except (OSError, AttributeError):
                pass  # Windows or permission error
                
        except Exception as e:
            self.logger.error(f"Failed to save credentials: {e}")
            raise SecurityError(f"Failed to save credentials: {e}")

class JWTManager:
    """JWT token management for authentication"""
    
    def __init__(self, secret_key: str, algorithm: str = 'HS256', 
                 default_expiry_hours: int = 24):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.default_expiry_hours = default_expiry_hours
        self.logger = logging.getLogger(__name__)
    
    def generate_token(self, payload: Dict[str, Any], 
                      expiry_hours: Optional[int] = None) -> str:
        """Generate JWT token"""
        expiry_hours = expiry_hours or self.default_expiry_hours
        
        # Add standard claims
        now = datetime.utcnow()
        payload.update({
            'iat': now,  # Issued at
            'exp': now + timedelta(hours=expiry_hours),  # Expiration
            'nbf': now  # Not before
        })
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            return token
        except Exception as e:
            self.logger.error(f"Failed to generate JWT token: {e}")
            raise SecurityError(f"Token generation failed: {e}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise SecurityError(f"Invalid token: {e}")
    
    def refresh_token(self, token: str, new_expiry_hours: Optional[int] = None) -> str:
        """Refresh an existing token"""
        try:
            # Verify current token (ignoring expiration)
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm],
                               options={"verify_exp": False})
            
            # Remove old timing claims
            for claim in ['iat', 'exp', 'nbf']:
                payload.pop(claim, None)
            
            # Generate new token
            return self.generate_token(payload, new_expiry_hours)
            
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {e}")
            raise SecurityError(f"Token refresh failed: {e}")

class RateLimiter:
    """Rate limiting for API calls and other operations"""
    
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._lock = Lock()
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        with self._lock:
            now = time.time()
            
            # Initialize or clean old requests
            if key not in self._requests:
                self._requests[key] = []
            
            # Remove old requests outside the window
            cutoff_time = now - window_seconds
            self._requests[key] = [req_time for req_time in self._requests[key] 
                                 if req_time > cutoff_time]
            
            # Check if under limit
            if len(self._requests[key]) < max_requests:
                self._requests[key].append(now)
                return True
            
            return False
    
    def get_remaining_requests(self, key: str, max_requests: int, 
                             window_seconds: int) -> int:
        """Get number of remaining requests in current window"""
        with self._lock:
            if key not in self._requests:
                return max_requests
            
            now = time.time()
            cutoff_time = now - window_seconds
            
            # Count recent requests
            recent_requests = sum(1 for req_time in self._requests[key] 
                                if req_time > cutoff_time)
            
            return max(0, max_requests - recent_requests)
    
    def reset_limit(self, key: str):
        """Reset rate limit for a key"""
        with self._lock:
            self._requests.pop(key, None)

def rate_limit(max_requests: int, window_seconds: int, key_func: Optional[callable] = None):
    """Decorator for rate limiting function calls"""
    limiter = RateLimiter()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__module__}.{func.__name__}"
            
            if not limiter.is_allowed(key, max_requests, window_seconds):
                remaining = limiter.get_remaining_requests(key, max_requests, window_seconds)
                raise SecurityError(f"Rate limit exceeded for {key}. {remaining} requests remaining.")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        if not api_key or len(api_key) < 16:
            return False
        
        # Check for common patterns
        if api_key.lower() in ['test', 'demo', 'example', 'placeholder']:
            return False
        
        return True
    
    @staticmethod
    def validate_signature(message: str, signature: str, secret: str) -> bool:
        """Validate HMAC signature"""
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32)
        
        # Use PBKDF2 with SHA256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return base64.urlsafe_b64encode(key).decode('utf-8'), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: bytes) -> bool:
        """Verify password against hash"""
        try:
            expected_hash, _ = SecurityValidator.hash_password(password, salt)
            return hmac.compare_digest(hashed_password, expected_hash)
        except Exception:
            return False

# Global security instances
encryption_manager = None
api_key_manager = None
jwt_manager = None

def initialize_security(encryption_key_file: str = "encryption.key",
                       credentials_file: str = "credentials.enc",
                       jwt_secret: Optional[str] = None) -> tuple[EncryptionManager, APIKeyManager, JWTManager]:
    """Initialize security components"""
    global encryption_manager, api_key_manager, jwt_manager
    
    # Initialize encryption
    encryption_manager = EncryptionManager(key_file=encryption_key_file)
    
    # Initialize API key manager
    api_key_manager = APIKeyManager(encryption_manager, credentials_file)
    
    # Initialize JWT manager
    if not jwt_secret:
        jwt_secret = SecurityValidator.generate_secure_token()
    jwt_manager = JWTManager(jwt_secret)
    
    return encryption_manager, api_key_manager, jwt_manager

def get_api_credentials(exchange: str) -> Optional[APICredentials]:
    """Get API credentials for exchange"""
    if not api_key_manager:
        raise SecurityError("Security not initialized. Call initialize_security() first.")
    return api_key_manager.get_credentials(exchange)

def add_api_credentials(exchange: str, api_key: str, api_secret: str,
                       api_passphrase: Optional[str] = None, sandbox: bool = True) -> bool:
    """Add API credentials for exchange"""
    if not api_key_manager:
        raise SecurityError("Security not initialized. Call initialize_security() first.")
    return api_key_manager.add_credentials(exchange, api_key, api_secret, api_passphrase, sandbox)

def encrypt_data(data: Union[str, Dict[str, Any]]) -> str:
    """Encrypt data using global encryption manager"""
    if not encryption_manager:
        raise SecurityError("Security not initialized. Call initialize_security() first.")
    return encryption_manager.encrypt(data)

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using global encryption manager"""
    if not encryption_manager:
        raise SecurityError("Security not initialized. Call initialize_security() first.")
    return encryption_manager.decrypt_to_string(encrypted_data)