import functools
import time
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta
from flask import request, jsonify, g, current_app
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, TooManyRequests
import jwt
from collections import defaultdict, deque
import logging
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger('security')

class EnhancedSecurityMiddleware:
    def __init__(self, app=None):
        self.app = app
        self.rate_limits = defaultdict(lambda: deque())
        self.blocked_ips = set()
        self.failed_attempts = defaultdict(int)
        self.suspicious_patterns = {
            'sql_injection': re.compile(r'(union|select|insert|update|delete|drop|create|alter|exec|script)', re.IGNORECASE),
            'xss': re.compile(r'(<script|javascript:|on\w+\s*=)', re.IGNORECASE),
            'path_traversal': re.compile(r'(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c)', re.IGNORECASE)
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Enhanced security checks before processing requests"""
        try:
            # Get client IP
            client_ip = self.get_client_ip()
            g.client_ip = client_ip
            
            # Check if IP is blocked
            if self.is_ip_blocked(client_ip):
                security_logger.warning(f"Blocked IP attempted access: {client_ip}")
                return jsonify({
                    'error': 'Access denied',
                    'message': 'Your IP has been temporarily blocked due to suspicious activity'
                }), 403
            
            # Rate limiting
            if not self.check_rate_limit(client_ip):
                security_logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.'
                }), 429
            
            # Content security validation
            security_issues = self.validate_request_security()
            if security_issues:
                security_logger.error(f"Security violation from {client_ip}: {security_issues}")
                self.record_security_violation(client_ip)
                return jsonify({
                    'error': 'Security violation detected',
                    'message': 'Request contains potentially malicious content'
                }), 400
            
            # API key validation for API endpoints
            if request.path.startswith('/api/'):
                auth_result = self.validate_authentication()
                if auth_result:
                    return auth_result
            
        except Exception as e:
            security_logger.error(f"Security middleware error: {str(e)}")
            return jsonify({
                'error': 'Security check failed',
                'message': 'Unable to process request due to security constraints'
            }), 500
    
    def after_request(self, response):
        """Security headers and logging after request"""
        try:
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Log request details for monitoring
            if hasattr(g, 'client_ip'):
                self.log_request_details(response)
            
            return response
        except Exception as e:
            security_logger.error(f"After request security error: {str(e)}")
            return response
    
    def get_client_ip(self) -> str:
        """Get the real client IP address"""
        # Check for forwarded headers (common in load balancers/proxies)
        forwarded_ips = [
            request.headers.get('X-Forwarded-For'),
            request.headers.get('X-Real-IP'),
            request.headers.get('CF-Connecting-IP'),  # Cloudflare
            request.environ.get('HTTP_X_FORWARDED_FOR'),
            request.environ.get('REMOTE_ADDR')
        ]
        
        for ip in forwarded_ips:
            if ip:
                # Handle comma-separated IPs (X-Forwarded-For can contain multiple IPs)
                return ip.split(',')[0].strip()
        
        return request.remote_addr or 'unknown'
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blocked list"""
        return ip in self.blocked_ips
    
    def check_rate_limit(self, ip: str, limit: int = 100, window: int = 3600) -> bool:
        """Enhanced rate limiting with sliding window"""
        now = time.time()
        
        # Clean old entries
        while self.rate_limits[ip] and self.rate_limits[ip][0] < now - window:
            self.rate_limits[ip].popleft()
        
        # Check if limit exceeded
        if len(self.rate_limits[ip]) >= limit:
            # Block IP if consistently exceeding limits
            if len(self.rate_limits[ip]) > limit * 2:
                self.block_ip_temporarily(ip)
            return False
        
        # Add current request
        self.rate_limits[ip].append(now)
        return True
    
    def validate_request_security(self) -> List[str]:
        """Comprehensive request security validation"""
        issues = []
        
        # Check request size
        if request.content_length and request.content_length > 10 * 1024 * 1024:  # 10MB limit
            issues.append('Request too large')
        
        # Validate content type for POST/PUT requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('Content-Type', '')
            allowed_types = ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                issues.append('Invalid content type')
        
        # Check for malicious patterns in URL
        url_to_check = request.url
        for pattern_name, pattern in self.suspicious_patterns.items():
            if pattern.search(url_to_check):
                issues.append(f'Suspicious {pattern_name} pattern in URL')
        
        # Check request data for malicious patterns
        try:
            if request.is_json and request.get_json():
                json_str = json.dumps(request.get_json())
                for pattern_name, pattern in self.suspicious_patterns.items():
                    if pattern.search(json_str):
                        issues.append(f'Suspicious {pattern_name} pattern in request data')
            
            elif request.form:
                form_str = str(dict(request.form))
                for pattern_name, pattern in self.suspicious_patterns.items():
                    if pattern.search(form_str):
                        issues.append(f'Suspicious {pattern_name} pattern in form data')
        except Exception as e:
            security_logger.warning(f"Error checking request data: {str(e)}")
        
        # Check for suspicious headers
        suspicious_headers = ['X-Forwarded-Host', 'X-Original-URL', 'X-Rewrite-URL']
        for header in suspicious_headers:
            if request.headers.get(header):
                issues.append(f'Suspicious header: {header}')
        
        return issues
    
    def validate_authentication(self) -> Optional[Tuple]:
        """Enhanced authentication validation"""
        auth_header = request.headers.get('Authorization')
        api_key = request.headers.get('X-API-Key')
        
        # Skip auth for public endpoints
        public_endpoints = ['/api/health', '/api/auth/login', '/api/auth/register']
        if any(request.path.startswith(endpoint) for endpoint in public_endpoints):
            return None
        
        # JWT Token validation
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(
                    token, 
                    current_app.config['JWT_SECRET_KEY'], 
                    algorithms=['HS256']
                )
                
                # Check token expiration
                if payload.get('exp', 0) < time.time():
                    return jsonify({'error': 'Token expired'}), 401
                
                # Store user info in g for use in views
                g.current_user_id = payload.get('user_id')
                g.current_user_email = payload.get('email')
                
                return None
                
            except jwt.InvalidTokenError as e:
                security_logger.warning(f"Invalid JWT token from {g.client_ip}: {str(e)}")
                self.record_failed_auth_attempt(g.client_ip)
                return jsonify({'error': 'Invalid token'}), 401
        
        # API Key validation
        elif api_key:
            if not self.validate_api_key(api_key):
                security_logger.warning(f"Invalid API key from {g.client_ip}")
                self.record_failed_auth_attempt(g.client_ip)
                return jsonify({'error': 'Invalid API key'}), 401
            return None
        
        # No valid authentication found
        return jsonify({'error': 'Authentication required'}), 401
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and existence"""
        # Basic format validation
        if not api_key or len(api_key) < 32:
            return False
        
        # Check if API key exists in database (implement based on your model)
        try:
            from models.api_key import APIKey
            key_obj = APIKey.query.filter_by(key_hash=hashlib.sha256(api_key.encode()).hexdigest()).first()
            if key_obj and key_obj.is_active:
                g.current_user_id = key_obj.user_id
                return True
        except Exception as e:
            security_logger.error(f"API key validation error: {str(e)}")
        
        return False
    
    def record_security_violation(self, ip: str):
        """Record security violations and take action"""
        self.failed_attempts[ip] += 1
        
        # Block IP after multiple violations
        if self.failed_attempts[ip] >= 5:
            self.block_ip_temporarily(ip)
            security_logger.error(f"IP {ip} blocked due to multiple security violations")
    
    def record_failed_auth_attempt(self, ip: str):
        """Record failed authentication attempts"""
        self.failed_attempts[f"auth_{ip}"] += 1
        
        # Block IP after multiple failed auth attempts
        if self.failed_attempts[f"auth_{ip}"] >= 10:
            self.block_ip_temporarily(ip)
            security_logger.error(f"IP {ip} blocked due to multiple failed authentication attempts")
    
    def block_ip_temporarily(self, ip: str, duration: int = 3600):
        """Temporarily block an IP address"""
        self.blocked_ips.add(ip)
        
        # Schedule unblocking (in a real implementation, use a proper task queue)
        def unblock_later():
            time.sleep(duration)
            self.blocked_ips.discard(ip)
            security_logger.info(f"IP {ip} unblocked after temporary ban")
        
        # In production, use Celery or similar for this
        import threading
        threading.Thread(target=unblock_later, daemon=True).start()
    
    def log_request_details(self, response):
        """Log request details for security monitoring"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'ip': g.client_ip,
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'status_code': response.status_code,
            'response_size': len(response.get_data()),
            'user_id': getattr(g, 'current_user_id', None)
        }
        
        # Log to security log file
        security_logger.info(f"Request: {json.dumps(log_data)}")
    
    def get_security_stats(self) -> Dict:
        """Get current security statistics"""
        return {
            'blocked_ips_count': len(self.blocked_ips),
            'active_rate_limits': len(self.rate_limits),
            'failed_attempts': dict(self.failed_attempts),
            'total_requests_last_hour': sum(
                len(requests) for requests in self.rate_limits.values()
            )
        }

