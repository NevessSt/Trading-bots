"""Sentry configuration for error tracking and monitoring."""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None

logger = logging.getLogger(__name__)

class SentryConfig:
    """Sentry configuration and initialization."""
    
    def __init__(self):
        self.dsn = os.getenv('SENTRY_DSN')
        self.environment = os.getenv('FLASK_ENV', 'development')
        self.release = os.getenv('APP_VERSION', '1.0.0')
        self.sample_rate = float(os.getenv('SENTRY_SAMPLE_RATE', '1.0'))
        self.traces_sample_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
        self.enabled = os.getenv('SENTRY_ENABLED', 'false').lower() == 'true'
        self.initialized = False
        
    def init_sentry(self, app=None) -> bool:
        """Initialize Sentry with Flask app integration."""
        if not SENTRY_AVAILABLE:
            logger.warning("Sentry SDK not available. Install with: pip install sentry-sdk[flask]")
            return False
            
        if not self.enabled:
            logger.info("Sentry monitoring disabled via SENTRY_ENABLED=false")
            return False
            
        if not self.dsn:
            logger.warning("Sentry DSN not configured. Set SENTRY_DSN environment variable.")
            return False
            
        try:
            # Configure logging integration
            logging_integration = LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            # Initialize Sentry
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                release=self.release,
                sample_rate=self.sample_rate,
                traces_sample_rate=self.traces_sample_rate,
                integrations=[
                    FlaskIntegration(
                        transaction_style='endpoint'
                    ),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    CeleryIntegration(
                        monitor_beat_tasks=True,
                        propagate_traces=True
                    ),
                    logging_integration,
                ],
                before_send=self._before_send_filter,
                before_send_transaction=self._before_send_transaction_filter,
                attach_stacktrace=True,
                send_default_pii=False,  # Don't send personally identifiable information
                max_breadcrumbs=50,
                debug=self.environment == 'development',
            )
            
            # Set user context and tags
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("component", "trading-bot")
                scope.set_tag("environment", self.environment)
                scope.set_context("app", {
                    "name": "Trading Bot Platform",
                    "version": self.release,
                    "started_at": datetime.utcnow().isoformat()
                })
                
            self.initialized = True
            logger.info(f"Sentry initialized successfully for environment: {self.environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            return False
    
    def _before_send_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter events before sending to Sentry."""
        # Don't send events in test environment
        if self.environment == 'testing':
            return None
            
        # Filter out certain exceptions
        if 'exc_info' in hint:
            exc_type, exc_value, tb = hint['exc_info']
            
            # Skip common HTTP errors that aren't actionable
            if exc_type.__name__ in ['ConnectionError', 'Timeout', 'HTTPError']:
                # Only send if it's a server error (5xx)
                if hasattr(exc_value, 'response') and exc_value.response:
                    if exc_value.response.status_code < 500:
                        return None
                        
            # Skip validation errors (they're user errors, not system errors)
            if exc_type.__name__ in ['ValidationError', 'ValueError', 'KeyError']:
                return None
                
        # Add custom context
        if 'request' in event.get('contexts', {}):
            # Remove sensitive headers
            headers = event['contexts']['request'].get('headers', {})
            sensitive_headers = ['authorization', 'x-api-key', 'cookie']
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = '[Filtered]'
                    
        return event
    
    def _before_send_transaction_filter(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter transaction events before sending to Sentry."""
        # Don't send transactions in test environment
        if self.environment == 'testing':
            return None
            
        # Skip health check endpoints
        transaction_name = event.get('transaction', '')
        if transaction_name in ['/health', '/ping', '/status']:
            return None
            
        return event
    
    def capture_exception(self, exception: Exception, **kwargs) -> Optional[str]:
        """Capture an exception with additional context."""
        if not self.initialized or not SENTRY_AVAILABLE:
            return None
            
        with sentry_sdk.configure_scope() as scope:
            # Add custom context
            for key, value in kwargs.items():
                scope.set_extra(key, value)
                
            return sentry_sdk.capture_exception(exception)
    
    def capture_message(self, message: str, level: str = 'info', **kwargs) -> Optional[str]:
        """Capture a message with additional context."""
        if not self.initialized or not SENTRY_AVAILABLE:
            return None
            
        with sentry_sdk.configure_scope() as scope:
            # Add custom context
            for key, value in kwargs.items():
                scope.set_extra(key, value)
                
            return sentry_sdk.capture_message(message, level=level)
    
    def set_user_context(self, user_id: str, email: Optional[str] = None, **kwargs):
        """Set user context for error tracking."""
        if not self.initialized or not SENTRY_AVAILABLE:
            return
            
        with sentry_sdk.configure_scope() as scope:
            user_data = {'id': user_id}
            if email:
                user_data['email'] = email
            user_data.update(kwargs)
            scope.set_user(user_data)
    
    def set_trading_context(self, bot_id: Optional[str] = None, exchange: Optional[str] = None, 
                          symbol: Optional[str] = None, **kwargs):
        """Set trading-specific context for error tracking."""
        if not self.initialized or not SENTRY_AVAILABLE:
            return
            
        with sentry_sdk.configure_scope() as scope:
            trading_context = {}
            if bot_id:
                trading_context['bot_id'] = bot_id
            if exchange:
                trading_context['exchange'] = exchange
            if symbol:
                trading_context['symbol'] = symbol
            trading_context.update(kwargs)
            
            scope.set_context('trading', trading_context)
    
    def add_breadcrumb(self, message: str, category: str = 'custom', level: str = 'info', **data):
        """Add a breadcrumb for debugging context."""
        if not self.initialized or not SENTRY_AVAILABLE:
            return
            
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data
        )

# Global Sentry instance
sentry_config = SentryConfig()

def init_sentry(app=None) -> bool:
    """Initialize Sentry monitoring."""
    return sentry_config.init_sentry(app)

def capture_exception(exception: Exception, **kwargs) -> Optional[str]:
    """Capture an exception with Sentry."""
    return sentry_config.capture_exception(exception, **kwargs)

def capture_message(message: str, level: str = 'info', **kwargs) -> Optional[str]:
    """Capture a message with Sentry."""
    return sentry_config.capture_message(message, level, **kwargs)

def set_user_context(user_id: str, email: Optional[str] = None, **kwargs):
    """Set user context for Sentry."""
    sentry_config.set_user_context(user_id, email, **kwargs)

def set_trading_context(bot_id: Optional[str] = None, exchange: Optional[str] = None, 
                       symbol: Optional[str] = None, **kwargs):
    """Set trading context for Sentry."""
    sentry_config.set_trading_context(bot_id, exchange, symbol, **kwargs)

def add_breadcrumb(message: str, category: str = 'custom', level: str = 'info', **data):
    """Add a breadcrumb for Sentry."""
    sentry_config.add_breadcrumb(message, category, level, **data)