import ccxt
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import os
from concurrent.futures import ThreadPoolExecutor
import time
from threading import Lock
from utils.error_handler import (
    error_handler, 
    RetryConfig, 
    CircuitBreakerConfig, 
    OrderCancellationHandler
)

@dataclass
class ExchangeConfig:
    """Configuration for an exchange"""
    name: str
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None  # For exchanges like Coinbase Pro
    testnet: bool = True
    rate_limit: int = 1200  # requests per minute
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority
    max_retries: int = 3
    retry_delay: float = 1.0

class ExchangeInterface(ABC):
    """Abstract interface for exchange implementations"""
    
    @abstractmethod
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def fetch_balance(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None, params: Dict = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def create_market_order(self, symbol: str, side: str, amount: float, params: Dict = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: Dict = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def fetch_markets(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass

class CCXTExchangeAdapter(ExchangeInterface):
    """Adapter for CCXT exchanges"""
    
    def __init__(self, exchange_instance, name: str, config: ExchangeConfig):
        self.exchange = exchange_instance
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._lock = Lock()
        self._last_request_time = 0
        
        # Initialize error handling components
        self.order_cancellation_handler = OrderCancellationHandler()
        
        # Configure retry settings for different operations
        self.retry_configs = {
            'market_data': RetryConfig(max_attempts=3, base_delay=1.0, max_delay=10.0),
            'order_operations': RetryConfig(max_attempts=5, base_delay=2.0, max_delay=30.0),
            'account_operations': RetryConfig(max_attempts=3, base_delay=1.5, max_delay=15.0)
        }
        
        # Configure circuit breakers
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            half_open_max_calls=3
        )
        
        # Register circuit breakers for different operation types
        error_handler.register_circuit_breaker(f'{name}_market_data', circuit_config)
        error_handler.register_circuit_breaker(f'{name}_orders', circuit_config)
        error_handler.register_circuit_breaker(f'{name}_account', circuit_config)
        
    def _rate_limit(self):
        """Implement rate limiting"""
        with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            min_interval = 60.0 / self.config.rate_limit  # seconds between requests
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()
    
    def _execute_with_enhanced_retry(self, operation_type: str, operation, *args, **kwargs):
        """Execute operation with enhanced error handling, retry logic, and circuit breakers"""
        circuit_breaker_key = f'{self.name}_{operation_type}'
        retry_config = self.retry_configs.get(operation_type, self.retry_configs['market_data'])
        
        def wrapped_operation():
            self._rate_limit()
            return operation(*args, **kwargs)
        
        try:
            return error_handler.execute_with_retry(
                wrapped_operation,
                retry_config=retry_config,
                circuit_breaker_key=circuit_breaker_key,
                operation_context={
                    'exchange_id': self.name,
                    'operation_type': operation_type,
                    'args': str(args)[:100],  # Truncate for logging
                    'kwargs': str({k: str(v)[:50] for k, v in kwargs.items()})
                }
            )
        except Exception as e:
            self.logger.error(f"Enhanced retry failed for {operation_type}: {str(e)}")
            raise
    
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        return self._execute_with_enhanced_retry('market_data', self.exchange.fetch_ticker, symbol)
    
    def fetch_balance(self) -> Dict[str, Any]:
        return self._execute_with_enhanced_retry('account_operations', self.exchange.fetch_balance)
    
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None, params: Dict = None) -> Dict[str, Any]:
        """Generic order creation method with automatic failure handling"""
        try:
            order = self._execute_with_enhanced_retry('order_operations', self.exchange.create_order, symbol, order_type, side, amount, price, params or {})
            
            # Track order for potential cancellation
            if order and 'id' in order:
                self.order_cancellation_handler.track_order(
                    order_id=order['id'],
                    symbol=symbol,
                    exchange_id=self.exchange_id,
                    order_type=order_type,
                    side=side,
                    amount=amount,
                    price=price
                )
            
            return order
        except Exception as e:
            self.logger.error(f"Order creation failed for {symbol} {side} {amount}: {str(e)}")
            raise
    
    def create_market_order(self, symbol: str, side: str, amount: float, params: Dict = None) -> Dict[str, Any]:
        return self._execute_with_enhanced_retry('order_operations', self.exchange.create_market_order, symbol, side, amount, params or {})
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: Dict = None) -> Dict[str, Any]:
        return self._execute_with_enhanced_retry('order_operations', self.exchange.create_limit_order, symbol, side, amount, price, params or {})
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel order with proper cleanup"""
        try:
            result = self._execute_with_enhanced_retry('order_operations', self.exchange.cancel_order, order_id, symbol)
            
            # Remove from tracking
            self.order_cancellation_handler.remove_order(order_id)
            
            return result
        except Exception as e:
            self.logger.error(f"Order cancellation failed for {order_id}: {str(e)}")
            # Still remove from tracking even if cancellation failed
            self.order_cancellation_handler.remove_order(order_id)
            raise
    
    def cancel_stale_orders(self, max_age_minutes: int = 30) -> List[str]:
        """Cancel orders that have been open too long"""
        stale_orders = self.order_cancellation_handler.get_stale_orders(max_age_minutes)
        cancelled_orders = []
        
        for order_id, order_info in stale_orders.items():
            try:
                self.cancel_order(order_id, order_info['symbol'])
                cancelled_orders.append(order_id)
                self.logger.info(f"Cancelled stale order {order_id} (age: {order_info.get('age_minutes', 'unknown')} minutes)")
            except Exception as e:
                self.logger.error(f"Failed to cancel stale order {order_id}: {str(e)}")
        
        return cancelled_orders
    
    def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        return self._execute_with_enhanced_retry('order_operations', self.exchange.fetch_order, order_id, symbol)
    
    def fetch_markets(self) -> Dict[str, Any]:
        return self._execute_with_enhanced_retry('market_data', self.exchange.fetch_markets)
    
    def get_name(self) -> str:
        return self.name

class ExchangeManager:
    """Manages multiple exchange connections with failover and load balancing"""
    
    def __init__(self):
        self.exchanges: Dict[str, ExchangeInterface] = {}
        self.configs: Dict[str, ExchangeConfig] = {}
        self.primary_exchange: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    def create_market_order(self, symbol: str, side: str, amount: float, **kwargs):
        """Create a market order"""
        return self.execute_with_failover('create_order', symbol, 'market', side, amount)
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, **kwargs):
        """Create a limit order"""
        return self.execute_with_failover('create_order', symbol, 'limit', side, amount, price)
    
    def create_stop_market_order(self, symbol: str, side: str, amount: float, stop_price: float, **kwargs):
        """Create a stop market order"""
        params = {'stopPrice': stop_price}
        return self.execute_with_failover('create_order', symbol, 'stop_market', side, amount, None, params)
    
    def cancel_order(self, order_id: str, symbol: str, **kwargs):
        """Cancel an order"""
        return self.execute_with_failover('cancel_order', order_id, symbol)
    
    def fetch_order(self, order_id: str, symbol: str, **kwargs):
        """Fetch order details"""
        return self.execute_with_failover('fetch_order', order_id, symbol)
    
    def fetch_balance(self, **kwargs):
        """Fetch account balance"""
        return self.execute_with_failover('fetch_balance')
    
    def fetch_ticker(self, symbol: str, **kwargs):
        """Fetch ticker data"""
        return self.execute_with_failover('fetch_ticker', symbol)
    
    def fetch_markets(self, **kwargs):
        """Fetch available markets"""
        return self.execute_with_failover('fetch_markets')
        
    def add_exchange(self, config: ExchangeConfig) -> bool:
        """Add an exchange to the manager"""
        try:
            if not config.enabled:
                self.logger.info(f"Exchange {config.name} is disabled, skipping")
                return False
                
            # Validate API credentials
            if not config.api_key or not config.api_secret:
                self.logger.error(f"Missing API credentials for {config.name}")
                return False
            
            # Validate API key format
            if len(config.api_key) < 10 or len(config.api_secret) < 10:
                self.logger.error(f"Invalid API key format for {config.name}")
                return False
            
            # Reject demo/test keys in production
            demo_patterns = ['demo', 'test', 'fake', 'mock', 'sample', 'placeholder']
            if not config.testnet and any(pattern in config.api_key.lower() or pattern in config.api_secret.lower() for pattern in demo_patterns):
                self.logger.error(f"Demo API keys not allowed in production for {config.name}")
                return False
            
            # Create exchange instance based on name
            exchange_instance = self._create_exchange_instance(config)
            if not exchange_instance:
                return False
            
            # Test connection
            adapter = CCXTExchangeAdapter(exchange_instance, config.name, config)
            try:
                balance = adapter.fetch_balance()
                self.logger.info(f"Successfully connected to {config.name} - Testnet: {config.testnet}")
            except ccxt.AuthenticationError:
                self.logger.error(f"Invalid API credentials for {config.name}")
                return False
            except ccxt.PermissionDenied:
                self.logger.error(f"Insufficient API permissions for {config.name}")
                return False
            except Exception as e:
                self.logger.error(f"Failed to connect to {config.name}: {e}")
                return False
            
            # Add to manager
            self.exchanges[config.name] = adapter
            self.configs[config.name] = config
            
            # Set as primary if it's the first or has higher priority
            if not self.primary_exchange or config.priority < self.configs[self.primary_exchange].priority:
                self.primary_exchange = config.name
                self.logger.info(f"Set {config.name} as primary exchange")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding exchange {config.name}: {e}")
            return False
    
    def _create_exchange_instance(self, config: ExchangeConfig):
        """Create CCXT exchange instance based on config"""
        try:
            exchange_params = {
                'apiKey': config.api_key,
                'secret': config.api_secret,
                'sandbox': config.testnet,
                'enableRateLimit': True,
            }
            
            # Add passphrase for exchanges that require it
            if config.passphrase:
                exchange_params['passphrase'] = config.passphrase
            
            if config.name.lower() == 'binance':
                return ccxt.binance(exchange_params)
            elif config.name.lower() == 'coinbase':
                return ccxt.coinbasepro(exchange_params)
            elif config.name.lower() == 'kraken':
                return ccxt.kraken(exchange_params)
            elif config.name.lower() == 'bybit':
                return ccxt.bybit(exchange_params)
            elif config.name.lower() == 'okx':
                return ccxt.okx(exchange_params)
            elif config.name.lower() == 'kucoin':
                return ccxt.kucoin(exchange_params)
            else:
                self.logger.error(f"Unsupported exchange: {config.name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating {config.name} instance: {e}")
            return None
    
    def get_exchange(self, name: Optional[str] = None) -> Optional[ExchangeInterface]:
        """Get exchange by name or primary exchange"""
        if name:
            return self.exchanges.get(name)
        return self.exchanges.get(self.primary_exchange) if self.primary_exchange else None
    
    def get_available_exchanges(self) -> List[str]:
        """Get list of available exchange names"""
        return list(self.exchanges.keys())
    
    def execute_with_failover(self, operation: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute operation with enhanced failover across exchanges"""
        # Sort exchanges by priority and health status
        sorted_exchanges = self._get_healthy_exchanges_by_priority()
        
        if not sorted_exchanges:
            raise Exception(f"No healthy exchanges available for operation: {operation}")
        
        last_exception = None
        failed_exchanges = []
        
        for exchange_name, exchange in sorted_exchanges:
            try:
                if hasattr(exchange, operation):
                    self.logger.info(f"Attempting {operation} on {exchange_name}")
                    
                    # Check circuit breaker status before attempting operation
                    circuit_key = f'{exchange_name}_orders'
                    if not error_handler.is_circuit_breaker_open(circuit_key):
                        method = getattr(exchange, operation)
                        result = method(*args, **kwargs)
                        self.logger.info(f"Successfully executed {operation} on {exchange_name}")
                        return result
                    else:
                        self.logger.warning(f"Circuit breaker open for {exchange_name}, skipping")
                        continue
                else:
                    self.logger.warning(f"Operation {operation} not supported on {exchange_name}")
                    continue
                    
            except Exception as e:
                last_exception = e
                failed_exchanges.append(exchange_name)
                self.logger.warning(f"Operation {operation} failed on {exchange_name}: {e}")
                
                # Record failure for health monitoring
                error_handler.record_error(
                    error=e,
                    context={
                        'operation': operation,
                        'exchange_id': exchange_name,
                        'args': str(args)[:100],
                        'kwargs': str(kwargs)[:100]
                    }
                )
                continue
        
        # If all exchanges failed
        error_msg = f"All exchanges failed for operation {operation}. Failed exchanges: {failed_exchanges}"
        self.logger.error(error_msg)
        
        if last_exception:
            raise last_exception
        else:
            raise Exception(error_msg)
    
    def _get_healthy_exchanges_by_priority(self) -> List[tuple]:
        """Get exchanges sorted by priority, filtering out unhealthy ones"""
        healthy_exchanges = []
        
        for exchange_name, exchange in self.exchanges.items():
            # Check if exchange circuit breakers are not all open
            circuit_keys = [f'{exchange_name}_market_data', f'{exchange_name}_orders', f'{exchange_name}_account']
            open_circuits = sum(1 for key in circuit_keys if error_handler.is_circuit_breaker_open(key))
            
            # Consider exchange healthy if less than half of its circuits are open
            if open_circuits < len(circuit_keys) / 2:
                healthy_exchanges.append((exchange_name, exchange))
            else:
                self.logger.warning(f"Exchange {exchange_name} considered unhealthy ({open_circuits}/{len(circuit_keys)} circuits open)")
        
        # Sort by priority (lower number = higher priority)
        return sorted(healthy_exchanges, key=lambda x: self.configs[x[0]].priority)
    
    def get_best_price(self, symbol: str, side: str) -> Dict[str, Any]:
        """Get best price across all exchanges"""
        prices = []
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                ticker = exchange.fetch_ticker(symbol)
                price = ticker['bid'] if side == 'sell' else ticker['ask']
                prices.append({
                    'exchange': exchange_name,
                    'price': price,
                    'ticker': ticker
                })
            except Exception as e:
                self.logger.warning(f"Failed to get price from {exchange_name}: {e}")
                continue
        
        if not prices:
            raise Exception(f"No price data available for {symbol}")
        
        # Return best price (highest for sell, lowest for buy)
        if side == 'sell':
            return max(prices, key=lambda x: x['price'])
        else:
            return min(prices, key=lambda x: x['price'])
    
    def remove_exchange(self, name: str) -> bool:
        """Remove an exchange from the manager"""
        if name in self.exchanges:
            del self.exchanges[name]
            del self.configs[name]
            
            # Update primary exchange if needed
            if self.primary_exchange == name:
                if self.exchanges:
                    # Set new primary based on priority
                    self.primary_exchange = min(
                        self.exchanges.keys(),
                        key=lambda x: self.configs[x].priority
                    )
                    self.logger.info(f"Set {self.primary_exchange} as new primary exchange")
                else:
                    self.primary_exchange = None
                    self.logger.warning("No exchanges available")
            
            self.logger.info(f"Removed exchange {name}")
            return True
        
        return False
    
    def get_exchange_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all exchanges"""
        status = {}
        
        for name, exchange in self.exchanges.items():
            try:
                # Test connection with a simple API call
                balance = exchange.fetch_balance()
                status[name] = {
                    'status': 'connected',
                    'testnet': self.configs[name].testnet,
                    'priority': self.configs[name].priority,
                    'is_primary': name == self.primary_exchange
                }
            except Exception as e:
                status[name] = {
                    'status': 'error',
                    'error': str(e),
                    'testnet': self.configs[name].testnet,
                    'priority': self.configs[name].priority,
                    'is_primary': name == self.primary_exchange
                }
        
        return status
    
    def shutdown(self):
        """Shutdown the exchange manager"""
        self.executor.shutdown(wait=True)
        self.exchanges.clear()
        self.configs.clear()
        self.primary_exchange = None
        self.logger.info("Exchange manager shutdown complete")