# Decorator for additional endpoint-specific security
def require_secure_endpoint(f):
    """Decorator for endpoints requiring additional security"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Additional security checks for sensitive endpoints
        if request.method in ['POST', 'PUT', 'DELETE']:
            # Require CSRF token for state-changing operations
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token:
                return jsonify({'error': 'CSRF token required'}), 400
        
        # Check for admin-only endpoints
        if 'admin' in request.path and not getattr(g, 'is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Decorator for trading-specific security
def require_trading_security(f):
    """Decorator for trading endpoints with additional safety checks"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has valid license for trading
        if not getattr(g, 'has_valid_license', False):
            return jsonify({
                'error': 'Valid license required for trading operations'
            }), 403
        
        # Validate trading parameters
        if request.is_json:
            data = request.get_json()
            
            # Check for reasonable trade amounts
            if 'amount' in data:
                try:
                    amount = float(data['amount'])
                    if amount <= 0 or amount > 1000000:  # Reasonable limits
                        return jsonify({
                            'error': 'Invalid trade amount'
                        }), 400
                except (ValueError, TypeError):
                    return jsonify({
                        'error': 'Invalid amount format'
                    }), 400
            
            # Validate trading pairs
            if 'symbol' in data:
                symbol = data['symbol'].upper()
                # Basic symbol validation (extend as needed)
                if not re.match(r'^[A-Z]{3,10}[/\-][A-Z]{3,10}$', symbol):
                    return jsonify({
                        'error': 'Invalid trading symbol format'
                    }), 400
        
        return f(*args, **kwargs)
    return decorated_function