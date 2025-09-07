"""Enhanced error handling and logging utilities for trading bot.

This module provides comprehensive error handling, retry mechanisms,
circuit breakers, and structured logging for robust trading operations.
"""

import time
import logging
import json
import traceback
from typing import Dict, Any, Optional, Callable, List, Union
from functools import wraps
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from threading import Lock
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Import existing backend utilities
try:
    from backend.utils.error_handler import (
        ErrorSeverity, CircuitBreakerState, RetryConfig, 
        CircuitBreakerConfig, CircuitBreaker, EnhancedErrorHandler
    )
    from backend.utils.logging_config import (
        StructuredFormatter, MonitoringLogHandler, setup_logging,
        get_trade_logger, get_api_logger, log_performance
    )
except ImportError:
    # Fallback implementations if backend modules are not available
    pass

class TradingErrorType(Enum):
    """Types of trading-specific errors"""
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    EXCHANGE_ERROR = "exchange_error"
    VALIDATION_ERROR = "validation_error"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    ORDER_ERROR = "order_error"
    STRATEGY_ERROR = "strategy_error"
    DATA_ERROR = "data_error"
    RISK_MANAGEMENT_ERROR = "risk_management_error"
    AUTHENTICATION_ERROR = "authentication_error"

@dataclass
class TradingError:
    """Structured trading error information"""
    error_type: TradingErrorType
    message: str
    timestamp: datetime
    severity: ErrorSeverity
    context: Dict[str, Any]
    exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    trade_id: Optional[str] = None
    
    def __post_init__(self):
        if self.exception and not self.stack_trace:
            self.stack_trace = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['error_type'] = self.error_type.value
        data['severity'] = self.severity.value
        if self.exception:
            data['exception_type'] = type(self.exception).__name__
            data['exception_message'] = str(self.exception)
        return data

