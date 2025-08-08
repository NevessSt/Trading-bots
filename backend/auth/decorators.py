from functools import wraps
from flask import request, jsonify, current_app
from auth.jwt_auth import jwt_auth
from models.user import User

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Verify token
        payload = jwt_auth.verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Get user from database
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Add user to request context
        request.current_user = user
        request.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        
        if request.current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

def subscription_required(plan_level='pro'):
    """Decorator to require specific subscription level"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user = request.current_user
            
            # Check if user has active subscription
            if not user.subscription or not user.subscription.is_active:
                return jsonify({
                    'error': 'Active subscription required',
                    'required_plan': plan_level
                }), 402  # Payment Required
            
            # Check subscription level
            plan_hierarchy = {'free': 0, 'pro': 1, 'enterprise': 2}
            user_level = plan_hierarchy.get(user.subscription.plan, 0)
            required_level = plan_hierarchy.get(plan_level, 1)
            
            if user_level < required_level:
                return jsonify({
                    'error': f'{plan_level.title()} subscription required',
                    'current_plan': user.subscription.plan,
                    'required_plan': plan_level
                }), 402
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def rate_limit_required(max_requests=100, window=3600):
    """Decorator to apply rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from .rate_limiter import rate_limiter
            
            # Get user identifier
            if hasattr(request, 'current_user'):
                identifier = f"user_{request.current_user.id}"
            else:
                identifier = request.remote_addr
            
            # Check rate limit
            if not rate_limiter.is_allowed(identifier, max_requests, window):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator