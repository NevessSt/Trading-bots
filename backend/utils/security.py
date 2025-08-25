import os
import hashlib
import secrets
import shutil
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from collections import defaultdict
import time

class SecurityManager:
    """Handles security operations for the trading bot"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.rate_limit_storage = defaultdict(list)
        self.failed_attempts = defaultdict(int)
        self.blocked_ips = set()
    
    def _get_or_create_encryption_key(self):
        """Get or create encryption key for API keys"""
        key_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'encryption.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_api_key(self, api_key):
        """Encrypt API key for storage
        
        Args:
            api_key (str): Plain text API key
            
        Returns:
            str: Encrypted API key
        """
        if not api_key:
            return None
        return self.cipher_suite.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key):
        """Decrypt API key for use
        
        Args:
            encrypted_key (str): Encrypted API key
            
        Returns:
            str: Plain text API key
        """
        if not encrypted_key:
            return None
        try:
            return self.cipher_suite.decrypt(encrypted_key.encode()).decode()
        except Exception:
            return None
    
    def validate_api_key_format(self, api_key, exchange):
        """Validate API key format for different exchanges
        
        Args:
            api_key (str): API key to validate
            exchange (str): Exchange name
            
        Returns:
            bool: True if format is valid
        """
        if not api_key or len(api_key.strip()) < 10:
            return False
        
        # Basic format validation for different exchanges
        exchange = exchange.lower()
        
        if exchange == 'binance':
            # Binance API keys are typically 64 characters long
            return len(api_key) >= 60 and api_key.isalnum()
        elif exchange == 'coinbase':
            # Coinbase Pro API keys are typically UUID format
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            return bool(re.match(uuid_pattern, api_key, re.IGNORECASE))
        elif exchange == 'kraken':
            # Kraken API keys are base64 encoded
            return len(api_key) >= 50 and all(c.isalnum() or c in '+/=' for c in api_key)
        elif exchange == 'bitfinex':
            # Bitfinex API keys are typically 25+ characters
            return len(api_key) >= 25 and api_key.isalnum()
        else:
            # Generic validation for other exchanges
            return len(api_key) >= 20 and api_key.replace('-', '').replace('_', '').isalnum()
    
    def hash_password(self, password):
        """Hash password with salt
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: Hashed password
        """
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash
        
        Args:
            password (str): Plain text password
            hashed_password (str): Hashed password
            
        Returns:
            bool: True if password matches
        """
        try:
            salt, password_hash = hashed_password.split(':')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return new_hash.hex() == password_hash
        except Exception:
            return False
    
    def generate_secure_token(self, length=32):
        """Generate secure random token
        
        Args:
            length (int): Token length
            
        Returns:
            str: Secure token
        """
        return secrets.token_urlsafe(length)
    
    def is_rate_limited(self, identifier, max_requests=100, window_minutes=15):
        """Check if identifier is rate limited
        
        Args:
            identifier (str): IP address or user ID
            max_requests (int): Maximum requests allowed
            window_minutes (int): Time window in minutes
            
        Returns:
            bool: True if rate limited
        """
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        # Clean old requests
        self.rate_limit_storage[identifier] = [
            req_time for req_time in self.rate_limit_storage[identifier]
            if req_time > window_start
        ]
        
        # Check if over limit
        if len(self.rate_limit_storage[identifier]) >= max_requests:
            return True
        
        # Add current request
        self.rate_limit_storage[identifier].append(now)
        return False
    
    def record_failed_attempt(self, identifier):
        """Record failed login attempt
        
        Args:
            identifier (str): IP address or user ID
        """
        self.failed_attempts[identifier] += 1
        
        # Block IP after 5 failed attempts
        if self.failed_attempts[identifier] >= 5:
            self.blocked_ips.add(identifier)
    
    def is_blocked(self, identifier):
        """Check if identifier is blocked
        
        Args:
            identifier (str): IP address or user ID
            
        Returns:
            bool: True if blocked
        """
        return identifier in self.blocked_ips
    
    def clear_failed_attempts(self, identifier):
        """Clear failed attempts for identifier
        
        Args:
            identifier (str): IP address or user ID
        """
        self.failed_attempts.pop(identifier, None)
    
    def validate_api_keys(self, api_key, api_secret):
        """Validate API key format
        
        Args:
            api_key (str): Binance API key
            api_secret (str): Binance API secret
            
        Returns:
            bool: True if valid format
        """
        if not api_key or not api_secret:
            return False
        
        # Basic format validation for Binance keys
        if len(api_key) != 64 or len(api_secret) != 64:
            return False
        
        # Check if keys contain only valid characters
        valid_chars = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
        if not all(c in valid_chars for c in api_key + api_secret):
            return False
        
        return True
    
    def sanitize_input(self, data):
        """Sanitize user input
        
        Args:
            data (str): Input data
            
        Returns:
            str: Sanitized data
        """
        if not isinstance(data, str):
            return data
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        for char in dangerous_chars:
            data = data.replace(char, '')
        
        return data.strip()

