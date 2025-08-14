import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import aiohttp
import websockets
import json
import logging
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
import redis
from dataclasses import dataclass
import threading
from queue import Queue, Empty
import requests
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

@dataclass
class MarketTick:
    """Real-time market tick data"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: float
    high: float
    low: float
    open: float
    change: float
    change_percent: float

@dataclass
class OHLCV:
    """OHLCV candlestick data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    timeframe: str

class DataCache:
    """High-performance data caching system"""
    
    def __init__(self, use_redis: bool = False, redis_host: str = 'localhost', redis_port: int = 6379):
        self.use_redis = use_redis
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.max_memory_items = 10000
        
        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                self.redis_client.ping()
                self.logger = logging.getLogger(__name__)
                self.logger.info("Redis cache initialized")
            except Exception as e:
                self.logger.warning(f"Redis not available, using memory cache: {e}")
                self.use_redis = False
    
    def get(self, key: str, max_age_seconds: int = 300) -> Optional[Any]:
        """Get cached data"""
        if self.use_redis:
            try:
                data = self.redis_client.get(key)
                if data:
                    cached_data = json.loads(data)
                    if time.time() - cached_data['timestamp'] < max_age_seconds:
                        return cached_data['data']
            except Exception:
                pass
        
        # Memory cache fallback
        if key in self.memory_cache:
            if time.time() - self.cache_timestamps[key] < max_age_seconds:
                return self.memory_cache[key]
            else:
                del self.memory_cache[key]
                del self.cache_timestamps[key]
        
        return None
    
    def set(self, key: str, data: Any, ttl_seconds: int = 300):
        """Set cached data"""
        if self.use_redis:
            try:
                cached_data = {
                    'data': data,
                    'timestamp': time.time()
                }
                self.redis_client.setex(key, ttl_seconds, json.dumps(cached_data, default=str))
                return
            except Exception:
                pass
        
        # Memory cache fallback
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove oldest item
            oldest_key = min(self.cache_timestamps.keys(), key=lambda k: self.cache_timestamps[k])
            del self.memory_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
        
        self.memory_cache[key] = data
        self.cache_timestamps[key] = time.time()

