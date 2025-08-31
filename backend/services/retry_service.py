"""Retry service with exponential backoff and circuit breaker patterns."""

import asyncio
import time
import random
from typing import Callable, Any, Optional, Dict, List, Union, Type
from functools import wraps
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from contextlib import contextmanager

from services.logging_service import get_logger, LogCategory, LogLevel


class RetryStrategy(Enum):
    """Retry strategy enumeration."""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"


class CircuitState(Enum):
    """Circuit breaker state enumeration."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open" # Testing if service is back


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
    backoff_multiplier: float = 2.0
    jitter_range: tuple = (0.1, 0.3)
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()
    timeout: Optional[float] = None
    

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: Type[Exception] = Exception
    success_threshold: int = 3  # Successes needed in half-open state
    

@dataclass
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    delay: float
    exception: Optional[Exception] = None
    timestamp: datetime = field(default_factory=datetime.now)
    

@dataclass
class RetryResult:
    """Result of retry operation."""
    success: bool
    result: Any = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    total_time: float = 0.0
    final_exception: Optional[Exception] = None
    

class CircuitBreaker:
    """Circuit breaker implementation."""
    
    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.lock = threading.Lock()
        self.logger = get_logger(LogCategory.SYSTEM)
        
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN state")
                    return True
                return False
            elif self.state == CircuitState.HALF_OPEN:
                return True
            
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout
    
    def record_success(self):
        """Record successful execution."""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.logger.info(f"Circuit breaker '{self.name}' moved to CLOSED state")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
                
    def record_failure(self, exception: Exception):
        """Record failed execution."""
        with self.lock:
            if isinstance(exception, self.config.expected_exception):
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.OPEN
                    self.logger.warning(f"Circuit breaker '{self.name}' moved to OPEN state (failure in half-open)")
                elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.logger.warning(f"Circuit breaker '{self.name}' moved to OPEN state (threshold reached)")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        with self.lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold
                }
            }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class RetryService:
    """Comprehensive retry service with circuit breaker support."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = get_logger(LogCategory.SYSTEM)
        self.lock = threading.Lock()
        
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker."""
        with self.lock:
            if name not in self.circuit_breakers:
                cb_config = config or CircuitBreakerConfig()
                self.circuit_breakers[name] = CircuitBreaker(cb_config, name)
            return self.circuit_breakers[name]
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        if config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * attempt
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.EXPONENTIAL_JITTER:
            base_delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
            jitter_min, jitter_max = config.jitter_range
            jitter = random.uniform(jitter_min, jitter_max)
            delay = base_delay * (1 + jitter)
        else:
            delay = config.base_delay
            
        return min(delay, config.max_delay)
    
    def is_retryable_exception(self, exception: Exception, config: RetryConfig) -> bool:
        """Check if exception is retryable."""
        # Check non-retryable exceptions first
        if config.non_retryable_exceptions and isinstance(exception, config.non_retryable_exceptions):
            return False
            
        # Check retryable exceptions
        return isinstance(exception, config.retryable_exceptions)
    
    def retry_sync(self, func: Callable, *args, config: Optional[RetryConfig] = None, 
                   circuit_breaker: Optional[str] = None, **kwargs) -> RetryResult:
        """Retry synchronous function with exponential backoff."""
        retry_config = config or RetryConfig()
        start_time = time.time()
        attempts = []
        
        # Get circuit breaker if specified
        cb = None
        if circuit_breaker:
            cb = self.get_circuit_breaker(circuit_breaker)
        
        for attempt in range(1, retry_config.max_attempts + 1):
            # Check circuit breaker
            if cb and not cb.can_execute():
                final_exception = CircuitBreakerOpenException(f"Circuit breaker '{circuit_breaker}' is open")
                self.logger.warning(f"Circuit breaker '{circuit_breaker}' prevented execution")
                return RetryResult(
                    success=False,
                    attempts=attempts,
                    total_time=time.time() - start_time,
                    final_exception=final_exception
                )
            
            try:
                # Execute function with timeout if specified
                if retry_config.timeout:
                    # For sync functions, we can't easily implement timeout without threading
                    # This is a simplified approach
                    result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Record success in circuit breaker
                if cb:
                    cb.record_success()
                
                total_time = time.time() - start_time
                self.logger.info(
                    f"Function succeeded on attempt {attempt}/{retry_config.max_attempts} after {total_time:.3f}s",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt,
                        "total_time": total_time,
                        "circuit_breaker": circuit_breaker
                    }
                )
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=total_time
                )
                
            except Exception as e:
                # Record failure in circuit breaker
                if cb:
                    cb.record_failure(e)
                
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    delay=0,
                    exception=e,
                    timestamp=datetime.now()
                )
                attempts.append(attempt_info)
                
                # Check if exception is retryable
                if not self.is_retryable_exception(e, retry_config):
                    self.logger.error(
                        f"Non-retryable exception in function {func.__name__}: {str(e)}",
                        extra={
                            "function": func.__name__,
                            "exception_type": type(e).__name__,
                            "attempt": attempt,
                            "circuit_breaker": circuit_breaker
                        }
                    )
                    return RetryResult(
                        success=False,
                        attempts=attempts,
                        total_time=time.time() - start_time,
                        final_exception=e
                    )
                
                # If this is the last attempt, don't delay
                if attempt == retry_config.max_attempts:
                    self.logger.error(
                        f"Function {func.__name__} failed after {attempt} attempts: {str(e)}",
                        extra={
                            "function": func.__name__,
                            "exception_type": type(e).__name__,
                            "total_attempts": attempt,
                            "circuit_breaker": circuit_breaker
                        }
                    )
                    return RetryResult(
                        success=False,
                        attempts=attempts,
                        total_time=time.time() - start_time,
                        final_exception=e
                    )
                
                # Calculate delay and wait
                delay = self.calculate_delay(attempt, retry_config)
                attempt_info.delay = delay
                
                self.logger.warning(
                    f"Function {func.__name__} failed on attempt {attempt}, retrying in {delay:.2f}s: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "attempt": attempt,
                        "delay": delay,
                        "circuit_breaker": circuit_breaker
                    }
                )
                
                time.sleep(delay)
        
        # This should never be reached, but just in case
        return RetryResult(
            success=False,
            attempts=attempts,
            total_time=time.time() - start_time,
            final_exception=Exception("Unexpected end of retry loop")
        )
    
    async def retry_async(self, func: Callable, *args, config: Optional[RetryConfig] = None,
                         circuit_breaker: Optional[str] = None, **kwargs) -> RetryResult:
        """Retry asynchronous function with exponential backoff."""
        retry_config = config or RetryConfig()
        start_time = time.time()
        attempts = []
        
        # Get circuit breaker if specified
        cb = None
        if circuit_breaker:
            cb = self.get_circuit_breaker(circuit_breaker)
        
        for attempt in range(1, retry_config.max_attempts + 1):
            # Check circuit breaker
            if cb and not cb.can_execute():
                final_exception = CircuitBreakerOpenException(f"Circuit breaker '{circuit_breaker}' is open")
                self.logger.warning(f"Circuit breaker '{circuit_breaker}' prevented execution")
                return RetryResult(
                    success=False,
                    attempts=attempts,
                    total_time=time.time() - start_time,
                    final_exception=final_exception
                )
            
            try:
                # Execute function with timeout if specified
                if retry_config.timeout:
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=retry_config.timeout)
                else:
                    result = await func(*args, **kwargs)
                
                # Record success in circuit breaker
                if cb:
                    cb.record_success()
                
                total_time = time.time() - start_time
                self.logger.info(
                    f"Async function succeeded on attempt {attempt}/{retry_config.max_attempts} after {total_time:.3f}s",
                    extra={
                        "function": func.__name__,
                        "attempt": attempt,
                        "total_time": total_time,
                        "circuit_breaker": circuit_breaker
                    }
                )
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_time=total_time
                )
                
            except Exception as e:
                # Record failure in circuit breaker
                if cb:
                    cb.record_failure(e)
                
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    delay=0,
                    exception=e,
                    timestamp=datetime.now()
                )
                attempts.append(attempt_info)
                
                # Check if exception is retryable
                if not self.is_retryable_exception(e, retry_config):
                    self.logger.error(
                        f"Non-retryable exception in async function {func.__name__}: {str(e)}",
                        extra={
                            "function": func.__name__,
                            "exception_type": type(e).__name__,
                            "attempt": attempt,
                            "circuit_breaker": circuit_breaker
                        }
                    )
                    return RetryResult(
                        success=False,
                        attempts=attempts,
                        total_time=time.time() - start_time,
                        final_exception=e
                    )
                
                # If this is the last attempt, don't delay
                if attempt == retry_config.max_attempts:
                    self.logger.error(
                        f"Async function {func.__name__} failed after {attempt} attempts: {str(e)}",
                        extra={
                            "function": func.__name__,
                            "exception_type": type(e).__name__,
                            "total_attempts": attempt,
                            "circuit_breaker": circuit_breaker
                        }
                    )
                    return RetryResult(
                        success=False,
                        attempts=attempts,
                        total_time=time.time() - start_time,
                        final_exception=e
                    )
                
                # Calculate delay and wait
                delay = self.calculate_delay(attempt, retry_config)
                attempt_info.delay = delay
                
                self.logger.warning(
                    f"Async function {func.__name__} failed on attempt {attempt}, retrying in {delay:.2f}s: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "attempt": attempt,
                        "delay": delay,
                        "circuit_breaker": circuit_breaker
                    }
                )
                
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        return RetryResult(
            success=False,
            attempts=attempts,
            total_time=time.time() - start_time,
            final_exception=Exception("Unexpected end of retry loop")
        )
    
    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers."""
        with self.lock:
            return {
                "total_circuit_breakers": len(self.circuit_breakers),
                "circuit_breakers": {name: cb.get_state() for name, cb in self.circuit_breakers.items()}
            }