# Global security manager instance
security_manager = SecurityManager()

# Decorators for security
def rate_limit(max_requests=100, window_minutes=15):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # Check if blocked
            if security_manager.is_blocked(client_ip):
                return jsonify({'error': 'IP address blocked due to suspicious activity'}), 429
            
            # Check rate limit
            if security_manager.is_rate_limited(client_ip, max_requests, window_minutes):
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_api_keys():
    """Decorator to require valid API keys"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # Check if user has valid API keys
            from models.user import User
            user = User.find_by_id(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            api_key = user.get('binance_api_key')
            api_secret = user.get('binance_api_secret')
            
            if not api_key or not api_secret:
                return jsonify({'error': 'Binance API keys not configured'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required():
    """Decorator to require admin privileges"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            from models.user import User
            user = User.find_by_id(user_id)
            if not user or user.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Utility functions for API key and data security
def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)


def hash_api_secret(secret):
    """Hash an API secret using SHA-256"""
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_api_secret(secret, hashed_secret):
    """Verify an API secret against its hash"""
    return hash_api_secret(secret) == hashed_secret


def encrypt_sensitive_data(data):
    """Encrypt sensitive data using Fernet encryption"""
    if isinstance(data, str):
        data = data.encode()
    
    # Get or create encryption key
    key_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'encryption.key')
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
    
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(data).decode()


def decrypt_sensitive_data(encrypted_data):
    """Decrypt sensitive data using Fernet encryption"""
    if isinstance(encrypted_data, str):
        encrypted_data = encrypted_data.encode()
    
    # Get encryption key
    key_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'encryption.key')
    if not os.path.exists(key_file):
        raise ValueError("Encryption key not found")
    
    with open(key_file, 'rb') as f:
        key = f.read()
    
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_data).decode()


def rotate_encryption_key():
    """Rotate the encryption key and re-encrypt all sensitive data"""
    from models.user import User
    from models.api_key import APIKey
    
    # Generate new key
    new_key = Fernet.generate_key()
    key_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'encryption.key')
    backup_key_file = key_file + '.backup'
    
    # Backup old key
    if os.path.exists(key_file):
        shutil.copy2(key_file, backup_key_file)
        
        # Get old key
        with open(key_file, 'rb') as f:
            old_key = f.read()
        old_cipher = Fernet(old_key)
        
        # Re-encrypt all API keys
        try:
            api_keys = APIKey.find_all()
            new_cipher = Fernet(new_key)
            
            for api_key in api_keys:
                if api_key.get('encrypted_secret'):
                    # Decrypt with old key
                    decrypted_secret = old_cipher.decrypt(api_key['encrypted_secret'].encode())
                    # Encrypt with new key
                    new_encrypted_secret = new_cipher.encrypt(decrypted_secret).decode()
                    # Update in database
                    APIKey.update_by_id(api_key['_id'], {'encrypted_secret': new_encrypted_secret})
            
            # Save new key
            with open(key_file, 'wb') as f:
                f.write(new_key)
                
            logger.info("Encryption key rotated successfully")
            return True
            
        except Exception as e:
            # Restore backup on failure
            if os.path.exists(backup_key_file):
                shutil.copy2(backup_key_file, key_file)
            logger.error(f"Key rotation failed: {str(e)}")
            raise
    else:
        # First time setup
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(new_key)
        return True


