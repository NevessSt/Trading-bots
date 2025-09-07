"""Exchange Manager Module

This module provides unified interface for multiple cryptocurrency exchanges:
- Multi-exchange support (Binance, Coinbase, Kraken, etc.)
- Unified API abstraction
- Order management and execution
- Market data streaming
- Account management
- Error handling and retry logic
"""

import logging
import asyncio
import ccxt.async_support as ccxt
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

class ExchangeType(Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    COINBASE = "coinbasepro"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    KUCOIN = "kucoin"
    HUOBI = "huobi"
    BITFINEX = "bitfinex"
    OKEX = "okex"

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    exchange_type: ExchangeType
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None  # For some exchanges like Coinbase
    sandbox: bool = False
    rate_limit: int = 1200  # Requests per minute
    timeout: int = 30000  # Milliseconds
    enable_rate_limit: bool = True
    
@dataclass
class OrderResult:
    """Order execution result"""
    success: bool
    order_id: Optional[str] = None
    symbol: str = ""
    side: str = ""
    amount: float = 0.0
    price: float = 0.0
    filled: float = 0.0
    remaining: float = 0.0
    cost: float = 0.0
    fees: float = 0.0
    status: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    raw_response: Optional[Dict] = None

@dataclass
class MarketData:
    """Market data structure"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    high: float
    low: float
    change: float
    change_percentage: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

class ExchangeManager:
    """Unified Exchange Management System
    
    Provides a unified interface for trading across multiple cryptocurrency exchanges.
    Handles order execution, market data, account management, and error handling.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the exchange manager
        
        Args:
            config: Configuration dictionary containing:
                   - exchanges: List of exchange configurations
                   - default_exchange: Primary exchange to use
                   - failover_enabled: Enable automatic failover
                   - retry_attempts: Number of retry attempts for failed operations
        """
        self.config = config
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.exchange_configs: Dict[str, ExchangeConfig] = {}
        self.default_exchange = config.get('default_exchange', 'binance')
        self.failover_enabled = config.get('failover_enabled', True)
        self.retry_attempts = config.get('retry_attempts', 3)
        
        # Performance tracking
        self.exchange_performance = defaultdict(lambda: {
            'success_count': 0,
            'error_count': 0,
            'avg_response_time': 0.0,
            'last_error': None,
            'last_success': None
        })
        
        # Market data cache
        self.market_data_cache: Dict[str, Dict[str, MarketData]] = defaultdict(dict)
        self.cache_ttl = config.get('cache_ttl', 5)  # seconds
        
        # Order tracking
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Exchange Manager initialized")
    
    async def initialize_exchanges(self, exchange_configs: List[ExchangeConfig]):
        """
        Initialize connections to configured exchanges
        
        Args:
            exchange_configs: List of exchange configurations
        """
        try:
            for config in exchange_configs:
                await self._initialize_exchange(config)
            
            logger.info(f"Initialized {len(self.exchanges)} exchanges: {list(self.exchanges.keys())}")
            
        except Exception as e:
            logger.error(f"Error initializing exchanges: {e}")
            raise
    
    async def _initialize_exchange(self, config: ExchangeConfig):
        """
        Initialize a single exchange connection
        
        Args:
            config: Exchange configuration
        """
        try:
            exchange_class = getattr(ccxt, config.exchange_type.value)
            
            exchange_params = {
                'apiKey': config.api_key,
                'secret': config.api_secret,
                'timeout': config.timeout,
                'enableRateLimit': config.enable_rate_limit,
                'sandbox': config.sandbox,
            }
            
            # Add passphrase for exchanges that require it
            if config.passphrase:
                exchange_params['passphrase'] = config.passphrase
            
            exchange = exchange_class(exchange_params)
            
            # Test connection
            await exchange.load_markets()
            
            exchange_name = config.exchange_type.value
            self.exchanges[exchange_name] = exchange
            self.exchange_configs[exchange_name] = config
            
            logger.info(f"Successfully initialized {exchange_name} exchange")
            
        except Exception as e:
            logger.error(f"Failed to initialize {config.exchange_type.value} exchange: {e}")
            raise
    
    async def execute_order(self, symbol: str, side: str, amount: float, 
                          price: Optional[float] = None, order_type: str = 'market',
                          exchange_name: Optional[str] = None) -> OrderResult:
        """
        Execute a trading order on the specified exchange
        
        This method handles order execution across different exchanges with unified interface.
        It supports various order types, tracks performance metrics, and provides detailed
        execution results with error handling and failover capabilities.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/BTC')
            side: Order side ('buy' or 'sell')
            amount: Order amount in base currency units
            price: Order price (required for limit orders, ignored for market orders)
            order_type: Order type ('market', 'limit', 'stop_loss', etc.)
            exchange_name: Specific exchange to use (uses default if not specified)
            
        Returns:
            OrderResult with detailed execution information including:
            - success: Whether the order was executed successfully
            - order_id: Exchange-specific order identifier
            - filled/remaining amounts, fees, status, etc.
        """
        # Use default exchange if none specified
        exchange_name = exchange_name or self.default_exchange
        
        try:
            # Start performance timing
            start_time = time.time()
            
            # Get the exchange instance (with failover if enabled)
            exchange = await self._get_exchange(exchange_name)
            if not exchange:
                return OrderResult(
                    success=False,
                    error=f"Exchange {exchange_name} not available"
                )
            
            # Prepare order parameters (can be extended for advanced order types)
            order_params = {}
            
            # Execute order based on the specified type
            if order_type == 'market':
                # Market orders execute immediately at current market price
                if side.lower() == 'buy':
                    result = await exchange.create_market_buy_order(symbol, amount)
                else:
                    result = await exchange.create_market_sell_order(symbol, amount)
            elif order_type == 'limit':
                # Limit orders require a specific price
                if not price:
                    return OrderResult(
                        success=False,
                        error="Price required for limit orders"
                    )
                result = await exchange.create_limit_order(symbol, side.lower(), amount, price)
            else:
                return OrderResult(
                    success=False,
                    error=f"Unsupported order type: {order_type}"
                )
            
            # Process and normalize the exchange response
            response_time = time.time() - start_time
            self._update_exchange_performance(exchange_name, True, response_time)
            
            # Create standardized order result from exchange-specific response
            order_result = OrderResult(
                success=True,
                order_id=result.get('id'),  # Exchange-specific order ID
                symbol=result.get('symbol', symbol),  # Normalized symbol format
                side=result.get('side', side),  # 'buy' or 'sell'
                amount=result.get('amount', amount),  # Requested amount
                price=result.get('price', price or 0.0),  # Execution price
                filled=result.get('filled', 0.0),  # Amount filled so far
                remaining=result.get('remaining', amount),  # Amount remaining
                cost=result.get('cost', 0.0),  # Total cost in quote currency
                fees=result.get('fee', {}).get('cost', 0.0),  # Trading fees
                status=result.get('status', 'unknown'),  # Order status
                raw_response=result  # Original exchange response for debugging
            )
            
            # Track active order for monitoring and management
            if order_result.order_id:
                self.active_orders[order_result.order_id] = {
                    'exchange': exchange_name,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'order_type': order_type,
                    'timestamp': datetime.utcnow()
                }
            
            logger.info(f"Order executed successfully on {exchange_name}: {order_result.order_id}")
            return order_result
            
        except Exception as e:
            self._update_exchange_performance(exchange_name, False, 0, str(e))
            logger.error(f"Order execution failed on {exchange_name}: {e}")
            
            # Try failover if enabled
            if self.failover_enabled and exchange_name == self.default_exchange:
                return await self._try_failover_order(symbol, side, amount, price, order_type)
            
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                amount=amount,
                price=price or 0.0,
                error=str(e)
            )
    
    async def _try_failover_order(self, symbol: str, side: str, amount: float,
                                price: Optional[float], order_type: str) -> OrderResult:
        """
        Try to execute order on alternative exchanges
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            amount: Order amount
            price: Order price
            order_type: Order type
            
        Returns:
            OrderResult from successful exchange or final failure
        """
        logger.info("Attempting failover order execution")
        
        # Try other exchanges in order of performance
        sorted_exchanges = sorted(
            [name for name in self.exchanges.keys() if name != self.default_exchange],
            key=lambda x: self.exchange_performance[x]['success_count'],
            reverse=True
        )
        
        for exchange_name in sorted_exchanges:
            try:
                logger.info(f"Trying failover execution on {exchange_name}")
                result = await self.execute_order(symbol, side, amount, price, order_type, exchange_name)
                
                if result.success:
                    logger.info(f"Failover successful on {exchange_name}")
                    return result
                    
            except Exception as e:
                logger.warning(f"Failover failed on {exchange_name}: {e}")
                continue
        
        return OrderResult(
            success=False,
            symbol=symbol,
            side=side,
            amount=amount,
            price=price or 0.0,
            error="All exchanges failed"
        )
    
    async def get_market_data(self, symbol: str, exchange_name: Optional[str] = None) -> Optional[MarketData]:
        """
        Get current market data for a trading symbol
        
        This method retrieves real-time market data including bid/ask prices, volume,
        and price changes. It implements caching to reduce API calls and improve performance.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT', 'ETH/BTC')
            exchange_name: Specific exchange to query (uses default if not specified)
            
        Returns:
            MarketData object with current market information, or None if retrieval failed
        """
        exchange_name = exchange_name or self.default_exchange
        
        try:
            # Check cache first to avoid unnecessary API calls
            cached_data = self.market_data_cache[exchange_name].get(symbol)
            if cached_data and (datetime.utcnow() - cached_data.timestamp).seconds < self.cache_ttl:
                return cached_data
            
            # Fetch fresh data from exchange
            exchange = await self._get_exchange(exchange_name)
            if not exchange:
                return None
            
            # Get ticker data from exchange API
            ticker = await exchange.fetch_ticker(symbol)
            
            # Create standardized market data object
            market_data = MarketData(
                symbol=symbol,
                bid=ticker.get('bid', 0.0),  # Highest buy price
                ask=ticker.get('ask', 0.0),  # Lowest sell price
                last=ticker.get('last', 0.0),  # Last traded price
                volume=ticker.get('baseVolume', 0.0),  # 24h trading volume
                high=ticker.get('high', 0.0),  # 24h high price
                low=ticker.get('low', 0.0),  # 24h low price
                change=ticker.get('change', 0.0),  # 24h price change (absolute)
                change_percentage=ticker.get('percentage', 0.0)  # 24h price change (%)
            )
            
            # Update cache with fresh data
            self.market_data_cache[exchange_name][symbol] = market_data
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol} on {exchange_name}: {e}")
            return None
    
    async def get_account_balance(self, exchange_name: Optional[str] = None) -> Dict[str, float]:
        """
        Get account balance from exchange
        
        Args:
            exchange_name: Specific exchange to query
            
        Returns:
            Dictionary of currency -> balance
        """
        exchange_name = exchange_name or self.default_exchange
        
        try:
            exchange = await self._get_exchange(exchange_name)
            if not exchange:
                return {}
            
            balance = await exchange.fetch_balance()
            
            # Extract free balances
            free_balance = {}
            for currency, amounts in balance.get('free', {}).items():
                if amounts and amounts > 0:
                    free_balance[currency] = amounts
            
            return free_balance
            
        except Exception as e:
            logger.error(f"Failed to get account balance from {exchange_name}: {e}")
            return {}
    
    async def cancel_order(self, order_id: str, symbol: str, exchange_name: Optional[str] = None) -> bool:
        """
        Cancel an active order
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol
            exchange_name: Specific exchange
            
        Returns:
            True if successful, False otherwise
        """
        exchange_name = exchange_name or self.default_exchange
        
        try:
            exchange = await self._get_exchange(exchange_name)
            if not exchange:
                return False
            
            await exchange.cancel_order(order_id, symbol)
            
            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]
            
            logger.info(f"Order {order_id} cancelled successfully on {exchange_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id} on {exchange_name}: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str, exchange_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific order
        
        Args:
            order_id: Order ID to check
            symbol: Trading pair symbol
            exchange_name: Specific exchange
            
        Returns:
            Order status dictionary or None if failed
        """
        exchange_name = exchange_name or self.default_exchange
        
        try:
            exchange = await self._get_exchange(exchange_name)
            if not exchange:
                return None
            
            order = await exchange.fetch_order(order_id, symbol)
            return order
            
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id} on {exchange_name}: {e}")
            return None
    
    async def get_trading_fees(self, symbol: str, exchange_name: Optional[str] = None) -> Dict[str, float]:
        """
        Get trading fees for a symbol
        
        Args:
            symbol: Trading pair symbol
            exchange_name: Specific exchange
            
        Returns:
            Dictionary with maker and taker fees
        """
        exchange_name = exchange_name or self.default_exchange
        
        try:
            exchange = await self._get_exchange(exchange_name)
            if not exchange:
                return {'maker': 0.001, 'taker': 0.001}  # Default fees
            
            # Load markets if not already loaded
            if not exchange.markets:
                await exchange.load_markets()
            
            market = exchange.markets.get(symbol)
            if market and 'fees' in market:
                return {
                    'maker': market['fees'].get('maker', 0.001),
                    'taker': market['fees'].get('taker', 0.001)
                }
            
            # Fallback to exchange default fees
            return {
                'maker': exchange.fees.get('trading', {}).get('maker', 0.001),
                'taker': exchange.fees.get('trading', {}).get('taker', 0.001)
            }
            
        except Exception as e:
            logger.error(f"Failed to get trading fees for {symbol} on {exchange_name}: {e}")
            return {'maker': 0.001, 'taker': 0.001}
    
    async def _get_exchange(self, exchange_name: str) -> Optional[ccxt.Exchange]:
        """
        Get exchange instance with health check
        
        Args:
            exchange_name: Name of the exchange
            
        Returns:
            Exchange instance or None if not available
        """
        if exchange_name not in self.exchanges:
            logger.error(f"Exchange {exchange_name} not configured")
            return None
        
        exchange = self.exchanges[exchange_name]
        
        # Basic health check
        try:
            # Check if exchange is responsive
            if not hasattr(exchange, 'markets') or not exchange.markets:
                await exchange.load_markets()
            return exchange
        except Exception as e:
            logger.error(f"Exchange {exchange_name} health check failed: {e}")
            return None
    
    def _update_exchange_performance(self, exchange_name: str, success: bool, 
                                   response_time: float, error: Optional[str] = None):
        """
        Update exchange performance metrics
        
        Args:
            exchange_name: Name of the exchange
            success: Whether the operation was successful
            response_time: Response time in seconds
            error: Error message if failed
        """
        perf = self.exchange_performance[exchange_name]
        
        if success:
            perf['success_count'] += 1
            perf['last_success'] = datetime.utcnow()
            
            # Update average response time
            total_ops = perf['success_count'] + perf['error_count']
            perf['avg_response_time'] = (
                (perf['avg_response_time'] * (total_ops - 1) + response_time) / total_ops
            )
        else:
            perf['error_count'] += 1
            perf['last_error'] = error
    
    def get_exchange_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for all exchanges
        
        Returns:
            Dictionary of exchange performance data
        """
        return dict(self.exchange_performance)
    
    def get_best_exchange(self, symbol: str) -> str:
        """
        Get the best performing exchange for a symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Name of the best exchange
        """
        # Simple scoring based on success rate and response time
        best_exchange = self.default_exchange
        best_score = 0.0
        
        for exchange_name, perf in self.exchange_performance.items():
            if exchange_name not in self.exchanges:
                continue
            
            total_ops = perf['success_count'] + perf['error_count']
            if total_ops == 0:
                continue
            
            success_rate = perf['success_count'] / total_ops
            response_score = 1.0 / (perf['avg_response_time'] + 0.1)  # Avoid division by zero
            
            # Combined score (70% success rate, 30% response time)
            score = (success_rate * 0.7) + (response_score * 0.3)
            
            if score > best_score:
                best_score = score
                best_exchange = exchange_name
        
        return best_exchange
    
    async def cleanup(self):
        """
        Clean up exchange connections
        """
        try:
            for exchange_name, exchange in self.exchanges.items():
                try:
                    await exchange.close()
                    logger.info(f"Closed connection to {exchange_name}")
                except Exception as e:
                    logger.error(f"Error closing {exchange_name}: {e}")
            
            self.exchanges.clear()
            logger.info("Exchange Manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get exchange manager status
        
        Returns:
            Dictionary with current status information
        """
        return {
            'configured_exchanges': list(self.exchanges.keys()),
            'default_exchange': self.default_exchange,
            'active_orders_count': len(self.active_orders),
            'failover_enabled': self.failover_enabled,
            'performance_metrics': self.get_exchange_performance()
        }

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'default_exchange': 'binance',
        'failover_enabled': True,
        'retry_attempts': 3,
        'cache_ttl': 5
    }
    
    exchange_manager = ExchangeManager(config)
    
    # Example exchange configurations
    exchange_configs = [
        ExchangeConfig(
            exchange_type=ExchangeType.BINANCE,
            api_key='your_binance_api_key',
            api_secret='your_binance_api_secret',
            sandbox=True
        )
    ]
    
    async def example_usage():
        # Initialize exchanges
        await exchange_manager.initialize_exchanges(exchange_configs)
        
        # Get market data
        market_data = await exchange_manager.get_market_data('BTC/USDT')
        if market_data:
            print(f"BTC/USDT Price: ${market_data.last:,.2f}")
        
        # Execute order
        order_result = await exchange_manager.execute_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.001,
            order_type='market'
        )
        
        if order_result.success:
            print(f"Order executed: {order_result.order_id}")
        else:
            print(f"Order failed: {order_result.error}")
        
        # Cleanup
        await exchange_manager.cleanup()
    
    # Run example
    asyncio.run(example_usage())