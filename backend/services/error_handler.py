"""Comprehensive error handling service with logging, retry, and notifications."""

import traceback
import sys
import asyncio
from typing import Dict, Any, Optional, Callable, Type, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from functools import wraps

from services.logging_service import get_logger, LogCategory, LogLevel
from services.retry_service import get_retry_service, RetryConfig, RetryResult
from services.notification_service import notification_service


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification."""
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    TRADING_ERROR = "trading_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    SYSTEM_ERROR = "system_error"
    SECURITY_ERROR = "security_error"
    CONFIGURATION_ERROR = "configuration_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    function_name: str
    module_name: str
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    exception: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    timestamp: datetime
    traceback_str: str
    should_retry: bool = False
    should_notify: bool = True
    custom_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ErrorHandler:
    """Comprehensive error handling service."""
    
    def __init__(self):
        self.logger = get_logger(LogCategory.ERROR)
        self.retry_service = get_retry_service()
        self.notification_service = notification_service
        
        # Error severity mapping
        self.severity_mapping = {
            ConnectionError: ErrorSeverity.HIGH,
            TimeoutError: ErrorSeverity.HIGH,
            PermissionError: ErrorSeverity.CRITICAL,
            ValueError: ErrorSeverity.MEDIUM,
            KeyError: ErrorSeverity.MEDIUM,
            AttributeError: ErrorSeverity.MEDIUM,
            ImportError: ErrorSeverity.HIGH,
            MemoryError: ErrorSeverity.CRITICAL,
            SystemError: ErrorSeverity.CRITICAL,
        }
        
        # Error category mapping
        self.category_mapping = {
            ConnectionError: ErrorCategory.NETWORK_ERROR,
            TimeoutError: ErrorCategory.NETWORK_ERROR,
            PermissionError: ErrorCategory.SECURITY_ERROR,
            ValueError: ErrorCategory.VALIDATION_ERROR,
            KeyError: ErrorCategory.VALIDATION_ERROR,
            AttributeError: ErrorCategory.SYSTEM_ERROR,
            ImportError: ErrorCategory.CONFIGURATION_ERROR,
            MemoryError: ErrorCategory.SYSTEM_ERROR,
            SystemError: ErrorCategory.SYSTEM_ERROR,
        }
    
    def get_error_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type."""
        return self.severity_mapping.get(type(exception), ErrorSeverity.MEDIUM)
    
    def get_error_category(self, exception: Exception) -> ErrorCategory:
        """Determine error category based on exception type."""
        return self.category_mapping.get(type(exception), ErrorCategory.SYSTEM_ERROR)
    
    def handle_error(self, exception: Exception, context: ErrorContext, 
                    severity: Optional[ErrorSeverity] = None,
                    category: Optional[ErrorCategory] = None,
                    should_retry: bool = False,
                    should_notify: bool = True,
                    custom_message: Optional[str] = None) -> ErrorInfo:
        """Handle an error with comprehensive logging and notification."""
        
        # Determine severity and category if not provided
        if severity is None:
            severity = self.get_error_severity(exception)
        if category is None:
            category = self.get_error_category(exception)
        
        # Create error info
        error_info = ErrorInfo(
            exception=exception,
            severity=severity,
            category=category,
            context=context,
            timestamp=datetime.now(),
            traceback_str=traceback.format_exc(),
            should_retry=should_retry,
            should_notify=should_notify,
            custom_message=custom_message,
            metadata={
                'python_version': sys.version,
                'exception_type': type(exception).__name__,
                'exception_module': type(exception).__module__
            }
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Send notifications if required
        if should_notify:
            self._send_error_notification(error_info)
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level and context."""
        log_data = {
            'error_id': id(error_info),
            'severity': error_info.severity.value,
            'category': error_info.category.value,
            'function': error_info.context.function_name,
            'module': error_info.context.module_name,
            'user_id': error_info.context.user_id,
            'request_id': error_info.context.request_id,
            'session_id': error_info.context.session_id,
            'exception_type': type(error_info.exception).__name__,
            'exception_message': str(error_info.exception),
            'custom_message': error_info.custom_message,
            'metadata': error_info.metadata,
            'additional_data': error_info.context.additional_data
        }
        
        # Choose log level based on severity
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"CRITICAL ERROR in {error_info.context.function_name}: {str(error_info.exception)}",
                extra=log_data
            )
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"HIGH SEVERITY ERROR in {error_info.context.function_name}: {str(error_info.exception)}",
                extra=log_data
            )
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"MEDIUM SEVERITY ERROR in {error_info.context.function_name}: {str(error_info.exception)}",
                extra=log_data
            )
        else:
            self.logger.info(
                f"LOW SEVERITY ERROR in {error_info.context.function_name}: {str(error_info.exception)}",
                extra=log_data
            )
        
        # Log full traceback for high severity errors
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"Full traceback:\n{error_info.traceback_str}")
    
    def _send_error_notification(self, error_info: ErrorInfo):
        """Send error notification based on severity."""
        try:
            message = error_info.custom_message or str(error_info.exception)
            
            if error_info.severity == ErrorSeverity.CRITICAL:
                self.notification_service.send_critical_alert(
                    title=f"Critical Error in {error_info.context.function_name}",
                    message=message,
                    metadata={
                        'category': error_info.category.value,
                        'function': error_info.context.function_name,
                        'module': error_info.context.module_name,
                        'timestamp': error_info.timestamp.isoformat(),
                        'user_id': error_info.context.user_id
                    }
                )
            elif error_info.severity == ErrorSeverity.HIGH:
                if error_info.category == ErrorCategory.API_ERROR:
                    self.notification_service.send_api_error_alert(
                        api_name=error_info.context.function_name,
                        error_message=message,
                        metadata=error_info.metadata
                    )
                elif error_info.category == ErrorCategory.SECURITY_ERROR:
                    self.notification_service.send_security_alert(
                        security_event=f"Security error in {error_info.context.function_name}",
                        details=message,
                        user_id=error_info.context.user_id,
                        metadata=error_info.metadata
                    )
                elif error_info.category == ErrorCategory.TRADING_ERROR:
                    self.notification_service.send_trading_engine_alert(
                        engine_status="error",
                        message=message,
                        metadata=error_info.metadata
                    )
                else:
                    self.notification_service.send_system_error(
                        error_message=message,
                        error_type=error_info.category.value,
                        metadata=error_info.metadata
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {str(e)}")
    
    def handle_with_retry(self, func: Callable, *args, 
                         retry_config: Optional[RetryConfig] = None,
                         context: Optional[ErrorContext] = None,
                         **kwargs) -> Any:
        """Handle function execution with retry logic and error handling."""
        if context is None:
            context = ErrorContext(
                function_name=func.__name__,
                module_name=func.__module__
            )
        
        try:
            result = self.retry_service.retry_sync(
                func, *args, config=retry_config, **kwargs
            )
            
            if not result.success:
                # Handle final failure after retries
                self.handle_error(
                    exception=result.final_exception,
                    context=context,
                    should_retry=False,
                    custom_message=f"Function failed after {len(result.attempts)} retry attempts"
                )
                raise result.final_exception
            
            return result.result
            
        except Exception as e:
            self.handle_error(
                exception=e,
                context=context,
                should_retry=False
            )
            raise
    
    async def handle_with_retry_async(self, func: Callable, *args,
                                     retry_config: Optional[RetryConfig] = None,
                                     context: Optional[ErrorContext] = None,
                                     **kwargs) -> Any:
        """Handle async function execution with retry logic and error handling."""
        if context is None:
            context = ErrorContext(
                function_name=func.__name__,
                module_name=func.__module__
            )
        
        try:
            result = await self.retry_service.retry_async(
                func, *args, config=retry_config, **kwargs
            )
            
            if not result.success:
                # Handle final failure after retries
                self.handle_error(
                    exception=result.final_exception,
                    context=context,
                    should_retry=False,
                    custom_message=f"Async function failed after {len(result.attempts)} retry attempts"
                )
                raise result.final_exception
            
            return result.result
            
        except Exception as e:
            self.handle_error(
                exception=e,
                context=context,
                should_retry=False
            )
            raise
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        return {
            'circuit_breaker_stats': self.retry_service.get_circuit_breaker_stats(),
            'error_handler_info': {
                'severity_levels': [s.value for s in ErrorSeverity],
                'error_categories': [c.value for c in ErrorCategory],
                'mapped_exceptions': list(self.severity_mapping.keys())
            }
        }


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


# Decorator functions
def handle_errors(severity: Optional[ErrorSeverity] = None,
                 category: Optional[ErrorCategory] = None,
                 should_notify: bool = True,
                 custom_message: Optional[str] = None):
    """Decorator for automatic error handling."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            context = ErrorContext(
                function_name=func.__name__,
                module_name=func.__module__
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    exception=e,
                    context=context,
                    severity=severity,
                    category=category,
                    should_notify=should_notify,
                    custom_message=custom_message
                )
                raise
        return wrapper
    return decorator