def audit_log(user_id, action, details=None, ip_address=None, user_agent=None):
    """Enhanced audit logging for security events"""
    from models.audit_log import AuditLog
    from datetime import datetime
    
    log_entry = {
        'user_id': user_id,
        'action': action,
        'details': details or {},
        'ip_address': ip_address,
        'user_agent': user_agent,
        'timestamp': datetime.utcnow(),
        'severity': get_action_severity(action)
    }
    
    try:
        AuditLog.create(log_entry)
        
        # Log critical actions to file as well
        if log_entry['severity'] in ['high', 'critical']:
            logger.warning(f"Security Event - User: {user_id}, Action: {action}, IP: {ip_address}")
            
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")


def get_action_severity(action):
    """Determine severity level for audit actions"""
    critical_actions = ['login_failed_multiple', 'api_key_compromised', 'unauthorized_access']
    high_actions = ['login_success', 'api_key_created', 'api_key_deleted', 'password_changed']
    medium_actions = ['bot_created', 'bot_started', 'bot_stopped', 'trade_executed']
    
    if action in critical_actions:
        return 'critical'
    elif action in high_actions:
        return 'high'
    elif action in medium_actions:
        return 'medium'
    else:
        return 'low'


def check_ip_whitelist(ip_address, user_id):
    """Check if IP address is whitelisted for user"""
    from models.user import User
    
    try:
        user = User.find_by_id(user_id)
        if not user:
            return False
            
        # Get user's IP whitelist
        whitelist = user.get('security_settings', {}).get('ip_whitelist', [])
        
        # If no whitelist configured, allow all IPs
        if not whitelist:
            return True
            
        # Check if IP is in whitelist (supports CIDR notation)
        import ipaddress
        user_ip = ipaddress.ip_address(ip_address)
        
        for allowed_ip in whitelist:
            try:
                if '/' in allowed_ip:
                    # CIDR notation
                    if user_ip in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                else:
                    # Single IP
                    if user_ip == ipaddress.ip_address(allowed_ip):
                        return True
            except ValueError:
                continue
                
        return False
        
    except Exception as e:
        logger.error(f"IP whitelist check failed: {str(e)}")
        return True  # Allow on error to prevent lockout


def generate_secure_token(length=32):
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def validate_password_strength(password):
    """Validate password strength and return requirements"""
    requirements = {
        'length': len(password) >= 8,
        'uppercase': any(c.isupper() for c in password),
        'lowercase': any(c.islower() for c in password),
        'digit': any(c.isdigit() for c in password),
        'special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    }
    
    is_strong = all(requirements.values())
    
    return {
        'is_strong': is_strong,
        'requirements': requirements,
        'missing': [req for req, met in requirements.items() if not met]
    }


def detect_suspicious_activity(user_id, action, ip_address=None):
    """Detect suspicious user activity patterns"""
    from models.audit_log import AuditLog
    from datetime import datetime, timedelta
    
    suspicious_indicators = []
    
    try:
        # Check for multiple failed logins
        if action == 'login_failed':
            recent_failures = AuditLog.count({
                'user_id': user_id,
                'action': 'login_failed',
                'timestamp': {'$gte': datetime.utcnow() - timedelta(minutes=15)}
            })
            
            if recent_failures >= 3:
                suspicious_indicators.append('multiple_failed_logins')
        
        # Check for logins from new IPs
        if action == 'login_success' and ip_address:
            recent_ips = AuditLog.find({
                'user_id': user_id,
                'action': 'login_success',
                'timestamp': {'$gte': datetime.utcnow() - timedelta(days=30)}
            }, {'ip_address': 1})
            
            known_ips = {log.get('ip_address') for log in recent_ips if log.get('ip_address')}
            
            if ip_address not in known_ips:
                suspicious_indicators.append('new_ip_login')
        
        # Check for rapid API key creation/deletion
        if action in ['api_key_created', 'api_key_deleted']:
            recent_api_actions = AuditLog.count({
                'user_id': user_id,
                'action': {'$in': ['api_key_created', 'api_key_deleted']},
                'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=1)}
            })
            
            if recent_api_actions >= 5:
                suspicious_indicators.append('rapid_api_key_changes')
        
        return suspicious_indicators
        
    except Exception as e:
        logger.error(f"Suspicious activity detection failed: {str(e)}")
        return []