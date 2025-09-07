#!/usr/bin/env python3
"""
Advanced Security Manager
Comprehensive API security with encryption, rate limiting, authentication, and secure key management
"""

import logging
import hashlib
import hmac
import secrets
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import bcrypt
import threading
from collections import defaultdict, deque
import ipaddress
import re
from functools import wraps
import os

class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuthenticationMethod(Enum):
    """Authentication methods"""
    API_KEY = "api_key"
    JWT_TOKEN = "jwt_token"
    OAUTH2 = "oauth2"
    TWO_FACTOR = "2fa"
    BIOMETRIC = "biometric"

@dataclass
class RateLimitRule:
    """Rate limiting rule"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10
    window_size: int = 60  # seconds
    penalty_duration: int = 300  # seconds

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    session_timeout: int = 3600  # 1 hour
    jwt_expiry: int = 1800  # 30 minutes
    refresh_token_expiry: int = 86400  # 24 hours
    require_2fa: bool = False
    allowed_ip_ranges: List[str] = field(default_factory=list)
    blocked_countries: List[str] = field(default_factory=list)
    encryption_algorithm: str = "AES-256-GCM"
    hash_algorithm: str = "SHA-256"

@dataclass
class APIKey:
    """API key information"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    permissions: List[str]
    rate_limit: RateLimitRule
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True
    usage_count: int = 0
    ip_whitelist: List[str] = field(default_factory=list)

@dataclass
class UserSession:
    """User session information"""
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    authentication_methods: List[AuthenticationMethod] = field(default_factory=list)

@dataclass
class SecurityEvent:
    """Security event for logging and monitoring"""
    event_id: str
    event_type: str
    severity: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    action_taken: str = ""

