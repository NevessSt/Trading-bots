"""Sentry middleware for enhanced error tracking with trading context."""

import logging
from flask import request, g
from flask_jwt_extended import get_jwt_identity, jwt_required
from functools import wraps
from typing import Optional, Dict, Any

from utils.sentry_config import (
    set_user_context, 
    set_trading_context, 
    add_breadcrumb,
    capture_exception,
    capture_message
)

logger = logging.getLogger(__name__)

class SentryMiddleware:
    """Middleware to enhance Sentry error tracking with context."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Sentry middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """Set up Sentry context before each request."""
        try:
            # Add request breadcrumb
            add_breadcrumb(
                message=f"{request.method} {request.path}",
                category='http',
                level='info',
                data={
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'query_params': dict(request.args)
                }
            )
            
            # Set user context if JWT token is present
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    user_id = get_jwt_identity()
                    if user_id:
                        set_user_context(user_id)
                        add_breadcrumb(
                            message=f"User {user_id} authenticated",
                            category='auth',
                            level='info'
                        )
                except Exception:
                    # JWT validation might fail, that's okay
                    pass
            
            # Extract trading context from request
            self._extract_trading_context()
            
        except Exception as e:
            logger.warning(f"Error setting up Sentry context: {e}")
    
    def after_request(self, response):
        """Add response context after request processing."""
        try:
            # Add response breadcrumb
            add_breadcrumb(
                message=f"Response {response.status_code}",
                category='http',
                level='info' if response.status_code < 400 else 'warning',
                data={
                    'status_code': response.status_code,
                    'content_length': response.content_length
                }
            )
            
            # Capture slow requests as messages
            if hasattr(g, 'request_start_time'):
                import time
                duration = time.time() - g.request_start_time
                if duration > 5.0:  # Log requests taking more than 5 seconds
                    capture_message(
                        f"Slow request: {request.method} {request.path} took {duration:.2f}s",
                        level='warning',
                        duration=duration,
                        endpoint=request.endpoint,
                        method=request.method,
                        path=request.path
                    )
            
        except Exception as e:
            logger.warning(f"Error adding response context to Sentry: {e}")
        
        return response
    
    def teardown_request(self, exception):
        """Handle request teardown and exceptions."""
        if exception:
            # Capture the exception with full context
            capture_exception(
                exception,
                endpoint=request.endpoint,
                method=request.method,
                path=request.path,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
    
    def _extract_trading_context(self):
        """Extract trading-specific context from request."""
        try:
            # Extract from URL parameters
            bot_id = request.args.get('bot_id') or request.view_args.get('bot_id')
            exchange = request.args.get('exchange')
            symbol = request.args.get('symbol')
            
            # Extract from JSON body
            if request.is_json and request.json:
                json_data = request.json
                bot_id = bot_id or json_data.get('bot_id')
                exchange = exchange or json_data.get('exchange')
                symbol = symbol or json_data.get('symbol')
            
            # Set trading context if any trading-related data is found
            if bot_id or exchange or symbol:
                set_trading_context(
                    bot_id=bot_id,
                    exchange=exchange,
                    symbol=symbol
                )
                
                add_breadcrumb(
                    message="Trading context extracted",
                    category='trading',
                    level='info',
                    data={
                        'bot_id': bot_id,
                        'exchange': exchange,
                        'symbol': symbol
                    }
                )
        
        except Exception as e:
            logger.warning(f"Error extracting trading context: {e}")

def with_sentry_context(**context_data):
    """Decorator to add custom context to Sentry for specific endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Add custom context
            for key, value in context_data.items():
                add_breadcrumb(
                    message=f"Custom context: {key}={value}",
                    category='custom',
                    level='info'
                )
            
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # Capture exception with custom context
                capture_exception(e, **context_data)
                raise
        
        return decorated_function
    return decorator

def track_trading_operation(operation_type: str):
    """Decorator to track trading operations in Sentry."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            add_breadcrumb(
                message=f"Starting trading operation: {operation_type}",
                category='trading',
                level='info',
                data={'operation': operation_type}
            )
            
            try:
                result = f(*args, **kwargs)
                
                add_breadcrumb(
                    message=f"Trading operation completed: {operation_type}",
                    category='trading',
                    level='info',
                    data={'operation': operation_type, 'success': True}
                )
                
                return result
                
            except Exception as e:
                add_breadcrumb(
                    message=f"Trading operation failed: {operation_type}",
                    category='trading',
                    level='error',
                    data={'operation': operation_type, 'error': str(e)}
                )
                
                capture_exception(
                    e,
                    operation_type=operation_type,
                    function_name=f.__name__
                )
                raise
        
        return decorated_function
    return decorator

def capture_trading_error(error: Exception, **context):
    """Helper function to capture trading-specific errors."""
    trading_context = {
        'error_type': 'trading_error',
        'component': 'trading_engine'
    }
    trading_context.update(context)
    
    return capture_exception(error, **trading_context)

def capture_api_error(error: Exception, exchange: str, endpoint: str, **context):
    """Helper function to capture exchange API errors."""
    api_context = {
        'error_type': 'api_error',
        'component': 'exchange_api',
        'exchange': exchange,
        'endpoint': endpoint
    }
    api_context.update(context)
    
    return capture_exception(error, **api_context)