# Global retry service instance
_retry_service: Optional[RetryService] = None


def get_retry_service() -> RetryService:
    """Get global retry service instance."""
    global _retry_service
    if _retry_service is None:
        _retry_service = RetryService()
    return _retry_service


# Decorator functions
def retry(config: Optional[RetryConfig] = None, circuit_breaker: Optional[str] = None):
    """Decorator for automatic retry with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_service = get_retry_service()
            result = retry_service.retry_sync(func, *args, config=config, circuit_breaker=circuit_breaker, **kwargs)
            if result.success:
                return result.result
            else:
                raise result.final_exception
        return wrapper
    return decorator


def async_retry(config: Optional[RetryConfig] = None, circuit_breaker: Optional[str] = None):
    """Decorator for automatic retry with exponential backoff for async functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_service = get_retry_service()
            result = await retry_service.retry_async(func, *args, config=config, circuit_breaker=circuit_breaker, **kwargs)
            if result.success:
                return result.result
            else:
                raise result.final_exception
        return wrapper
    return decorator


# Predefined configurations for common scenarios
API_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL_JITTER,
    backoff_multiplier=2.0,
    retryable_exceptions=(ConnectionError, TimeoutError, OSError),
    timeout=30.0
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=10.0,
    strategy=RetryStrategy.EXPONENTIAL,
    backoff_multiplier=2.0,
    timeout=15.0
)

TRADING_API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=60.0,
    strategy=RetryStrategy.EXPONENTIAL_JITTER,
    backoff_multiplier=3.0,
    retryable_exceptions=(ConnectionError, TimeoutError),
    timeout=45.0
)

BINANCE_CIRCUIT_BREAKER_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=300.0,  # 5 minutes
    success_threshold=3
)