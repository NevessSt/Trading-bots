import time
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker pattern implementation for API calls"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self.logger = logging.getLogger(__name__)
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (datetime.now() - self.last_failure_time).seconds >= self.timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failure and update circuit breaker state"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")

class RetryManager:
    """Advanced retry mechanism with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = logging.getLogger(__name__)
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    self.logger.error(f"All {self.max_retries} retry attempts failed: {str(e)}")
                    break
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                time.sleep(delay)
        
        raise last_exception

class APIHealthMonitor:
    """Monitor API health and manage service availability"""
    
    def __init__(self):
        self.api_status = {}
        self.last_check = {}
        self.check_interval = 300  # 5 minutes
        self.logger = logging.getLogger(__name__)
    
    def check_api_health(self, api_name: str, health_url: str) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(health_url, timeout=10)
            is_healthy = response.status_code == 200
            
            self.api_status[api_name] = {
                'healthy': is_healthy,
                'last_check': datetime.now(),
                'status_code': response.status_code
            }
            
            return is_healthy
        except Exception as e:
            self.logger.error(f"Health check failed for {api_name}: {str(e)}")
            self.api_status[api_name] = {
                'healthy': False,
                'last_check': datetime.now(),
                'error': str(e)
            }
            return False
    
    def is_api_available(self, api_name: str) -> bool:
        """Check if API is currently available"""
        if api_name not in self.api_status:
            return True  # Assume available if not checked yet
        
        status = self.api_status[api_name]
        last_check = status.get('last_check')
        
        # Re-check if enough time has passed
        if last_check and (datetime.now() - last_check).seconds > self.check_interval:
            return True  # Allow re-check
        
        return status.get('healthy', True)

class StabilityManager:
    """Main stability manager coordinating all stability features"""
    
    def __init__(self):
        self.circuit_breakers = {}
        self.retry_manager = RetryManager()
        self.health_monitor = APIHealthMonitor()
        self.logger = logging.getLogger(__name__)
        self._setup_requests_session()
    
    def _setup_requests_session(self):
        """Setup requests session with retry strategy"""
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def stable_api_call(self, service_name: str, func: Callable, *args, **kwargs):
        """Make API call with full stability protection"""
        # Check API health first
        if not self.health_monitor.is_api_available(service_name):
            raise Exception(f"Service {service_name} is currently unavailable")
        
        # Get circuit breaker for this service
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        # Execute with circuit breaker and retry protection
        def protected_call():
            return circuit_breaker.call(func, *args, **kwargs)
        
        return self.retry_manager.retry_with_backoff(protected_call)
    
    def graceful_degradation(self, primary_func: Callable, fallback_func: Callable, *args, **kwargs):
        """Execute primary function with fallback on failure"""
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary function failed, using fallback: {str(e)}")
            return fallback_func(*args, **kwargs)

# Decorator for automatic stability protection
def stable_operation(service_name: str = "default"):
    """Decorator to add stability protection to functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            stability_manager = StabilityManager()
            return stability_manager.stable_api_call(service_name, func, *args, **kwargs)
        return wrapper
    return decorator

# Global stability manager instance
stability_manager = StabilityManager()

# Health check endpoints for common exchanges
EXCHANGE_HEALTH_ENDPOINTS = {
    'binance': 'https://api.binance.com/api/v3/ping',
    'coinbase': 'https://api.coinbase.com/v2/time',
    'kraken': 'https://api.kraken.com/0/public/SystemStatus',
    'bybit': 'https://api.bybit.com/v2/public/time'
}

def monitor_exchange_health():
    """Monitor health of all configured exchanges"""
    health_status = {}
    
    for exchange, endpoint in EXCHANGE_HEALTH_ENDPOINTS.items():
        health_status[exchange] = stability_manager.health_monitor.check_api_health(exchange, endpoint)
    
    return health_status

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test circuit breaker
    @stable_operation("test_service")
    def test_function():
        # Simulate API call that might fail
        import random
        if random.random() < 0.7:  # 70% failure rate for testing
            raise Exception("API call failed")
        return "Success"
    
    # Test the stability system
    for i in range(10):
        try:
            result = test_function()
            print(f"Call {i+1}: {result}")
        except Exception as e:
            print(f"Call {i+1}: Failed - {str(e)}")
        time.sleep(1)