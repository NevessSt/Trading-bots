"""Security middleware for authentication and authorization."""

from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from functools import wraps
from typing import Optional, List
import time
from collections import defaultdict, deque

from models import User
from services.auth_service import AuthService
from services.license_service import Permission, LicenseType
from services.logging_service import get_logger, LogCategory
from services.error_handler import handle_errors, ErrorCategory


class SecurityMiddleware:
    """Middleware for handling security concerns."""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.logger = get_logger(LogCategory.SECURITY)
        
        # Rate limiting storage (in production, use Redis)
        self.rate_limit_storage = defaultdict(lambda: deque())
        self.failed_attempts = defaultdict(int)
        self.blocked_ips = set()
    
    def authenticate_request(self, f):
        """Decorator to authenticate requests using JWT or API key."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = None
            auth_method = None
            
            # Try JWT authentication first
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                auth_method = 'jwt'
                
                if not user:
                    return jsonify({'error': 'User not found'}), 401
                    
            except Exception:
                # Try API key authentication
                api_key = request.headers.get('X-API-Key')
                api_secret = request.headers.get('X-API-Secret')
                
                if api_key and api_secret:
                    user = self.auth_service.validate_api_key(api_key, api_secret)
                    auth_method = 'api_key'
                    
                    if not user:
                        self.logger.warning(f"Invalid API key from IP: {request.remote_addr}")
                        return jsonify({'error': 'Invalid API credentials'}), 401
                else:
                    return jsonify({'error': 'Authentication required'}), 401
            
            # Store user in request context
            g.current_user = user
            g.auth_method = auth_method
            
            # Log successful authentication
            self.logger.info(f"Request authenticated: {user.username} via {auth_method}")
            
            return f(*args, **kwargs)
        return decorated_function
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user') or not g.current_user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                if not self.auth_service.check_permission(g.current_user, permission):
                    self.logger.warning(
                        f"Permission denied: {g.current_user.username} - {permission.value}"
                    )
                    return jsonify({
                        'error': f'Permission required: {permission.value}',
                        'required_permission': permission.value
                    }), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def require_license_type(self, min_license_type: LicenseType):
        """Decorator to require minimum license type."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user') or not g.current_user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                license_info = self.auth_service.license_service.get_license_info(
                    g.current_user.license_key
                )
                
                if not license_info or license_info.license_type.value < min_license_type.value:
                    self.logger.warning(
                        f"License upgrade required: {g.current_user.username} - {min_license_type.value}"
                    )
                    return jsonify({
                        'error': f'License upgrade required: {min_license_type.value}',
                        'current_license': license_info.license_type.value if license_info else 'none',
                        'required_license': min_license_type.value
                    }), 402  # Payment Required
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def rate_limit(self, max_requests: int = 100, window_seconds: int = 3600):
        """Rate limiting decorator."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = request.remote_addr
                current_time = time.time()
                
                # Check if IP is blocked
                if client_ip in self.blocked_ips:
                    return jsonify({'error': 'IP address blocked'}), 429
                
                # Clean old requests
                requests = self.rate_limit_storage[client_ip]
                while requests and requests[0] < current_time - window_seconds:
                    requests.popleft()
                
                # Check rate limit
                if len(requests) >= max_requests:
                    self.failed_attempts[client_ip] += 1
                    
                    # Block IP after too many rate limit violations
                    if self.failed_attempts[client_ip] > 10:
                        self.blocked_ips.add(client_ip)
                        self.logger.warning(f"IP blocked due to rate limiting: {client_ip}")
                    
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': window_seconds
                    }), 429
                
                # Add current request
                requests.append(current_time)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def validate_content_type(self, allowed_types: List[str] = ['application/json']):
        """Validate request content type."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.method in ['POST', 'PUT', 'PATCH']:
                    content_type = request.content_type
                    if not content_type or not any(ct in content_type for ct in allowed_types):
                        return jsonify({
                            'error': 'Invalid content type',
                            'allowed_types': allowed_types
                        }), 400
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def log_request(self, f):
        """Log all requests for security monitoring."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Log request details
            self.logger.info(
                f"Request: {request.method} {request.path} from {request.remote_addr}"
            )
            
            try:
                response = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log response
                status_code = getattr(response, 'status_code', 200)
                self.logger.info(
                    f"Response: {status_code} in {duration:.3f}s"
                )
                
                return response
                
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(
                    f"Request failed: {str(e)} in {duration:.3f}s"
                )
                raise
                
        return decorated_function
    
    def validate_request_size(self, max_size_mb: int = 10):
        """Validate request payload size."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                content_length = request.content_length
                max_size_bytes = max_size_mb * 1024 * 1024
                
                if content_length and content_length > max_size_bytes:
                    return jsonify({
                        'error': 'Request payload too large',
                        'max_size_mb': max_size_mb
                    }), 413
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def cors_headers(self, f):
        """Add CORS headers for security."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add security headers
            if hasattr(response, 'headers'):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
        return decorated_function


# Global middleware instance
security_middleware = SecurityMiddleware()

# Convenience decorators
authenticate = security_middleware.authenticate_request
require_permission = security_middleware.require_permission
require_license_type = security_middleware.require_license_type
rate_limit = security_middleware.rate_limit
validate_content_type = security_middleware.validate_content_type
log_request = security_middleware.log_request
validate_request_size = security_middleware.validate_request_size
cors_headers = security_middleware.cors_headers