def handle_errors_async(severity: Optional[ErrorSeverity] = None,
                       category: Optional[ErrorCategory] = None,
                       should_notify: bool = True,
                       custom_message: Optional[str] = None):
    """Decorator for automatic error handling in async functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            context = ErrorContext(
                function_name=func.__name__,
                module_name=func.__module__
            )
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    exception=e,
                    context=context,
                    severity=severity,
                    category=category,
                    should_notify=should_notify,
                    custom_message=custom_message
                )
                raise
        return wrapper
    return decorator


# Context manager for error handling
class ErrorHandlingContext:
    """Context manager for error handling."""
    
    def __init__(self, context: ErrorContext, 
                 severity: Optional[ErrorSeverity] = None,
                 category: Optional[ErrorCategory] = None,
                 should_notify: bool = True):
        self.context = context
        self.severity = severity
        self.category = category
        self.should_notify = should_notify
        self.error_handler = get_error_handler()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_handler.handle_error(
                exception=exc_val,
                context=self.context,
                severity=self.severity,
                category=self.category,
                should_notify=self.should_notify
            )
        return False  # Don't suppress the exception


# Convenience functions
def handle_api_error(exception: Exception, api_name: str, 
                    user_id: Optional[int] = None, **kwargs):
    """Handle API-specific errors."""
    error_handler = get_error_handler()
    context = ErrorContext(
        function_name=api_name,
        module_name="api",
        user_id=user_id,
        additional_data=kwargs
    )
    
    return error_handler.handle_error(
        exception=exception,
        context=context,
        category=ErrorCategory.API_ERROR,
        severity=ErrorSeverity.HIGH
    )


def handle_trading_error(exception: Exception, strategy_name: str,
                        user_id: Optional[int] = None, **kwargs):
    """Handle trading-specific errors."""
    error_handler = get_error_handler()
    context = ErrorContext(
        function_name=strategy_name,
        module_name="trading",
        user_id=user_id,
        additional_data=kwargs
    )
    
    return error_handler.handle_error(
        exception=exception,
        context=context,
        category=ErrorCategory.TRADING_ERROR,
        severity=ErrorSeverity.HIGH
    )


def handle_security_error(exception: Exception, security_context: str,
                         user_id: Optional[int] = None, **kwargs):
    """Handle security-specific errors."""
    error_handler = get_error_handler()
    context = ErrorContext(
        function_name=security_context,
        module_name="security",
        user_id=user_id,
        additional_data=kwargs
    )
    
    return error_handler.handle_error(
        exception=exception,
        context=context,
        category=ErrorCategory.SECURITY_ERROR,
        severity=ErrorSeverity.CRITICAL
    )