class EncryptionManager:
    """Advanced encryption and decryption manager"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.logger = logging.getLogger(__name__)
        
        # Generate or use provided master key
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = self._generate_master_key()
        
        # Initialize Fernet cipher
        self.cipher = Fernet(base64.urlsafe_b64encode(self.master_key[:32]))
        
        # Generate RSA key pair for asymmetric encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def _generate_master_key(self) -> bytes:
        """Generate a secure master key"""
        return secrets.token_bytes(32)
    
    def encrypt_symmetric(self, data: str) -> str:
        """Encrypt data using symmetric encryption"""
        try:
            encrypted_data = self.cipher.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Symmetric encryption failed: {e}")
            raise
    
    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Symmetric decryption failed: {e}")
            raise
    
    def encrypt_asymmetric(self, data: str) -> str:
        """Encrypt data using asymmetric encryption"""
        try:
            encrypted_data = self.public_key.encrypt(
                data.encode('utf-8'),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Asymmetric encryption failed: {e}")
            raise
    
    def decrypt_asymmetric(self, encrypted_data: str) -> str:
        """Decrypt data using asymmetric encryption"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted_data.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Asymmetric decryption failed: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Password hashing failed: {e}")
            raise
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self) -> Tuple[str, str]:
        """Generate API key pair (public key, secret)"""
        public_key = f"ak_{secrets.token_urlsafe(16)}"
        secret = secrets.token_urlsafe(32)
        return public_key, secret
    
    def sign_data(self, data: str, secret: str) -> str:
        """Sign data using HMAC-SHA256"""
        try:
            signature = hmac.new(
                secret.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
            self.logger.error(f"Data signing failed: {e}")
            raise
    
    def verify_signature(self, data: str, signature: str, secret: str) -> bool:
        """Verify data signature"""
        try:
            expected_signature = self.sign_data(data, secret)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            self.logger.error(f"Signature verification failed: {e}")
            return False

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_history = defaultdict(lambda: deque())
        self.blocked_ips = defaultdict(lambda: {'until': None, 'reason': ''})
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier: str, rule: RateLimitRule, ip_address: str = "") -> Tuple[bool, str]:
        """Check if request is allowed based on rate limiting rules"""
        try:
            with self.lock:
                current_time = time.time()
                
                # Check if IP is blocked
                if ip_address and ip_address in self.blocked_ips:
                    block_info = self.blocked_ips[ip_address]
                    if block_info['until'] and current_time < block_info['until']:
                        return False, f"IP blocked: {block_info['reason']}"
                    elif block_info['until'] and current_time >= block_info['until']:
                        # Unblock IP
                        del self.blocked_ips[ip_address]
                
                # Get request history for identifier
                history = self.request_history[identifier]
                
                # Remove old requests outside the window
                window_start = current_time - rule.window_size
                while history and history[0] < window_start:
                    history.popleft()
                
                # Check burst limit
                if len(history) >= rule.burst_limit:
                    return False, "Burst limit exceeded"
                
                # Check requests per minute
                minute_ago = current_time - 60
                minute_requests = sum(1 for t in history if t > minute_ago)
                if minute_requests >= rule.requests_per_minute:
                    return False, "Requests per minute limit exceeded"
                
                # Check requests per hour
                hour_ago = current_time - 3600
                hour_requests = sum(1 for t in history if t > hour_ago)
                if hour_requests >= rule.requests_per_hour:
                    return False, "Requests per hour limit exceeded"
                
                # Check requests per day
                day_ago = current_time - 86400
                day_requests = sum(1 for t in history if t > day_ago)
                if day_requests >= rule.requests_per_day:
                    return False, "Requests per day limit exceeded"
                
                # Add current request to history
                history.append(current_time)
                
                return True, "Request allowed"
                
        except Exception as e:
            self.logger.error(f"Rate limiting check failed: {e}")
            return False, "Rate limiting error"
    
    def block_ip(self, ip_address: str, duration: int, reason: str):
        """Block IP address for specified duration"""
        try:
            with self.lock:
                self.blocked_ips[ip_address] = {
                    'until': time.time() + duration,
                    'reason': reason
                }
                self.logger.warning(f"IP {ip_address} blocked for {duration}s: {reason}")
        except Exception as e:
            self.logger.error(f"Failed to block IP: {e}")
    
    def unblock_ip(self, ip_address: str):
        """Unblock IP address"""
        try:
            with self.lock:
                if ip_address in self.blocked_ips:
                    del self.blocked_ips[ip_address]
                    self.logger.info(f"IP {ip_address} unblocked")
        except Exception as e:
            self.logger.error(f"Failed to unblock IP: {e}")
    
    def get_rate_limit_status(self, identifier: str, rule: RateLimitRule) -> Dict[str, Any]:
        """Get current rate limit status for identifier"""
        try:
            with self.lock:
                current_time = time.time()
                history = self.request_history[identifier]
                
                # Count requests in different time windows
                minute_ago = current_time - 60
                hour_ago = current_time - 3600
                day_ago = current_time - 86400
                
                minute_requests = sum(1 for t in history if t > minute_ago)
                hour_requests = sum(1 for t in history if t > hour_ago)
                day_requests = sum(1 for t in history if t > day_ago)
                
                return {
                    'requests_per_minute': {
                        'current': minute_requests,
                        'limit': rule.requests_per_minute,
                        'remaining': max(0, rule.requests_per_minute - minute_requests)
                    },
                    'requests_per_hour': {
                        'current': hour_requests,
                        'limit': rule.requests_per_hour,
                        'remaining': max(0, rule.requests_per_hour - hour_requests)
                    },
                    'requests_per_day': {
                        'current': day_requests,
                        'limit': rule.requests_per_day,
                        'remaining': max(0, rule.requests_per_day - day_requests)
                    },
                    'burst_remaining': max(0, rule.burst_limit - len(history))
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get rate limit status: {e}")
            return {}

class SecurityManager:
    """Main security manager coordinating all security components"""
    
    def __init__(self, policy: SecurityPolicy, jwt_secret: Optional[str] = None):
        self.policy = policy
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.encryption = EncryptionManager()
        self.rate_limiter = RateLimiter()
        
        # JWT configuration
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.jwt_algorithm = "HS256"
        
        # Storage (in production, use proper database)
        self.api_keys = {}  # key_id -> APIKey
        self.user_sessions = {}  # session_id -> UserSession
        self.security_events = deque(maxlen=10000)  # Security event log
        self.failed_login_attempts = defaultdict(lambda: {'count': 0, 'last_attempt': None})
        
        # Thread safety
        self.lock = threading.Lock()
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against security policy"""
        errors = []
        
        if len(password) < self.policy.min_password_length:
            errors.append(f"Password must be at least {self.policy.min_password_length} characters long")
        
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.policy.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if self.policy.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def create_api_key(self, user_id: str, name: str, permissions: List[str], 
                      rate_limit: RateLimitRule, expires_in_days: Optional[int] = None) -> Tuple[str, str]:
        """Create new API key"""
        try:
            with self.lock:
                # Generate key pair
                key_id, secret = self.encryption.generate_api_key()
                
                # Hash the secret for storage
                key_hash = self.encryption.hash_password(secret)
                
                # Calculate expiry
                expires_at = None
                if expires_in_days:
                    expires_at = datetime.now() + timedelta(days=expires_in_days)
                
                # Create API key object
                api_key = APIKey(
                    key_id=key_id,
                    key_hash=key_hash,
                    user_id=user_id,
                    name=name,
                    permissions=permissions,
                    rate_limit=rate_limit,
                    created_at=datetime.now(),
                    expires_at=expires_at
                )
                
                # Store API key
                self.api_keys[key_id] = api_key
                
                # Log security event
                self._log_security_event(
                    "api_key_created",
                    "info",
                    user_id,
                    "",
                    "",
                    {"key_id": key_id, "name": name, "permissions": permissions}
                )
                
                self.logger.info(f"API key created: {key_id} for user {user_id}")
                return key_id, secret
                
        except Exception as e:
            self.logger.error(f"Failed to create API key: {e}")
            raise
    
    def validate_api_key(self, key_id: str, secret: str, ip_address: str = "") -> Tuple[bool, Optional[APIKey], str]:
        """Validate API key and secret"""
        try:
            with self.lock:
                # Check if key exists
                if key_id not in self.api_keys:
                    return False, None, "Invalid API key"
                
                api_key = self.api_keys[key_id]
                
                # Check if key is active
                if not api_key.is_active:
                    return False, None, "API key is disabled"
                
                # Check expiry
                if api_key.expires_at and datetime.now() > api_key.expires_at:
                    return False, None, "API key has expired"
                
                # Verify secret
                if not self.encryption.verify_password(secret, api_key.key_hash):
                    return False, None, "Invalid API key secret"
                
                # Check IP whitelist
                if api_key.ip_whitelist and ip_address:
                    ip_allowed = False
                    for allowed_ip in api_key.ip_whitelist:
                        try:
                            if ipaddress.ip_address(ip_address) in ipaddress.ip_network(allowed_ip, strict=False):
                                ip_allowed = True
                                break
                        except ValueError:
                            continue
                    
                    if not ip_allowed:
                        return False, None, "IP address not whitelisted"
                
                # Check rate limiting
                allowed, reason = self.rate_limiter.is_allowed(key_id, api_key.rate_limit, ip_address)
                if not allowed:
                    return False, None, f"Rate limit exceeded: {reason}"
                
                # Update usage statistics
                api_key.last_used = datetime.now()
                api_key.usage_count += 1
                
                return True, api_key, "API key validated successfully"
                
        except Exception as e:
            self.logger.error(f"API key validation failed: {e}")
            return False, None, "Validation error"
    
    def create_jwt_token(self, user_id: str, permissions: List[str], 
                        security_level: SecurityLevel = SecurityLevel.MEDIUM) -> str:
        """Create JWT token"""
        try:
            now = datetime.utcnow()
            payload = {
                'user_id': user_id,
                'permissions': permissions,
                'security_level': security_level.value,
                'iat': now,
                'exp': now + timedelta(seconds=self.policy.jwt_expiry),
                'jti': secrets.token_urlsafe(16)  # JWT ID for revocation
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            self.logger.info(f"JWT token created for user {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"JWT token creation failed: {e}")
            raise
    
    def validate_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Additional validation can be added here (e.g., check revocation list)
            
            return True, payload, "Token validated successfully"
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
        except Exception as e:
            self.logger.error(f"JWT token validation failed: {e}")
            return False, None, "Token validation error"
    
    def create_user_session(self, user_id: str, ip_address: str, user_agent: str, 
                           security_level: SecurityLevel = SecurityLevel.MEDIUM) -> str:
        """Create user session"""
        try:
            with self.lock:
                session_id = self.encryption.generate_secure_token()
                
                session = UserSession(
                    session_id=session_id,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=datetime.now(),
                    last_activity=datetime.now(),
                    expires_at=datetime.now() + timedelta(seconds=self.policy.session_timeout),
                    security_level=security_level
                )
                
                self.user_sessions[session_id] = session
                
                # Log security event
                self._log_security_event(
                    "session_created",
                    "info",
                    user_id,
                    ip_address,
                    user_agent,
                    {"session_id": session_id, "security_level": security_level.value}
                )
                
                self.logger.info(f"User session created: {session_id} for user {user_id}")
                return session_id
                
        except Exception as e:
            self.logger.error(f"Session creation failed: {e}")
            raise
    
    def validate_user_session(self, session_id: str, ip_address: str = "") -> Tuple[bool, Optional[UserSession], str]:
        """Validate user session"""
        try:
            with self.lock:
                if session_id not in self.user_sessions:
                    return False, None, "Invalid session"
                
                session = self.user_sessions[session_id]
                
                # Check if session is active
                if not session.is_active:
                    return False, None, "Session is disabled"
                
                # Check expiry
                if datetime.now() > session.expires_at:
                    session.is_active = False
                    return False, None, "Session has expired"
                
                # Check IP address (optional strict checking)
                if ip_address and session.ip_address != ip_address:
                    # Log suspicious activity
                    self._log_security_event(
                        "session_ip_mismatch",
                        "warning",
                        session.user_id,
                        ip_address,
                        "",
                        {"session_id": session_id, "original_ip": session.ip_address, "new_ip": ip_address}
                    )
                    # Optionally invalidate session for high security
                    if session.security_level == SecurityLevel.CRITICAL:
                        session.is_active = False
                        return False, None, "Session invalidated due to IP change"
                
                # Update last activity
                session.last_activity = datetime.now()
                
                return True, session, "Session validated successfully"
                
        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return False, None, "Session validation error"
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate user session"""
        try:
            with self.lock:
                if session_id in self.user_sessions:
                    self.user_sessions[session_id].is_active = False
                    self.logger.info(f"Session invalidated: {session_id}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Session invalidation failed: {e}")
            return False
    
    def check_ip_allowed(self, ip_address: str) -> Tuple[bool, str]:
        """Check if IP address is allowed based on policy"""
        try:
            # Check allowed IP ranges
            if self.policy.allowed_ip_ranges:
                ip_allowed = False
                for allowed_range in self.policy.allowed_ip_ranges:
                    try:
                        if ipaddress.ip_address(ip_address) in ipaddress.ip_network(allowed_range, strict=False):
                            ip_allowed = True
                            break
                    except ValueError:
                        continue
                
                if not ip_allowed:
                    return False, "IP address not in allowed ranges"
            
            # Additional IP checks can be added here (GeoIP, reputation, etc.)
            
            return True, "IP address allowed"
            
        except Exception as e:
            self.logger.error(f"IP check failed: {e}")
            return False, "IP check error"
    
    def record_failed_login(self, identifier: str, ip_address: str) -> bool:
        """Record failed login attempt and check if account should be locked"""
        try:
            with self.lock:
                current_time = datetime.now()
                
                # Update failed attempts
                attempts = self.failed_login_attempts[identifier]
                attempts['count'] += 1
                attempts['last_attempt'] = current_time
                
                # Check if account should be locked
                if attempts['count'] >= self.policy.max_login_attempts:
                    # Lock account
                    self.rate_limiter.block_ip(ip_address, self.policy.lockout_duration, "Too many failed login attempts")
                    
                    # Log security event
                    self._log_security_event(
                        "account_locked",
                        "warning",
                        identifier,
                        ip_address,
                        "",
                        {"failed_attempts": attempts['count']}
                    )
                    
                    self.logger.warning(f"Account locked: {identifier} after {attempts['count']} failed attempts")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to record login attempt: {e}")
            return False
    
    def reset_failed_login_attempts(self, identifier: str):
        """Reset failed login attempts for identifier"""
        try:
            with self.lock:
                if identifier in self.failed_login_attempts:
                    del self.failed_login_attempts[identifier]
        except Exception as e:
            self.logger.error(f"Failed to reset login attempts: {e}")
    
    def _log_security_event(self, event_type: str, severity: str, user_id: Optional[str], 
                           ip_address: str, user_agent: str, details: Dict[str, Any]):
        """Log security event"""
        try:
            event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details=details
            )
            
            self.security_events.append(event)
            
            # Log to file/database in production
            self.logger.info(f"Security event: {event_type} - {severity} - {user_id} - {ip_address}")
            
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
    
    def get_security_events(self, limit: int = 100, event_type: Optional[str] = None, 
                           severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get security events with optional filtering"""
        try:
            events = list(self.security_events)
            
            # Apply filters
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            if severity:
                events = [e for e in events if e.severity == severity]
            
            # Sort by timestamp (newest first) and limit
            events.sort(key=lambda x: x.timestamp, reverse=True)
            events = events[:limit]
            
            # Convert to dict format
            return [{
                'event_id': e.event_id,
                'event_type': e.event_type,
                'severity': e.severity,
                'user_id': e.user_id,
                'ip_address': e.ip_address,
                'user_agent': e.user_agent,
                'timestamp': e.timestamp.isoformat(),
                'details': e.details,
                'action_taken': e.action_taken
            } for e in events]
            
        except Exception as e:
            self.logger.error(f"Failed to get security events: {e}")
            return []
    
    def get_api_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key information (without sensitive data)"""
        try:
            if key_id in self.api_keys:
                api_key = self.api_keys[key_id]
                return {
                    'key_id': api_key.key_id,
                    'user_id': api_key.user_id,
                    'name': api_key.name,
                    'permissions': api_key.permissions,
                    'created_at': api_key.created_at.isoformat(),
                    'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
                    'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
                    'is_active': api_key.is_active,
                    'usage_count': api_key.usage_count,
                    'rate_limit_status': self.rate_limiter.get_rate_limit_status(key_id, api_key.rate_limit)
                }
            return None
        except Exception as e:
            self.logger.error(f"Failed to get API key info: {e}")
            return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key"""
        try:
            with self.lock:
                if key_id in self.api_keys:
                    self.api_keys[key_id].is_active = False
                    
                    # Log security event
                    self._log_security_event(
                        "api_key_revoked",
                        "info",
                        self.api_keys[key_id].user_id,
                        "",
                        "",
                        {"key_id": key_id}
                    )
                    
                    self.logger.info(f"API key revoked: {key_id}")
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to revoke API key: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of cleaned sessions"""
        try:
            with self.lock:
                current_time = datetime.now()
                expired_sessions = []
                
                for session_id, session in self.user_sessions.items():
                    if current_time > session.expires_at:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.user_sessions[session_id]
                
                if expired_sessions:
                    self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                return len(expired_sessions)
                
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {e}")
            return 0

# Decorator for API endpoint protection
def require_api_key(security_manager: SecurityManager, required_permissions: List[str] = None):
    """Decorator to require valid API key for endpoint access"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract API key from request (implementation depends on web framework)
            # This is a generic example
            
            try:
                # Get API key from headers (example)
                api_key_header = kwargs.get('api_key_header', '')
                if not api_key_header:
                    return {'error': 'API key required'}, 401
                
                # Parse API key
                try:
                    key_id, secret = api_key_header.split(':')
                except ValueError:
                    return {'error': 'Invalid API key format'}, 401
                
                # Validate API key
                ip_address = kwargs.get('ip_address', '')
                valid, api_key, message = security_manager.validate_api_key(key_id, secret, ip_address)
                
                if not valid:
                    return {'error': message}, 401
                
                # Check permissions
                if required_permissions:
                    for permission in required_permissions:
                        if permission not in api_key.permissions:
                            return {'error': f'Permission required: {permission}'}, 403
                
                # Add API key info to kwargs
                kwargs['api_key'] = api_key
                
                return func(*args, **kwargs)
                
            except Exception as e:
                security_manager.logger.error(f"API key validation error: {e}")
                return {'error': 'Authentication error'}, 500
        
        return wrapper
    return decorator

# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create security policy
    policy = SecurityPolicy(
        min_password_length=12,
        require_2fa=False,
        max_login_attempts=3,
        lockout_duration=300
    )
    
    # Create security manager
    security_manager = SecurityManager(policy)
    
    # Create rate limit rule
    rate_limit = RateLimitRule(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        burst_limit=10
    )
    
    # Create API key
    key_id, secret = security_manager.create_api_key(
        user_id="user123",
        name="Test API Key",
        permissions=["read", "write"],
        rate_limit=rate_limit,
        expires_in_days=30
    )
    
    print(f"Created API key: {key_id}")
    print(f"Secret: {secret}")
    
    # Validate API key
    valid, api_key, message = security_manager.validate_api_key(key_id, secret, "192.168.1.1")
    print(f"Validation result: {valid} - {message}")
    
    if valid:
        print(f"API key info: {security_manager.get_api_key_info(key_id)}")
    
    # Create JWT token
    jwt_token = security_manager.create_jwt_token("user123", ["read", "write"])
    print(f"JWT token: {jwt_token}")
    
    # Validate JWT token
    valid, payload, message = security_manager.validate_jwt_token(jwt_token)
    print(f"JWT validation: {valid} - {message}")
    if valid:
        print(f"JWT payload: {payload}")
    
    # Test encryption
    test_data = "Sensitive trading data: BTC position 1.5 @ $45000"
    encrypted = security_manager.encryption.encrypt_symmetric(test_data)
    decrypted = security_manager.encryption.decrypt_symmetric(encrypted)
    
    print(f"Original: {test_data}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    
    # Get security events
    events = security_manager.get_security_events(limit=10)
    print(f"Security events: {len(events)}")
    for event in events:
        print(f"  {event['timestamp']}: {event['event_type']} - {event['severity']}")