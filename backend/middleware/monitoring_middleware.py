import time
from flask import request, g
from functools import wraps
from utils.monitoring import get_metrics_collector
from utils.logger import get_logger

logger = get_logger('monitoring_middleware')

class MonitoringMiddleware:
    """Middleware for automatic API monitoring and metrics collection"""
    
    def __init__(self, app=None):
        self.app = app
        self.collector = get_metrics_collector()
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the monitoring middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """Called before each request"""
        g.start_time = time.time()
        self.collector.active_requests += 1
    
    def after_request(self, response):
        """Called after each request"""
        try:
            # Calculate response time
            response_time = time.time() - g.get('start_time', time.time())
            
            # Get request details
            endpoint = request.endpoint or request.path
            method = request.method
            status_code = response.status_code
            
            # Record API metrics
            self.collector.record_api_call(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time
            )
            
            # Add response headers for monitoring
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
            response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
            
        except Exception as e:
            logger.error(f"Error in monitoring middleware: {e}")
        
        finally:
            self.collector.active_requests = max(0, self.collector.active_requests - 1)
        
        return response
    
    def teardown_request(self, exception):
        """Called when request context is torn down"""
        if exception:
            # Record error if request failed with exception
            endpoint = request.endpoint or request.path
            self.collector.record_error(
                error_type='request_exception',
                error_message=str(exception),
                labels={'endpoint': endpoint, 'method': request.method}
            )

def monitor_function(metric_name=None, labels=None):
    """Decorator to monitor function execution time and errors"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            collector = get_metrics_collector()
            name = metric_name or f"{f.__module__}.{f.__name__}"
            
            with collector.start_timer(name, labels):
                try:
                    result = f(*args, **kwargs)
                    collector.increment_counter(f"{name}_success", labels=labels)
                    return result
                except Exception as e:
                    collector.increment_counter(f"{name}_error", labels=labels)
                    collector.record_error(
                        error_type='function_error',
                        error_message=str(e),
                        labels={**(labels or {}), 'function': name}
                    )
                    raise
        
        return decorated_function
    return decorator

def monitor_trade_execution(f):
    """Decorator specifically for monitoring trade execution functions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        collector = get_metrics_collector()
        
        try:
            # Extract trade details from arguments if possible
            trade_labels = {}
            if len(args) > 0 and hasattr(args[0], '__dict__'):
                obj = args[0]
                if hasattr(obj, 'symbol'):
                    trade_labels['symbol'] = getattr(obj, 'symbol', 'unknown')
                if hasattr(obj, 'side'):
                    trade_labels['side'] = getattr(obj, 'side', 'unknown')
            
            with collector.start_timer('trade_execution_time', trade_labels):
                result = f(*args, **kwargs)
                collector.increment_counter('trade_execution_success', labels=trade_labels)
                return result
                
        except Exception as e:
            collector.increment_counter('trade_execution_error', labels=trade_labels)
            collector.record_error(
                error_type='trade_execution',
                error_message=str(e),
                labels=trade_labels
            )
            raise
    
    return decorated_function

def monitor_api_key_usage(f):
    """Decorator for monitoring API key usage and rate limits"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        collector = get_metrics_collector()
        
        try:
            # Extract exchange info if available
            exchange_labels = {}
            if len(args) > 0:
                if hasattr(args[0], 'exchange_name'):
                    exchange_labels['exchange'] = getattr(args[0], 'exchange_name', 'unknown')
                elif hasattr(args[0], 'name'):
                    exchange_labels['exchange'] = getattr(args[0], 'name', 'unknown')
            
            with collector.start_timer('api_call_time', exchange_labels):
                result = f(*args, **kwargs)
                collector.increment_counter('api_calls_success', labels=exchange_labels)
                return result
                
        except Exception as e:
            collector.increment_counter('api_calls_error', labels=exchange_labels)
            
            # Check for rate limit errors
            error_message = str(e).lower()
            if 'rate limit' in error_message or 'too many requests' in error_message:
                collector.record_error(
                    error_type='rate_limit_exceeded',
                    error_message=str(e),
                    labels=exchange_labels
                )
            else:
                collector.record_error(
                    error_type='api_call_error',
                    error_message=str(e),
                    labels=exchange_labels
                )
            raise
    
    return decorated_function

def monitor_database_operations(f):
    """Decorator for monitoring database operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        collector = get_metrics_collector()
        
        # Extract operation type from function name
        operation_type = 'unknown'
        func_name = f.__name__.lower()
        if 'create' in func_name or 'insert' in func_name:
            operation_type = 'create'
        elif 'update' in func_name or 'modify' in func_name:
            operation_type = 'update'
        elif 'delete' in func_name or 'remove' in func_name:
            operation_type = 'delete'
        elif 'find' in func_name or 'get' in func_name or 'query' in func_name:
            operation_type = 'read'
        
        db_labels = {'operation': operation_type, 'function': f.__name__}
        
        try:
            with collector.start_timer('database_operation_time', db_labels):
                result = f(*args, **kwargs)
                collector.increment_counter('database_operations_success', labels=db_labels)
                return result
                
        except Exception as e:
            collector.increment_counter('database_operations_error', labels=db_labels)
            collector.record_error(
                error_type='database_error',
                error_message=str(e),
                labels=db_labels
            )
            raise
    
    return decorated_function

# Convenience function to get monitoring decorators
def get_monitoring_decorators():
    """Get all available monitoring decorators"""
    return {
        'function': monitor_function,
        'trade': monitor_trade_execution,
        'api': monitor_api_key_usage,
        'database': monitor_database_operations
    }