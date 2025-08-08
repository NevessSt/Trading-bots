from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from auth.jwt_auth import jwt_auth
from auth.decorators import token_required, rate_limit_required
from auth.validators import (
    validate_json_input, 
    USER_REGISTRATION_SCHEMA, 
    USER_LOGIN_SCHEMA,
    InputValidator
)
from models.user import User
from models.subscription import Subscription
from utils.logger import logger

auth_v2_bp = Blueprint('auth_v2', __name__, url_prefix='/api/v2/auth')

@auth_v2_bp.route('/register', methods=['POST'])
@rate_limit_required(max_requests=5, window=3600)  # 5 registrations per hour
@validate_json_input(USER_REGISTRATION_SCHEMA)
def register():
    """Register a new user with email verification"""
    try:
        data = request.validated_data
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'error': 'User with this email already exists'
            }), 409
        
        # Validate password strength
        password_validation = InputValidator.validate_password(data['password'])
        if not password_validation['valid']:
            return jsonify({
                'error': 'Password does not meet requirements',
                'details': password_validation['errors']
            }), 400
        
        # Hash password
        password_hash = jwt_auth.hash_password(data['password'])
        
        # Generate email verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Create user
        user_data = {
            'email': data['email'],
            'password_hash': password_hash,
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'verification_token': verification_token,
            'verification_token_expires': datetime.utcnow() + timedelta(hours=24)
        }
        
        user_id = User.create(user_data)
        if not user_id:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Send verification email
        if not _send_verification_email(data['email'], verification_token):
            current_app.logger.warning(f"Failed to send verification email to {data['email']}")
        
        # Log security event
        log_security_event('user_registered', str(user_id), {
            'email': data['email'],
            'ip_address': request.remote_addr
        })
        
        return jsonify({
            'message': 'User registered successfully. Please check your email for verification.',
            'user_id': str(user_id)
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_v2_bp.route('/verify-email', methods=['POST'])
@rate_limit_required(max_requests=10, window=3600)
def verify_email():
    """Verify user email with token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Verification token is required'}), 400
        
        # Find user with valid verification token
        user = User.query.filter(
            User.verification_token == token,
            User.verification_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            return jsonify({'error': 'Invalid or expired verification token'}), 400
        
        # Verify email
        user.is_verified = True
        
        # Remove verification token
        user.verification_token = None
        user.verification_token_expires = None
        user.save()
        
        # Log security event
        logger.log_security_event('email_verified', str(user.id), {
            'email': user.email,
            'ip_address': request.remote_addr
        })
        
        return jsonify({'message': 'Email verified successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({'error': 'Email verification failed'}), 500

@auth_v2_bp.route('/login', methods=['POST'])
@rate_limit_required(max_requests=10, window=3600)  # 10 login attempts per hour
@validate_json_input(USER_LOGIN_SCHEMA)
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = request.validated_data
        
        # Find user by email
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is locked
        if User.is_account_locked(user):
            return jsonify({
                'error': 'Account temporarily locked due to multiple failed login attempts'
            }), 423
        
        # Check if account is active
        if not user.get('is_active', True):
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Verify password
        if not jwt_auth.verify_password(data['password'], user['password_hash']):
            # Increment failed login attempts
            User.increment_login_attempts(str(user.id))
            
            # Log security event
            logger.log_security_event('login_failed', str(user.id), {
                'email': user.email,
                'ip_address': request.remote_addr,
                'reason': 'invalid_password'
            })
            
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if email is verified
        if not user.is_verified:
            return jsonify({
                'error': 'Please verify your email before logging in',
                'requires_verification': True
            }), 401
        
        # Reset login attempts and update last login
        user.login_attempts = 0
        user.last_login = datetime.utcnow()
        user.save()
        
        # Generate JWT tokens
        tokens = jwt_auth.generate_tokens(
            str(user.id),
            user.email,
            user.role or 'user'
        )
        
        # Get user subscription
        subscription = user.subscription
        
        # Log security event
        logger.log_security_event('login_successful', str(user.id), {
            'email': user.email,
            'ip_address': request.remote_addr
        })
        
        return jsonify({
            'message': 'Login successful',
            'tokens': tokens,
            'user': {
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role or 'user',
                'subscription': {
                    'plan': subscription.get('plan', 'free') if subscription else 'free',
                    'status': subscription.get('status', 'active') if subscription else 'active'
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_v2_bp.route('/refresh', methods=['POST'])
@rate_limit_required(max_requests=20, window=3600)
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Generate new tokens
        tokens = jwt_auth.refresh_access_token(refresh_token)
        if not tokens:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'tokens': tokens
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_v2_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout user (client should discard tokens)"""
    try:
        user = request.current_user
        
        # Log security event
        log_security_event('logout', str(user['_id']), {
            'email': user['email'],
            'ip_address': request.remote_addr
        })
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_v2_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get user profile information"""
    try:
        user = request.current_user
        subscription = User.get_subscription(str(user['_id']))
        
        # Get subscription features
        plan = subscription.get('plan', 'free') if subscription else 'free'
        features = Subscription.get_plan_features(plan)
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'role': user.get('role', 'user'),
                'is_verified': user.get('is_verified', False),
                'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
                'last_login': user.get('last_login').isoformat() if user.get('last_login') else None
            },
            'subscription': {
                'plan': plan,
                'status': subscription.get('status', 'active') if subscription else 'active',
                'features': features,
                'next_billing_date': subscription.get('next_billing_date').isoformat() if subscription and subscription.get('next_billing_date') else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to get profile'}), 500

@auth_v2_bp.route('/change-password', methods=['POST'])
@token_required
@rate_limit_required(max_requests=5, window=3600)
def change_password():
    """Change user password"""
    try:
        user = request.current_user
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        # Verify current password
        if not jwt_auth.verify_password(current_password, user['password_hash']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        password_validation = InputValidator.validate_password(new_password)
        if not password_validation['valid']:
            return jsonify({
                'error': 'New password does not meet requirements',
                'details': password_validation['errors']
            }), 400
        
        # Hash new password
        new_password_hash = jwt_auth.hash_password(new_password)
        
        # Update password
        user.password_hash = new_password_hash
        user.password_changed_at = datetime.utcnow()
        user.save()
        
        # Log security event
        log_security_event('password_changed', str(user.id), {
            'email': user.email,
            'ip_address': request.remote_addr
        })
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500

@auth_v2_bp.route('/resend-verification', methods=['POST'])
@rate_limit_required(max_requests=3, window=3600)
def resend_verification():
    """Resend email verification"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email or not InputValidator.validate_email(email):
            return jsonify({'error': 'Valid email is required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists
            return jsonify({'message': 'If the email exists, verification email has been sent'}), 200
        
        # Check if already verified
        if user.get('is_verified', False):
            return jsonify({'error': 'Email is already verified'}), 400
        
        # Generate new verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Update user with new token
        user.verification_token = verification_token
        user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
        user.save()
        
        # Send verification email
        _send_verification_email(email, verification_token)
        
        return jsonify({'message': 'Verification email sent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({'error': 'Failed to resend verification'}), 500

def _send_verification_email(email: str, token: str) -> bool:
    """Send email verification email"""
    try:
        smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_username = current_app.config.get('SMTP_USERNAME')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        
        if not smtp_username or not smtp_password:
            current_app.logger.warning("SMTP credentials not configured")
            return False
        
        # Create verification URL
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{base_url}/verify-email?token={token}"
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = "Verify Your Email - Trading Bot Platform"
        
        body = f"""
        <html>
        <body>
            <h2>Welcome to Trading Bot Platform!</h2>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        return False