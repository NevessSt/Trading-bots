import time
import logging
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from datetime import datetime, timedelta
from enum import Enum
import ccxt
from dataclasses import dataclass
from threading import Lock

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CircuitBreakerState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (
        ccxt.NetworkError,
        ccxt.ExchangeNotAvailable,
        ccxt.RequestTimeout,
        ccxt.RateLimitExceeded,
        ConnectionError,
        TimeoutError
    )

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: tuple = (Exception,)

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = Lock()
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker")
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN - failing fast")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() > self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        with self._lock:
            self.failure_count = 0
            self.state = CircuitBreakerState.CLOSED
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed execution"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class EnhancedErrorHandler:
    """Enhanced error handling with retry logic, circuit breakers, and fallbacks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
        self._lock = Lock()
    
    def get_circuit_breaker(self, service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            config = config or CircuitBreakerConfig()
            self.circuit_breakers[service_name] = CircuitBreaker(config)
        return self.circuit_breakers[service_name]
    
    def with_retry_and_circuit_breaker(
        self,
        service_name: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None
    ):
        """Decorator for retry logic with circuit breaker"""
        retry_config = retry_config or RetryConfig()
        circuit_breaker = self.get_circuit_breaker(service_name, circuit_config)
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_retry_and_circuit_breaker(
                    func, service_name, retry_config, circuit_breaker, *args, **kwargs
                )
            return wrapper
        return decorator
    
    def _execute_with_retry_and_circuit_breaker(
        self,
        func: Callable,
        service_name: str,
        retry_config: RetryConfig,
        circuit_breaker: CircuitBreaker,
        *args,
        **kwargs
    ):
        """Execute function with retry logic and circuit breaker"""
        last_exception = None
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                # Use circuit breaker
                result = circuit_breaker.call(func, *args, **kwargs)
                
                # Reset error count on success
                with self._lock:
                    if service_name in self.error_counts:
                        del self.error_counts[service_name]
                
                return result
                
            except retry_config.retryable_exceptions as e:
                last_exception = e
                self._log_retry_attempt(service_name, attempt, retry_config.max_retries, e)
                
                if attempt < retry_config.max_retries:
                    delay = self._calculate_delay(attempt, retry_config)
                    time.sleep(delay)
                    continue
                else:
                    self._log_final_failure(service_name, e)
                    break
                    
            except Exception as e:
                # Non-retryable exception
                self._log_non_retryable_error(service_name, e)
                raise e
        
        # Track error
        self._track_error(service_name)
        raise last_exception
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry with exponential backoff and jitter"""
        delay = min(
            config.base_delay * (config.exponential_base ** attempt),
            config.max_delay
        )
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay
    
    def _track_error(self, service_name: str):
        """Track error occurrence"""
        with self._lock:
            self.error_counts[service_name] = self.error_counts.get(service_name, 0) + 1
            self.last_errors[service_name] = datetime.now()
    
    def _log_retry_attempt(self, service_name: str, attempt: int, max_retries: int, error: Exception):
        """Log retry attempt"""
        self.logger.warning(
            f"Retry attempt {attempt + 1}/{max_retries + 1} for {service_name}: {error}"
        )
    
    def _log_final_failure(self, service_name: str, error: Exception):
        """Log final failure after all retries"""
        self.logger.error(
            f"All retry attempts failed for {service_name}: {error}"
        )
    
    def _log_non_retryable_error(self, service_name: str, error: Exception):
        """Log non-retryable error"""
        self.logger.error(
            f"Non-retryable error in {service_name}: {error}"
        )
    
    def get_error_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get error statistics"""
        stats = {}
        
        with self._lock:
            for service_name in set(list(self.error_counts.keys()) + list(self.circuit_breakers.keys())):
                stats[service_name] = {
                    'error_count': self.error_counts.get(service_name, 0),
                    'last_error': self.last_errors.get(service_name),
                    'circuit_breaker_state': self.circuit_breakers[service_name].state.value if service_name in self.circuit_breakers else 'none',
                    'circuit_breaker_failures': self.circuit_breakers[service_name].failure_count if service_name in self.circuit_breakers else 0
                }
        
        return stats
    
    def reset_error_stats(self, service_name: Optional[str] = None):
        """Reset error statistics"""
        with self._lock:
            if service_name:
                self.error_counts.pop(service_name, None)
                self.last_errors.pop(service_name, None)
                if service_name in self.circuit_breakers:
                    self.circuit_breakers[service_name].failure_count = 0
                    self.circuit_breakers[service_name].state = CircuitBreakerState.CLOSED
            else:
                self.error_counts.clear()
                self.last_errors.clear()
                for cb in self.circuit_breakers.values():
                    cb.failure_count = 0
                    cb.state = CircuitBreakerState.CLOSED

class OrderCancellationHandler:
    """Handle order cancellation on failures"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.logger = logging.getLogger(f"{__name__}.OrderCancellation")
        self.pending_orders: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
    
    def track_order(self, order_id: str, symbol: str, user_id: int, order_details: Dict[str, Any]):
        """Track an order for potential cancellation"""
        with self._lock:
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'user_id': user_id,
                'created_at': datetime.now(),
                'details': order_details
            }
    
    def remove_order(self, order_id: str):
        """Remove order from tracking (successful completion)"""
        with self._lock:
            self.pending_orders.pop(order_id, None)
    
    def cancel_order_on_failure(self, order_id: str, reason: str) -> bool:
        """Cancel order due to failure"""
        with self._lock:
            if order_id not in self.pending_orders:
                self.logger.warning(f"Order {order_id} not found in pending orders")
                return False
            
            order_info = self.pending_orders[order_id]
        
        try:
            # Attempt to cancel the order
            result = self.exchange_manager.cancel_order(order_id, order_info['symbol'])
            
            self.logger.info(
                f"Successfully cancelled order {order_id} for user {order_info['user_id']} due to: {reason}"
            )
            
            # Remove from tracking
            self.remove_order(order_id)
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to cancel order {order_id}: {e}"
            )
            return False
    
    def cancel_stale_orders(self, max_age_minutes: int = 30) -> List[str]:
        """Cancel orders that are too old"""
        cancelled_orders = []
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        with self._lock:
            stale_orders = [
                (order_id, info) for order_id, info in self.pending_orders.items()
                if info['created_at'] < cutoff_time
            ]
        
        for order_id, order_info in stale_orders:
            if self.cancel_order_on_failure(order_id, f"Stale order (>{max_age_minutes} minutes)"):
                cancelled_orders.append(order_id)
        
        return cancelled_orders
    
    def get_pending_orders(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending orders"""
        with self._lock:
            return self.pending_orders.copy()

# Global instances
error_handler = EnhancedErrorHandler()