class MarketDataManager:
    """Comprehensive market data management system"""
    
    def __init__(self, 
                 exchanges_config: Dict[str, Dict] = None,
                 cache_enabled: bool = True,
                 use_redis: bool = False,
                 db_path: str = 'market_data.db',
                 rate_limit_delay: float = 0.1):
        """
        Initialize market data manager
        
        Args:
            exchanges_config: Configuration for exchanges
            cache_enabled: Enable data caching
            use_redis: Use Redis for caching
            db_path: SQLite database path for historical data
            rate_limit_delay: Delay between API calls
        """
        self.exchanges_config = exchanges_config or {
            'binance': {'sandbox': False, 'rateLimit': 1200},
            'coinbase': {'sandbox': False, 'rateLimit': 1000},
            'kraken': {'sandbox': False, 'rateLimit': 1000}
        }
        
        self.exchanges = {}
        self.cache = DataCache(use_redis=use_redis) if cache_enabled else None
        self.db_path = db_path
        self.rate_limit_delay = rate_limit_delay
        self.logger = logging.getLogger(__name__)
        
        # WebSocket connections
        self.ws_connections = {}
        self.ws_callbacks = {}
        self.ws_running = {}
        
        # Data queues for real-time processing
        self.tick_queue = Queue(maxsize=10000)
        self.ohlcv_queue = Queue(maxsize=1000)
        
        # Initialize exchanges
        self._initialize_exchanges()
        
        # Initialize database
        self._initialize_database()
        
        # Start background data processor
        self.data_processor_thread = threading.Thread(target=self._process_data_queue, daemon=True)
        self.data_processor_thread.start()
    
    def _initialize_exchanges(self):
        """Initialize exchange connections"""
        for exchange_name, config in self.exchanges_config.items():
            try:
                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class({
                    'apiKey': config.get('apiKey', ''),
                    'secret': config.get('secret', ''),
                    'password': config.get('password', ''),
                    'sandbox': config.get('sandbox', False),
                    'rateLimit': config.get('rateLimit', 1000),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot'  # spot, margin, future, option
                    }
                })
                
                # Test connection
                exchange.load_markets()
                self.exchanges[exchange_name] = exchange
                self.logger.info(f"Initialized {exchange_name} exchange")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {exchange_name}: {e}")
    
    def _initialize_database(self):
        """Initialize SQLite database for historical data storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ohlcv_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(exchange, symbol, timeframe, timestamp)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tick_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    bid REAL,
                    ask REAL,
                    last REAL NOT NULL,
                    volume REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(exchange, symbol, timestamp)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_time ON ohlcv_data(symbol, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tick_symbol_time ON tick_data(symbol, timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
    
    def get_historical_data(self, 
                           symbol: str, 
                           timeframe: str = '1h', 
                           limit: int = 500,
                           exchange: str = 'binance',
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           use_cache: bool = True) -> pd.DataFrame:
        """Get historical OHLCV data
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            exchange: Exchange name
            start_date: Start date for data
            end_date: End date for data
            use_cache: Use cached data if available
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"ohlcv_{exchange}_{symbol}_{timeframe}_{limit}"
        
        # Check cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key, max_age_seconds=300)
            if cached_data is not None:
                return pd.DataFrame(cached_data)
        
        try:
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not available")
            
            exchange_obj = self.exchanges[exchange]
            
            # Convert dates to timestamps
            since = None
            if start_date:
                since = int(start_date.timestamp() * 1000)
            
            # Fetch data
            ohlcv_data = exchange_obj.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            
            if not ohlcv_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Filter by end date if specified
            if end_date:
                df = df[df.index <= end_date]
            
            # Cache the result
            if use_cache and self.cache:
                self.cache.set(cache_key, df.reset_index().to_dict('records'), ttl_seconds=300)
            
            # Store in database
            self._store_ohlcv_data(exchange, symbol, timeframe, df)
            
            self.logger.info(f"Fetched {len(df)} candles for {symbol} on {exchange}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            # Try to get data from database as fallback
            return self._get_ohlcv_from_db(exchange, symbol, timeframe, limit)
    
    def get_multiple_symbols_data(self, 
                                 symbols: List[str], 
                                 timeframe: str = '1h',
                                 limit: int = 500,
                                 exchange: str = 'binance',
                                 max_workers: int = 5) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols in parallel
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Timeframe
            limit: Number of candles per symbol
            exchange: Exchange name
            max_workers: Maximum parallel workers
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        def fetch_symbol_data(symbol):
            try:
                time.sleep(self.rate_limit_delay)  # Rate limiting
                return symbol, self.get_historical_data(symbol, timeframe, limit, exchange)
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {e}")
                return symbol, pd.DataFrame()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_symbol_data, symbol) for symbol in symbols]
            
            for future in as_completed(futures):
                symbol, data = future.result()
                results[symbol] = data
        
        return results
    
    def get_real_time_data(self, symbol: str, exchange: str = 'binance') -> Optional[MarketTick]:
        """Get real-time market data
        
        Args:
            symbol: Trading pair symbol
            exchange: Exchange name
            
        Returns:
            Current market tick data
        """
        cache_key = f"tick_{exchange}_{symbol}"
        
        # Check cache first (very short TTL for real-time data)
        if self.cache:
            cached_data = self.cache.get(cache_key, max_age_seconds=5)
            if cached_data:
                return MarketTick(**cached_data)
        
        try:
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not available")
            
            exchange_obj = self.exchanges[exchange]
            ticker = exchange_obj.fetch_ticker(symbol)
            
            tick = MarketTick(
                symbol=symbol,
                timestamp=datetime.now(),
                bid=ticker.get('bid', 0),
                ask=ticker.get('ask', 0),
                last=ticker.get('last', 0),
                volume=ticker.get('baseVolume', 0),
                high=ticker.get('high', 0),
                low=ticker.get('low', 0),
                open=ticker.get('open', 0),
                change=ticker.get('change', 0),
                change_percent=ticker.get('percentage', 0)
            )
            
            # Cache the result
            if self.cache:
                self.cache.set(cache_key, tick.__dict__, ttl_seconds=5)
            
            # Add to processing queue
            try:
                self.tick_queue.put_nowait(tick)
            except:
                pass  # Queue full, skip
            
            return tick
            
        except Exception as e:
            self.logger.error(f"Error fetching real-time data: {e}")
            return None
    
    def start_websocket_stream(self, 
                              symbols: List[str], 
                              exchange: str = 'binance',
                              callback: Optional[callable] = None):
        """Start WebSocket stream for real-time data
        
        Args:
            symbols: List of symbols to stream
            exchange: Exchange name
            callback: Callback function for incoming data
        """
        if exchange not in self.exchanges:
            self.logger.error(f"Exchange {exchange} not available")
            return
        
        stream_key = f"{exchange}_{'-'.join(symbols)}"
        
        if stream_key in self.ws_running and self.ws_running[stream_key]:
            self.logger.warning(f"WebSocket stream {stream_key} already running")
            return
        
        self.ws_callbacks[stream_key] = callback
        self.ws_running[stream_key] = True
        
        # Start WebSocket in separate thread
        ws_thread = threading.Thread(
            target=self._run_websocket_stream,
            args=(symbols, exchange, stream_key),
            daemon=True
        )
        ws_thread.start()
        
        self.logger.info(f"Started WebSocket stream for {symbols} on {exchange}")
    
    def _run_websocket_stream(self, symbols: List[str], exchange: str, stream_key: str):
        """Run WebSocket stream (implementation depends on exchange)"""
        # This is a simplified implementation
        # In practice, you'd use exchange-specific WebSocket APIs
        
        async def websocket_handler():
            while self.ws_running.get(stream_key, False):
                try:
                    # Simulate real-time data updates
                    for symbol in symbols:
                        tick = self.get_real_time_data(symbol, exchange)
                        if tick and self.ws_callbacks.get(stream_key):
                            self.ws_callbacks[stream_key](tick)
                    
                    await asyncio.sleep(1)  # Update every second
                    
                except Exception as e:
                    self.logger.error(f"WebSocket error: {e}")
                    await asyncio.sleep(5)  # Wait before retry
        
        # Run the async handler
        try:
            asyncio.run(websocket_handler())
        except Exception as e:
            self.logger.error(f"WebSocket stream error: {e}")
        finally:
            self.ws_running[stream_key] = False
    
    def stop_websocket_stream(self, symbols: List[str], exchange: str = 'binance'):
        """Stop WebSocket stream"""
        stream_key = f"{exchange}_{'-'.join(symbols)}"
        self.ws_running[stream_key] = False
        self.logger.info(f"Stopped WebSocket stream {stream_key}")
    
    def get_order_book(self, 
                      symbol: str, 
                      exchange: str = 'binance', 
                      limit: int = 100) -> Optional[Dict]:
        """Get order book data
        
        Args:
            symbol: Trading pair symbol
            exchange: Exchange name
            limit: Number of order book levels
            
        Returns:
            Order book data with bids and asks
        """
        cache_key = f"orderbook_{exchange}_{symbol}_{limit}"
        
        # Check cache
        if self.cache:
            cached_data = self.cache.get(cache_key, max_age_seconds=10)
            if cached_data:
                return cached_data
        
        try:
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not available")
            
            exchange_obj = self.exchanges[exchange]
            order_book = exchange_obj.fetch_order_book(symbol, limit)
            
            # Add metadata
            order_book['symbol'] = symbol
            order_book['exchange'] = exchange
            order_book['timestamp'] = datetime.now().isoformat()
            
            # Calculate spread and depth
            if order_book['bids'] and order_book['asks']:
                best_bid = order_book['bids'][0][0]
                best_ask = order_book['asks'][0][0]
                order_book['spread'] = best_ask - best_bid
                order_book['spread_pct'] = (order_book['spread'] / best_ask) * 100
                
                # Calculate depth (total volume at top 10 levels)
                bid_depth = sum([level[1] for level in order_book['bids'][:10]])
                ask_depth = sum([level[1] for level in order_book['asks'][:10]])
                order_book['bid_depth'] = bid_depth
                order_book['ask_depth'] = ask_depth
            
            # Cache the result
            if self.cache:
                self.cache.set(cache_key, order_book, ttl_seconds=10)
            
            return order_book
            
        except Exception as e:
            self.logger.error(f"Error fetching order book: {e}")
            return None
    
    def get_market_summary(self, exchange: str = 'binance') -> Dict[str, Any]:
        """Get market summary statistics
        
        Args:
            exchange: Exchange name
            
        Returns:
            Market summary data
        """
        cache_key = f"market_summary_{exchange}"
        
        # Check cache
        if self.cache:
            cached_data = self.cache.get(cache_key, max_age_seconds=60)
            if cached_data:
                return cached_data
        
        try:
            if exchange not in self.exchanges:
                raise ValueError(f"Exchange {exchange} not available")
            
            exchange_obj = self.exchanges[exchange]
            
            # Get all tickers
            tickers = exchange_obj.fetch_tickers()
            
            # Calculate summary statistics
            total_volume = sum([ticker.get('baseVolume', 0) for ticker in tickers.values()])
            avg_change = np.mean([ticker.get('percentage', 0) for ticker in tickers.values()])
            
            # Top gainers and losers
            sorted_tickers = sorted(tickers.items(), key=lambda x: x[1].get('percentage', 0), reverse=True)
            top_gainers = sorted_tickers[:10]
            top_losers = sorted_tickers[-10:]
            
            # Most active by volume
            volume_sorted = sorted(tickers.items(), key=lambda x: x[1].get('baseVolume', 0), reverse=True)
            most_active = volume_sorted[:10]
            
            summary = {
                'exchange': exchange,
                'timestamp': datetime.now().isoformat(),
                'total_pairs': len(tickers),
                'total_volume_24h': total_volume,
                'average_change_24h': avg_change,
                'top_gainers': [(symbol, data.get('percentage', 0)) for symbol, data in top_gainers],
                'top_losers': [(symbol, data.get('percentage', 0)) for symbol, data in top_losers],
                'most_active': [(symbol, data.get('baseVolume', 0)) for symbol, data in most_active]
            }
            
            # Cache the result
            if self.cache:
                self.cache.set(cache_key, summary, ttl_seconds=60)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error fetching market summary: {e}")
            return {}
    
    def _store_ohlcv_data(self, exchange: str, symbol: str, timeframe: str, df: pd.DataFrame):
        """Store OHLCV data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            for timestamp, row in df.iterrows():
                conn.execute('''
                    INSERT OR REPLACE INTO ohlcv_data 
                    (exchange, symbol, timeframe, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    exchange, symbol, timeframe, int(timestamp.timestamp()),
                    row['open'], row['high'], row['low'], row['close'], row['volume']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing OHLCV data: {e}")
    
    def _get_ohlcv_from_db(self, exchange: str, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Get OHLCV data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv_data
                WHERE exchange = ? AND symbol = ? AND timeframe = ?
                ORDER BY timestamp DESC
                LIMIT ?
            '''
            
            df = pd.read_sql_query(query, conn, params=(exchange, symbol, timeframe, limit))
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                df = df.sort_index()  # Sort chronologically
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting data from database: {e}")
            return pd.DataFrame()
    
    def _process_data_queue(self):
        """Background thread to process incoming data"""
        while True:
            try:
                # Process tick data
                try:
                    tick = self.tick_queue.get(timeout=1)
                    self._store_tick_data(tick)
                except Empty:
                    pass
                
                # Process OHLCV data
                try:
                    ohlcv = self.ohlcv_queue.get(timeout=1)
                    # Process OHLCV if needed
                except Empty:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Error in data processor: {e}")
                time.sleep(1)
    
    def _store_tick_data(self, tick: MarketTick):
        """Store tick data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            conn.execute('''
                INSERT OR REPLACE INTO tick_data 
                (exchange, symbol, timestamp, bid, ask, last, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'binance',  # Default exchange for now
                tick.symbol,
                int(tick.timestamp.timestamp()),
                tick.bid,
                tick.ask,
                tick.last,
                tick.volume
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing tick data: {e}")
    
    def get_supported_symbols(self, exchange: str = 'binance') -> List[str]:
        """Get list of supported trading symbols
        
        Args:
            exchange: Exchange name
            
        Returns:
            List of supported symbols
        """
        cache_key = f"symbols_{exchange}"
        
        # Check cache
        if self.cache:
            cached_data = self.cache.get(cache_key, max_age_seconds=3600)  # Cache for 1 hour
            if cached_data:
                return cached_data
        
        try:
            if exchange not in self.exchanges:
                return []
            
            exchange_obj = self.exchanges[exchange]
            markets = exchange_obj.load_markets()
            symbols = list(markets.keys())
            
            # Filter for active markets only
            active_symbols = [symbol for symbol, market in markets.items() if market.get('active', True)]
            
            # Cache the result
            if self.cache:
                self.cache.set(cache_key, active_symbols, ttl_seconds=3600)
            
            return active_symbols
            
        except Exception as e:
            self.logger.error(f"Error getting supported symbols: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all data sources
        
        Returns:
            Health status of exchanges and services
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'exchanges': {},
            'cache': {'enabled': self.cache is not None},
            'database': {'connected': False},
            'websockets': {}
        }
        
        # Check exchanges
        for exchange_name, exchange_obj in self.exchanges.items():
            try:
                # Simple API call to test connectivity
                exchange_obj.fetch_status()
                health_status['exchanges'][exchange_name] = {
                    'status': 'healthy',
                    'last_check': datetime.now().isoformat()
                }
            except Exception as e:
                health_status['exchanges'][exchange_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
        
        # Check database
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('SELECT 1')
            conn.close()
            health_status['database']['connected'] = True
        except Exception as e:
            health_status['database']['error'] = str(e)
        
        # Check WebSocket connections
        for stream_key, is_running in self.ws_running.items():
            health_status['websockets'][stream_key] = {
                'running': is_running,
                'last_check': datetime.now().isoformat()
            }
        
        return health_status
    
    def cleanup(self):
        """Cleanup resources"""
        # Stop all WebSocket streams
        for stream_key in list(self.ws_running.keys()):
            self.ws_running[stream_key] = False
        
        # Close exchange connections
        for exchange in self.exchanges.values():
            try:
                if hasattr(exchange, 'close'):
                    exchange.close()
            except Exception:
                pass
        
        self.logger.info("Market data manager cleanup completed")
    
    def __del__(self):
        """Destructor"""
        self.cleanup()