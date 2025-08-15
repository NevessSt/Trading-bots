#!/usr/bin/env python3
"""
User Management System for TradingBot Pro
Handles user roles, permissions, account management, and access control
"""

from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from enum import Enum
import jwt
import logging
from typing import Dict, List, Optional, Set
import re
import sqlite3
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from functools import wraps
import json
from contextlib import contextmanager

class UserRole(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    PREMIUM = "premium"
    BASIC = "basic"
    TRIAL = "trial"
    SUSPENDED = "suspended"

class Permission(Enum):
    # Trading permissions
    CREATE_STRATEGY = "create_strategy"
    DELETE_STRATEGY = "delete_strategy"
    MODIFY_STRATEGY = "modify_strategy"
    START_TRADING = "start_trading"
    STOP_TRADING = "stop_trading"
    
    # API permissions
    ADD_API_KEY = "add_api_key"
    DELETE_API_KEY = "delete_api_key"
    VIEW_API_KEYS = "view_api_keys"
    
    # Account permissions
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    MODIFY_SETTINGS = "modify_settings"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    MODIFY_SYSTEM_CONFIG = "modify_system_config"
    
    # Limits
    UNLIMITED_STRATEGIES = "unlimited_strategies"
    UNLIMITED_API_KEYS = "unlimited_api_keys"
    PRIORITY_SUPPORT = "priority_support"

class UserManager:
    def __init__(self, app=None, db_path='users.db'):
        self.app = app
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.role_permissions = self._initialize_role_permissions()
        self.rate_limits = self._initialize_rate_limits()
        self._lock = threading.Lock()
        
        # Initialize database
        self._init_database()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        app.config.setdefault('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        app.config.setdefault('JWT_EXPIRATION_DELTA', timedelta(hours=24))
        app.config.setdefault('PASSWORD_MIN_LENGTH', 8)
        app.config.setdefault('MAX_LOGIN_ATTEMPTS', 5)
        app.config.setdefault('LOCKOUT_DURATION', timedelta(minutes=30))
        app.config.setdefault('SMTP_SERVER', 'smtp.gmail.com')
        app.config.setdefault('SMTP_PORT', 587)
        app.config.setdefault('SMTP_USERNAME', '')
        app.config.setdefault('SMTP_PASSWORD', '')
        app.config.setdefault('FROM_EMAIL', 'noreply@tradingbot.com')
        
        self.jwt_secret = app.config['JWT_SECRET_KEY']
        self.smtp_config = {
            'server': app.config['SMTP_SERVER'],
            'port': app.config['SMTP_PORT'],
            'username': app.config['SMTP_USERNAME'],
            'password': app.config['SMTP_PASSWORD'],
            'from_email': app.config['FROM_EMAIL']
        }
    
    def _initialize_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """Initialize role-based permissions"""
        return {
            UserRole.ADMIN: {
                Permission.CREATE_STRATEGY, Permission.DELETE_STRATEGY, Permission.MODIFY_STRATEGY,
                Permission.START_TRADING, Permission.STOP_TRADING,
                Permission.ADD_API_KEY, Permission.DELETE_API_KEY, Permission.VIEW_API_KEYS,
                Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA, Permission.MODIFY_SETTINGS,
                Permission.MANAGE_USERS, Permission.VIEW_SYSTEM_LOGS, Permission.MODIFY_SYSTEM_CONFIG,
                Permission.UNLIMITED_STRATEGIES, Permission.UNLIMITED_API_KEYS, Permission.PRIORITY_SUPPORT
            },
            UserRole.MODERATOR: {
                Permission.CREATE_STRATEGY, Permission.DELETE_STRATEGY, Permission.MODIFY_STRATEGY,
                Permission.START_TRADING, Permission.STOP_TRADING,
                Permission.ADD_API_KEY, Permission.DELETE_API_KEY, Permission.VIEW_API_KEYS,
                Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA, Permission.MODIFY_SETTINGS,
                Permission.VIEW_SYSTEM_LOGS, Permission.UNLIMITED_STRATEGIES, Permission.PRIORITY_SUPPORT
            },
            UserRole.PREMIUM: {
                Permission.CREATE_STRATEGY, Permission.DELETE_STRATEGY, Permission.MODIFY_STRATEGY,
                Permission.START_TRADING, Permission.STOP_TRADING,
                Permission.ADD_API_KEY, Permission.DELETE_API_KEY, Permission.VIEW_API_KEYS,
                Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA, Permission.MODIFY_SETTINGS,
                Permission.UNLIMITED_STRATEGIES, Permission.PRIORITY_SUPPORT
            },
            UserRole.BASIC: {
                Permission.CREATE_STRATEGY, Permission.DELETE_STRATEGY, Permission.MODIFY_STRATEGY,
                Permission.START_TRADING, Permission.STOP_TRADING,
                Permission.ADD_API_KEY, Permission.DELETE_API_KEY, Permission.VIEW_API_KEYS,
                Permission.VIEW_ANALYTICS, Permission.MODIFY_SETTINGS
            },
            UserRole.TRIAL: {
                Permission.CREATE_STRATEGY, Permission.MODIFY_STRATEGY,
                Permission.START_TRADING, Permission.STOP_TRADING,
                Permission.ADD_API_KEY, Permission.VIEW_API_KEYS,
                Permission.VIEW_ANALYTICS
            },
            UserRole.SUSPENDED: set()  # No permissions
        }
    
    def _initialize_rate_limits(self) -> Dict[UserRole, Dict[str, int]]:
        """Initialize rate limits per role"""
        return {
            UserRole.ADMIN: {
                'api_requests_per_minute': 1000,
                'strategies_limit': -1,  # Unlimited
                'api_keys_limit': -1,    # Unlimited
                'concurrent_trades': -1   # Unlimited
            },
            UserRole.MODERATOR: {
                'api_requests_per_minute': 500,
                'strategies_limit': -1,
                'api_keys_limit': 20,
                'concurrent_trades': 50
            },
            UserRole.PREMIUM: {
                'api_requests_per_minute': 300,
                'strategies_limit': -1,
                'api_keys_limit': 10,
                'concurrent_trades': 20
            },
            UserRole.BASIC: {
                'api_requests_per_minute': 100,
                'strategies_limit': 5,
                'api_keys_limit': 3,
                'concurrent_trades': 5
            },
            UserRole.TRIAL: {
                'api_requests_per_minute': 50,
                'strategies_limit': 1,
                'api_keys_limit': 1,
                'concurrent_trades': 1
            },
            UserRole.SUSPENDED: {
                'api_requests_per_minute': 0,
                'strategies_limit': 0,
                'api_keys_limit': 0,
                'concurrent_trades': 0
            }
        }
    
    def create_user(self, username: str, email: str, password: str, role: UserRole = UserRole.TRIAL) -> Dict:
        """Create a new user account"""
        try:
            # Validate input
            if not self._validate_username(username):
                return {'success': False, 'error': 'Invalid username format'}
            
            if not self._validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            if not self._validate_password(password):
                return {'success': False, 'error': 'Password does not meet requirements'}
            
            # Check if user already exists
            if self._user_exists(username, email):
                return {'success': False, 'error': 'User already exists'}
            
            # Create user
            user_data = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                'role': role.value,
                'created_at': datetime.utcnow(),
                'last_login': None,
                'is_active': True,
                'email_verified': False,
                'failed_login_attempts': 0,
                'locked_until': None,
                'subscription_status': 'trial' if role == UserRole.TRIAL else 'active',
                'subscription_expires': datetime.utcnow() + timedelta(days=7) if role == UserRole.TRIAL else None
            }
            
            user_id = self._save_user(user_data)
            
            # Send verification email
            self._send_verification_email(user_id, email)
            
            self.logger.info(f"User created: {username} ({email}) with role {role.value}")
            
            return {
                'success': True,
                'user_id': user_id,
                'message': 'User created successfully. Please check your email for verification.'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create user {username}: {e}")
            return {'success': False, 'error': 'Failed to create user'}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user login"""
        try:
            user = self._get_user_by_username(username)
            if not user:
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Check if account is locked
            if self._is_account_locked(user):
                return {'success': False, 'error': 'Account temporarily locked due to failed login attempts'}
            
            # Check if account is suspended
            if user['role'] == UserRole.SUSPENDED.value:
                return {'success': False, 'error': 'Account suspended'}
            
            # Verify password
            if not check_password_hash(user['password_hash'], password):
                self._record_failed_login(user['id'])
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Check subscription status
            if not self._is_subscription_active(user):
                return {'success': False, 'error': 'Subscription expired'}
            
            # Generate JWT token
            token = self._generate_jwt_token(user)
            
            # Update last login
            self._update_last_login(user['id'])
            
            # Reset failed login attempts
            self._reset_failed_login_attempts(user['id'])
            
            self.logger.info(f"User authenticated: {username}")
            
            return {
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'subscription_status': user['subscription_status']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Authentication failed for {username}: {e}")
            return {'success': False, 'error': 'Authentication failed'}
    
    def has_permission(self, user_id: int, permission: Permission) -> bool:
        """Check if user has specific permission"""
        try:
            user = self._get_user_by_id(user_id)
            if not user or not user['is_active']:
                return False
            
            user_role = UserRole(user['role'])
            return permission in self.role_permissions.get(user_role, set())
            
        except Exception as e:
            self.logger.error(f"Permission check failed for user {user_id}: {e}")
            return False
    
    def check_rate_limit(self, user_id: int, limit_type: str) -> bool:
        """Check if user is within rate limits"""
        try:
            user = self._get_user_by_id(user_id)
            if not user:
                return False
            
            user_role = UserRole(user['role'])
            limits = self.rate_limits.get(user_role, {})
            limit = limits.get(limit_type, 0)
            
            if limit == -1:  # Unlimited
                return True
            
            current_usage = self._get_current_usage(user_id, limit_type)
            return current_usage < limit
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed for user {user_id}: {e}")
            return False
    
    def update_user_role(self, user_id: int, new_role: UserRole, admin_id: int) -> bool:
        """Update user role (admin only)"""
        try:
            # Check if admin has permission
            if not self.has_permission(admin_id, Permission.MANAGE_USERS):
                return False
            
            # Update role
            success = self._update_user_role(user_id, new_role)
            
            if success:
                self.logger.info(f"User {user_id} role updated to {new_role.value} by admin {admin_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update user role: {e}")
            return False
    
    def suspend_user(self, user_id: int, reason: str, admin_id: int) -> bool:
        """Suspend user account"""
        try:
            if not self.has_permission(admin_id, Permission.MANAGE_USERS):
                return False
            
            success = self._update_user_role(user_id, UserRole.SUSPENDED)
            
            if success:
                self._log_user_action(user_id, 'suspended', reason, admin_id)
                self.logger.info(f"User {user_id} suspended by admin {admin_id}: {reason}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to suspend user: {e}")
            return False
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics and usage"""
        try:
            user = self._get_user_by_id(user_id)
            if not user:
                return {}
            
            user_role = UserRole(user['role'])
            limits = self.rate_limits.get(user_role, {})
            
            return {
                'user_id': user_id,
                'role': user_role.value,
                'subscription_status': user['subscription_status'],
                'account_created': user['created_at'],
                'last_login': user['last_login'],
                'limits': limits,
                'current_usage': {
                    'strategies': self._get_current_usage(user_id, 'strategies_limit'),
                    'api_keys': self._get_current_usage(user_id, 'api_keys_limit'),
                    'concurrent_trades': self._get_current_usage(user_id, 'concurrent_trades')
                },
                'permissions': [p.value for p in self.role_permissions.get(user_role, set())]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user stats: {e}")
            return {}
    
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'trial',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    email_verified BOOLEAN DEFAULT 0,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    subscription_status TEXT DEFAULT 'trial',
                    subscription_expires TIMESTAMP,
                    verification_token TEXT,
                    reset_token TEXT,
                    reset_token_expires TIMESTAMP
                )
            ''')
            
            # User sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # User actions log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    admin_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (admin_id) REFERENCES users (id)
                )
            ''')
            
            # Rate limiting table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    limit_type TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, limit_type)
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get user from JWT token in request
                token = request.headers.get('Authorization', '').replace('Bearer ', '')
                if not token:
                    return jsonify({'error': 'No token provided'}), 401
                
                try:
                    payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
                    user_id = payload['user_id']
                    
                    if not self.has_permission(user_id, permission):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                    
                    return f(*args, **kwargs)
                except jwt.ExpiredSignatureError:
                    return jsonify({'error': 'Token expired'}), 401
                except jwt.InvalidTokenError:
                    return jsonify({'error': 'Invalid token'}), 401
            
            return decorated_function
        return decorator
    
    # Helper methods
    def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True
    
    def _user_exists(self, username: str, email: str) -> bool:
        """Check if user already exists"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM users WHERE username = ? OR email = ?',
                (username, email)
            )
            return cursor.fetchone() is not None
    
    def _save_user(self, user_data: Dict) -> int:
        """Save user to database"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            user_data['verification_token'] = verification_token
            
            cursor.execute('''
                INSERT INTO users (
                    username, email, password_hash, role, created_at,
                    is_active, email_verified, subscription_status,
                    subscription_expires, verification_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['username'],
                user_data['email'],
                user_data['password_hash'],
                user_data['role'],
                user_data['created_at'],
                user_data['is_active'],
                user_data['email_verified'],
                user_data['subscription_status'],
                user_data['subscription_expires'],
                verification_token
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def _get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def _is_account_locked(self, user: Dict) -> bool:
        """Check if account is locked"""
        if user['locked_until'] and user['locked_until'] > datetime.utcnow():
            return True
        return False
    
    def _is_subscription_active(self, user: Dict) -> bool:
        """Check if subscription is active"""
        if user['subscription_expires'] and user['subscription_expires'] < datetime.utcnow():
            return False
        return user['subscription_status'] == 'active'
    
    def _generate_jwt_token(self, user: Dict) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def _update_last_login(self, user_id: int):
        """Update last login timestamp"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET last_login = ? WHERE id = ?',
                (datetime.utcnow(), user_id)
            )
            conn.commit()
    
    def _record_failed_login(self, user_id: int):
        """Record failed login attempt"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Increment failed attempts
            cursor.execute(
                'UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE id = ?',
                (user_id,)
            )
            
            # Check if should lock account
            cursor.execute('SELECT failed_login_attempts FROM users WHERE id = ?', (user_id,))
            attempts = cursor.fetchone()[0]
            
            if attempts >= 5:  # Lock after 5 failed attempts
                lock_until = datetime.utcnow() + timedelta(minutes=30)
                cursor.execute(
                    'UPDATE users SET locked_until = ? WHERE id = ?',
                    (lock_until, user_id)
                )
            
            conn.commit()
    
    def _reset_failed_login_attempts(self, user_id: int):
        """Reset failed login attempts"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?',
                (user_id,)
            )
            conn.commit()
    
    def _get_current_usage(self, user_id: int, limit_type: str) -> int:
        """Get current usage for limit type"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if we need to reset the window (for time-based limits)
            if 'per_minute' in limit_type:
                window_duration = timedelta(minutes=1)
            elif 'per_hour' in limit_type:
                window_duration = timedelta(hours=1)
            elif 'per_day' in limit_type:
                window_duration = timedelta(days=1)
            else:
                # For non-time-based limits, get actual count from other tables
                if limit_type == 'strategies_limit':
                    cursor.execute('SELECT COUNT(*) FROM strategies WHERE user_id = ?', (user_id,))
                elif limit_type == 'api_keys_limit':
                    cursor.execute('SELECT COUNT(*) FROM api_keys WHERE user_id = ?', (user_id,))
                elif limit_type == 'concurrent_trades':
                    cursor.execute('SELECT COUNT(*) FROM trades WHERE user_id = ? AND status = "active"', (user_id,))
                else:
                    return 0
                
                result = cursor.fetchone()
                return result[0] if result else 0
            
            # For time-based limits
            cursor.execute(
                'SELECT count, window_start FROM rate_limits WHERE user_id = ? AND limit_type = ?',
                (user_id, limit_type)
            )
            result = cursor.fetchone()
            
            if not result:
                return 0
            
            count, window_start = result
            window_start = datetime.fromisoformat(window_start)
            
            # Reset if window expired
            if datetime.utcnow() - window_start > window_duration:
                cursor.execute(
                    'UPDATE rate_limits SET count = 0, window_start = ? WHERE user_id = ? AND limit_type = ?',
                    (datetime.utcnow(), user_id, limit_type)
                )
                conn.commit()
                return 0
            
            return count
    
    def _update_user_role(self, user_id: int, role: UserRole) -> bool:
        """Update user role in database"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET role = ? WHERE id = ?',
                    (role.value, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Failed to update user role: {e}")
            return False
    
    def _log_user_action(self, user_id: int, action: str, reason: str, admin_id: int):
        """Log user action"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO user_actions (user_id, action, details, admin_id) VALUES (?, ?, ?, ?)',
                (user_id, action, reason, admin_id)
            )
            conn.commit()
    
    def _send_verification_email(self, user_id: int, email: str):
        """Send email verification"""
        try:
            # Get verification token
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT verification_token FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                if not result:
                    return
                
                verification_token = result[0]
            
            # Create verification link
            verification_link = f"http://localhost:5000/verify-email?token={verification_token}"
            
            # Create email content
            subject = "Verify Your TradingBot Pro Account"
            body = f"""
            Welcome to TradingBot Pro!
            
            Please click the link below to verify your email address:
            {verification_link}
            
            If you didn't create this account, please ignore this email.
            
            Best regards,
            TradingBot Pro Team
            """
            
            # Send email
            self._send_email(email, subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send verification email: {e}")
    
    def _send_email(self, to_email: str, subject: str, body: str):
        """Send email using SMTP"""
        try:
            if not self.smtp_config.get('username'):
                self.logger.warning("SMTP not configured, skipping email")
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.smtp_config['from_email'], to_email, text)
            server.quit()
            
            self.logger.info(f"Email sent to {to_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    def verify_email(self, token: str) -> bool:
        """Verify email with token"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET email_verified = 1, verification_token = NULL WHERE verification_token = ?',
                    (token,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Email verification failed: {e}")
            return False
    
    def request_password_reset(self, email: str) -> bool:
        """Request password reset"""
        try:
            user = self._get_user_by_email(email)
            if not user:
                return False
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.utcnow() + timedelta(hours=1)
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?',
                    (reset_token, reset_expires, user['id'])
                )
                conn.commit()
            
            # Send reset email
            reset_link = f"http://localhost:5000/reset-password?token={reset_token}"
            subject = "Password Reset - TradingBot Pro"
            body = f"""
            You requested a password reset for your TradingBot Pro account.
            
            Click the link below to reset your password:
            {reset_link}
            
            This link will expire in 1 hour.
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            TradingBot Pro Team
            """
            
            self._send_email(email, subject, body)
            return True
            
        except Exception as e:
            self.logger.error(f"Password reset request failed: {e}")
            return False
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token"""
        try:
            if not self._validate_password(new_password):
                return False
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT id FROM users WHERE reset_token = ? AND reset_token_expires > ?',
                    (token, datetime.utcnow())
                )
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                user_id = result[0]
                password_hash = generate_password_hash(new_password)
                
                cursor.execute(
                    'UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?',
                    (password_hash, user_id)
                )
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Password reset failed: {e}")
            return False
    
    def _get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def increment_rate_limit(self, user_id: int, limit_type: str):
        """Increment rate limit counter"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO rate_limits (user_id, limit_type, count, window_start) VALUES (?, ?, COALESCE((SELECT count FROM rate_limits WHERE user_id = ? AND limit_type = ?), 0) + 1, COALESCE((SELECT window_start FROM rate_limits WHERE user_id = ? AND limit_type = ?), ?))',
                (user_id, limit_type, user_id, limit_type, user_id, limit_type, datetime.utcnow())
            )
            conn.commit()
    
    def get_all_users(self, admin_id: int, page: int = 1, per_page: int = 50) -> Dict:
        """Get all users (admin only)"""
        if not self.has_permission(admin_id, Permission.MANAGE_USERS):
            return {'success': False, 'error': 'Insufficient permissions'}
        
        try:
            offset = (page - 1) * per_page
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute('SELECT COUNT(*) FROM users')
                total = cursor.fetchone()[0]
                
                # Get users
                cursor.execute(
                    'SELECT id, username, email, role, created_at, last_login, is_active, email_verified, subscription_status FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?',
                    (per_page, offset)
                )
                users = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'success': True,
                    'users': users,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get users: {e}")
            return {'success': False, 'error': 'Failed to retrieve users'}
    
    def delete_user(self, user_id: int, admin_id: int) -> bool:
        """Delete user account (admin only)"""
        if not self.has_permission(admin_id, Permission.MANAGE_USERS):
            return False
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Log the deletion
                self._log_user_action(user_id, 'deleted', 'Account deleted by admin', admin_id)
                
                # Delete user (cascade will handle related records)
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to delete user: {e}")
            return False

if __name__ == "__main__":
    user_manager = UserManager()
    print("User management system initialized")
    print(f"Available roles: {[role.value for role in UserRole]}")
    print(f"Available permissions: {[perm.value for perm in Permission]}")