class TradingLogger:
    """Enhanced logging system for trading operations"""
    
    def __init__(self, name: str = "trading_bot", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create specialized loggers
        self.main_logger = self._setup_logger("main", "trading_bot.log")
        self.trade_logger = self._setup_logger("trades", "trades.log")
        self.error_logger = self._setup_logger("errors", "errors.log")
        self.api_logger = self._setup_logger("api", "api_calls.log")
        self.performance_logger = self._setup_logger("performance", "performance.log")
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[TradingError] = []
        self._lock = Lock()
    
    def _setup_logger(self, logger_name: str, filename: str) -> logging.Logger:
        """Setup individual logger with file rotation"""
        logger = logging.getLogger(f"{self.name}.{logger_name}")
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
        
        # Console handler for important messages
        if logger_name in ["main", "errors"]:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(console_handler)
        
        return logger
    
    def log_trade(self, action: str, symbol: str, quantity: float, 
                  price: float, **context):
        """Log trading operations"""
        trade_data = {
            'action': action,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.utcnow().isoformat(),
            **context
        }
        
        self.trade_logger.info(
            f"Trade executed: {action} {quantity} {symbol} @ {price}",
            extra=trade_data
        )
    
    def log_error(self, trading_error: TradingError):
        """Log trading errors with context"""
        with self._lock:
            # Track error counts
            error_key = f"{trading_error.error_type.value}_{trading_error.exchange or 'unknown'}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Store error history (keep last 1000)
            self.error_history.append(trading_error)
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]
        
        # Log the error
        self.error_logger.error(
            f"Trading error: {trading_error.message}",
            extra=trading_error.to_dict()
        )
        
        # Also log to main logger for critical errors
        if trading_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.main_logger.error(
                f"Critical trading error: {trading_error.message}",
                extra=trading_error.to_dict()
            )
    
    def log_api_call(self, endpoint: str, method: str, response_time: float,
                     status_code: int, **context):
        """Log API calls with performance metrics"""
        api_data = {
            'endpoint': endpoint,
            'method': method,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': datetime.utcnow().isoformat(),
            **context
        }
        
        log_level = logging.INFO if status_code < 400 else logging.WARNING
        self.api_logger.log(
            log_level,
            f"API call: {method} {endpoint} - {status_code} ({response_time:.3f}s)",
            extra=api_data
        )
    
    def log_performance(self, operation: str, execution_time: float, **context):
        """Log performance metrics"""
        perf_data = {
            'operation': operation,
            'execution_time': execution_time,
            'timestamp': datetime.utcnow().isoformat(),
            **context
        }
        
        self.performance_logger.info(
            f"Performance: {operation} completed in {execution_time:.4f}s",
            extra=perf_data
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        with self._lock:
            recent_errors = [e for e in self.error_history 
                           if (datetime.utcnow() - e.timestamp).total_seconds() < 3600]
            
            return {
                'total_errors': len(self.error_history),
                'recent_errors_1h': len(recent_errors),
                'error_counts': self.error_counts.copy(),
                'most_recent_errors': [e.to_dict() for e in self.error_history[-5:]]
            }

class TradingErrorHandler:
    """Comprehensive error handling for trading operations"""
    
    def __init__(self, logger: Optional[TradingLogger] = None):
        self.logger = logger or TradingLogger()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = Lock()
    
    def handle_api_error(self, func: Callable) -> Callable:
        """Decorator for handling API errors with retry logic"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            service_name = f"{func.__module__}.{func.__name__}"
            
            # Default retry configuration for API calls
            retry_config = RetryConfig(
                max_retries=3,
                base_delay=1.0,
                max_delay=30.0,
                exponential_base=2.0,
                jitter=True
            )
            
            return self._execute_with_error_handling(
                func, service_name, retry_config, *args, **kwargs
            )
        return wrapper
    
    def handle_trading_operation(self, func: Callable) -> Callable:
        """Decorator for handling trading operations with enhanced error handling"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            service_name = f"trading.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful operation
                execution_time = time.time() - start_time
                self.logger.log_performance(
                    func.__name__, execution_time,
                    success=True, **kwargs
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Determine error type and severity
                error_type = self._classify_error(e)
                severity = self._determine_severity(e, error_type)
                
                # Create structured error
                trading_error = TradingError(
                    error_type=error_type,
                    message=str(e),
                    timestamp=datetime.utcnow(),
                    severity=severity,
                    context={
                        'function': func.__name__,
                        'execution_time': execution_time,
                        'args': str(args)[:200],  # Truncate for logging
                        'kwargs': {k: str(v)[:100] for k, v in kwargs.items()}
                    },
                    exception=e
                )
                
                # Log the error
                self.logger.log_error(trading_error)
                
                # Re-raise for handling by calling code
                raise e
                
        return wrapper
    
    def _execute_with_error_handling(self, func: Callable, service_name: str,
                                   retry_config: RetryConfig, *args, **kwargs):
        """Execute function with comprehensive error handling"""
        last_exception = None
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                
                # Log successful API call
                execution_time = time.time() - start_time
                self.logger.log_performance(
                    service_name, execution_time,
                    attempt=attempt + 1, success=True
                )
                
                return result
                
            except Exception as e:
                last_exception = e
                execution_time = time.time() - start_time
                
                # Check if error is retryable
                if not self._is_retryable_error(e, retry_config):
                    self._log_non_retryable_error(service_name, e, execution_time)
                    raise e
                
                # Log retry attempt
                if attempt < retry_config.max_retries:
                    delay = self._calculate_delay(attempt, retry_config)
                    self._log_retry_attempt(service_name, attempt + 1, 
                                          retry_config.max_retries, e, delay)
                    time.sleep(delay)
                else:
                    self._log_final_failure(service_name, e, execution_time)
        
        # All retries exhausted
        raise last_exception
    
    def _classify_error(self, error: Exception) -> TradingErrorType:
        """Classify error type based on exception"""
        error_name = type(error).__name__.lower()
        error_message = str(error).lower()
        
        if 'network' in error_name or 'connection' in error_name:
            return TradingErrorType.NETWORK_ERROR
        elif 'api' in error_name or 'http' in error_name:
            return TradingErrorType.API_ERROR
        elif 'insufficient' in error_message and 'fund' in error_message:
            return TradingErrorType.INSUFFICIENT_FUNDS
        elif 'order' in error_message:
            return TradingErrorType.ORDER_ERROR
        elif 'auth' in error_name or 'permission' in error_message:
            return TradingErrorType.AUTHENTICATION_ERROR
        elif 'validation' in error_name or 'invalid' in error_message:
            return TradingErrorType.VALIDATION_ERROR
        else:
            return TradingErrorType.EXCHANGE_ERROR
    
    def _determine_severity(self, error: Exception, error_type: TradingErrorType) -> ErrorSeverity:
        """Determine error severity"""
        if error_type in [TradingErrorType.AUTHENTICATION_ERROR, 
                         TradingErrorType.INSUFFICIENT_FUNDS]:
            return ErrorSeverity.HIGH
        elif error_type in [TradingErrorType.ORDER_ERROR, 
                           TradingErrorType.STRATEGY_ERROR]:
            return ErrorSeverity.MEDIUM
        elif error_type in [TradingErrorType.NETWORK_ERROR, 
                           TradingErrorType.API_ERROR]:
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM
    
    def _is_retryable_error(self, error: Exception, config: RetryConfig) -> bool:
        """Check if error is retryable"""
        return isinstance(error, config.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt"""
        delay = min(config.base_delay * (config.exponential_base ** attempt), 
                   config.max_delay)
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay
    
    def _log_retry_attempt(self, service_name: str, attempt: int, max_retries: int,
                          error: Exception, delay: float):
        """Log retry attempt"""
        self.logger.main_logger.warning(
            f"Retry attempt {attempt}/{max_retries} for {service_name} "
            f"after {delay:.2f}s delay. Error: {error}"
        )
    
    def _log_final_failure(self, service_name: str, error: Exception, execution_time: float):
        """Log final failure after all retries"""
        trading_error = TradingError(
            error_type=self._classify_error(error),
            message=f"Final failure for {service_name}: {error}",
            timestamp=datetime.utcnow(),
            severity=ErrorSeverity.HIGH,
            context={
                'service_name': service_name,
                'execution_time': execution_time,
                'retry_exhausted': True
            },
            exception=error
        )
        self.logger.log_error(trading_error)
    
    def _log_non_retryable_error(self, service_name: str, error: Exception, execution_time: float):
        """Log non-retryable error"""
        trading_error = TradingError(
            error_type=self._classify_error(error),
            message=f"Non-retryable error for {service_name}: {error}",
            timestamp=datetime.utcnow(),
            severity=self._determine_severity(error, self._classify_error(error)),
            context={
                'service_name': service_name,
                'execution_time': execution_time,
                'retryable': False
            },
            exception=error
        )
        self.logger.log_error(trading_error)

# Global instances for easy access
trading_logger = TradingLogger()
trading_error_handler = TradingErrorHandler(trading_logger)

# Convenience decorators
handle_api_errors = trading_error_handler.handle_api_error
handle_trading_operations = trading_error_handler.handle_trading_operation