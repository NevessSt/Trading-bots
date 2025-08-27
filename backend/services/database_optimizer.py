from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import Index, text
from sqlalchemy.orm import sessionmaker
from flask import current_app
from db import db
from models import User, Bot, Trade, APIKey
import redis
import json
import hashlib
from functools import wraps
import time

class DatabaseOptimizer:
    """Database optimization service for performance improvements"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or self._get_redis_client()
        self.cache_ttl = {
            'short': 300,    # 5 minutes
            'medium': 1800,  # 30 minutes
            'long': 3600,    # 1 hour
            'daily': 86400   # 24 hours
        }
    
    def _get_redis_client(self):
        """Get Redis client for caching"""
        try:
            # Try to get Redis URL from current_app if available
            try:
                redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            except RuntimeError:
                # Fallback if no application context
                redis_url = 'redis://localhost:6379/0'
            
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            # Use print instead of logger if no app context
            try:
                current_app.logger.warning(f"Redis connection failed: {e}")
            except RuntimeError:
                print(f"Warning: Redis connection failed: {e}")
            return None
    
    def create_database_indexes(self):
        """Create optimized database indexes for better query performance"""
        indexes = [
            # User table indexes
            Index('idx_users_email', User.email),
            Index('idx_users_username', User.username),
            Index('idx_users_license_type', User.license_type),
            Index('idx_users_created_at', User.created_at),
            Index('idx_users_last_login', User.last_login),
            
            # Trade table indexes (most critical for performance)
            Index('idx_trades_user_id', Trade.user_id),
            Index('idx_trades_bot_id', Trade.bot_id),
            Index('idx_trades_symbol', Trade.symbol),
            Index('idx_trades_status', Trade.status),
            Index('idx_trades_created_at', Trade.created_at),
            Index('idx_trades_executed_at', Trade.executed_at),
            Index('idx_trades_exchange', Trade.exchange),
            Index('idx_trades_strategy', Trade.strategy),
            
            # Composite indexes for common query patterns
            Index('idx_trades_user_status', Trade.user_id, Trade.status),
            Index('idx_trades_user_symbol', Trade.user_id, Trade.symbol),
            Index('idx_trades_user_created', Trade.user_id, Trade.created_at.desc()),
            Index('idx_trades_bot_created', Trade.bot_id, Trade.created_at.desc()),
            Index('idx_trades_symbol_created', Trade.symbol, Trade.created_at.desc()),
            Index('idx_trades_status_created', Trade.status, Trade.created_at.desc()),
            
            # Bot table indexes
            Index('idx_bots_user_id', Bot.user_id),
            Index('idx_bots_strategy', Bot.strategy),
            Index('idx_bots_symbol', Bot.symbol),
            Index('idx_bots_is_active', Bot.is_active),
            Index('idx_bots_is_running', Bot.is_running),
            Index('idx_bots_created_at', Bot.created_at),
            Index('idx_bots_last_run_at', Bot.last_run_at),
            
            # Composite indexes for bots
            Index('idx_bots_user_active', Bot.user_id, Bot.is_active),
            Index('idx_bots_user_running', Bot.user_id, Bot.is_running),
            Index('idx_bots_strategy_active', Bot.strategy, Bot.is_active),
            
            # API Key indexes
            Index('idx_api_keys_user_id', APIKey.user_id),
            Index('idx_api_keys_exchange', APIKey.exchange),
            Index('idx_api_keys_is_active', APIKey.is_active),
        ]
        
        try:
            for index in indexes:
                if not self._index_exists(index.name):
                    db.session.execute(text(f"CREATE INDEX IF NOT EXISTS {index.name} ON {index.table.name} ({', '.join([col.name for col in index.columns])})"))
            
            db.session.commit()
            try:
                current_app.logger.info("Database indexes created successfully")
            except RuntimeError:
                print("Database indexes created successfully")
            return True
        except Exception as e:
            db.session.rollback()
            try:
                current_app.logger.error(f"Failed to create indexes: {e}")
            except RuntimeError:
                print(f"Error: Failed to create indexes: {e}")
            return False
    
    def _index_exists(self, index_name):
        """Check if index already exists"""
        try:
            result = db.session.execute(text(
                "SELECT 1 FROM pg_indexes WHERE indexname = :index_name"
            ), {'index_name': index_name})
            return result.fetchone() is not None
        except:
            return False
    
    def optimize_database_settings(self):
        """Apply database-level optimizations"""
        optimizations = [
            # Connection pooling
            "ALTER SYSTEM SET max_connections = '200';",
            "ALTER SYSTEM SET shared_buffers = '256MB';",
            "ALTER SYSTEM SET effective_cache_size = '1GB';",
            "ALTER SYSTEM SET maintenance_work_mem = '64MB';",
            "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
            "ALTER SYSTEM SET wal_buffers = '16MB';",
            "ALTER SYSTEM SET default_statistics_target = 100;",
            "ALTER SYSTEM SET random_page_cost = 1.1;",
            "ALTER SYSTEM SET effective_io_concurrency = 200;",
        ]
        
        try:
            for optimization in optimizations:
                db.session.execute(text(optimization))
            
            # Reload configuration
            db.session.execute(text("SELECT pg_reload_conf();"))
            db.session.commit()
            
            try:
                current_app.logger.info("Database optimizations applied")
            except RuntimeError:
                print("Database optimizations applied")
            return True
        except Exception as e:
            db.session.rollback()
            try:
                current_app.logger.error(f"Failed to apply database optimizations: {e}")
            except RuntimeError:
                print(f"Error: Failed to apply database optimizations: {e}")
            return False
    
    def analyze_tables(self):
        """Update table statistics for better query planning"""
        tables = ['users', 'bots', 'trades', 'api_keys', 'subscriptions']
        
        try:
            for table in tables:
                db.session.execute(text(f"ANALYZE {table};"))
            
            db.session.commit()
            try:
                current_app.logger.info("Table statistics updated")
            except RuntimeError:
                print("Table statistics updated")
            return True
        except Exception as e:
            db.session.rollback()
            try:
                current_app.logger.error(f"Failed to analyze tables: {e}")
            except RuntimeError:
                print(f"Error: Failed to analyze tables: {e}")
            return False
    
    def cache_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments"""
        key_data = f"{prefix}:{'|'.join(map(str, args))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            try:
                current_app.logger.warning(f"Cache get error: {e}")
            except RuntimeError:
                print(f"Warning: Cache get error: {e}")
        
        return None
    
    def set_cached(self, key: str, value: Any, ttl: str = 'medium') -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            return False
        
        try:
            ttl_seconds = self.cache_ttl.get(ttl, self.cache_ttl['medium'])
            self.redis_client.setex(key, ttl_seconds, json.dumps(value, default=str))
            return True
        except Exception as e:
            try:
                current_app.logger.warning(f"Cache set error: {e}")
            except RuntimeError:
                print(f"Warning: Cache set error: {e}")
            return False
    
    def invalidate_cache(self, pattern: str) -> bool:
        """Invalidate cache entries matching pattern"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(f"*{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            try:
                current_app.logger.warning(f"Cache invalidation error: {e}")
            except RuntimeError:
                print(f"Warning: Cache invalidation error: {e}")
            return False

def cached_query(ttl: str = 'medium', key_prefix: str = None):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = DatabaseOptimizer()
            
            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = optimizer.cache_key(prefix, *args, *kwargs.values())
            
            # Try to get from cache
            cached_result = optimizer.get_cached(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            optimizer.set_cached(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def query_timer(func):
    """Decorator to measure query execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 1.0:  # Log slow queries
            try:
                current_app.logger.warning(
                    f"Slow query detected: {func.__name__} took {execution_time:.2f}s"
                )
            except RuntimeError:
                print(f"Warning: Slow query detected: {func.__name__} took {execution_time:.2f}s")
        
        return result
    return wrapper

class OptimizedQueries:
    """Optimized query methods for common operations"""
    
    def __init__(self):
        self.optimizer = DatabaseOptimizer()
    
    @cached_query(ttl='short', key_prefix='user_trades')
    @query_timer
    def get_user_trades_optimized(self, user_id: int, limit: int = 50, offset: int = 0, 
                                 status: str = None, symbol: str = None) -> List[Dict]:
        """Optimized query for user trades with caching"""
        query = db.session.query(Trade).filter(Trade.user_id == user_id)
        
        if status:
            query = query.filter(Trade.status == status)
        if symbol:
            query = query.filter(Trade.symbol == symbol)
        
        trades = query.order_by(Trade.created_at.desc()).limit(limit).offset(offset).all()
        return [trade.to_dict() for trade in trades]
    
    @cached_query(ttl='medium', key_prefix='user_stats')
    @query_timer
    def get_user_trading_stats(self, user_id: int, days: int = 30) -> Dict:
        """Optimized query for user trading statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Use raw SQL for better performance
        stats_query = text("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN status = 'filled' THEN 1 END) as filled_trades,
                COUNT(CASE WHEN status IN ('pending', 'partial') THEN 1 END) as pending_trades,
                COALESCE(SUM(CASE WHEN status = 'filled' THEN total_value END), 0) as total_volume,
                COALESCE(SUM(CASE WHEN status = 'filled' THEN fee END), 0) as total_fees,
                COALESCE(AVG(CASE WHEN status = 'filled' THEN total_value END), 0) as avg_trade_size
            FROM trades 
            WHERE user_id = :user_id AND created_at >= :start_date
        """)
        
        result = db.session.execute(stats_query, {
            'user_id': user_id,
            'start_date': start_date
        }).fetchone()
        
        return {
            'total_trades': result.total_trades,
            'filled_trades': result.filled_trades,
            'pending_trades': result.pending_trades,
            'total_volume': float(result.total_volume),
            'total_fees': float(result.total_fees),
            'avg_trade_size': float(result.avg_trade_size),
            'success_rate': (result.filled_trades / result.total_trades * 100) if result.total_trades > 0 else 0
        }
    
    @cached_query(ttl='short', key_prefix='bot_performance')
    @query_timer
    def get_bot_performance_optimized(self, bot_id: int, days: int = 30) -> Dict:
        """Optimized query for bot performance metrics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        performance_query = text("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN status = 'filled' THEN 1 END) as successful_trades,
                COALESCE(SUM(CASE WHEN status = 'filled' AND side = 'buy' THEN quantity * average_price END), 0) as total_bought,
                COALESCE(SUM(CASE WHEN status = 'filled' AND side = 'sell' THEN quantity * average_price END), 0) as total_sold,
                COALESCE(SUM(CASE WHEN status = 'filled' THEN fee END), 0) as total_fees
            FROM trades 
            WHERE bot_id = :bot_id AND created_at >= :start_date
        """)
        
        result = db.session.execute(performance_query, {
            'bot_id': bot_id,
            'start_date': start_date
        }).fetchone()
        
        return {
            'total_trades': result.total_trades,
            'successful_trades': result.successful_trades,
            'total_bought': float(result.total_bought),
            'total_sold': float(result.total_sold),
            'total_fees': float(result.total_fees),
            'success_rate': (result.successful_trades / result.total_trades * 100) if result.total_trades > 0 else 0,
            'net_pnl': float(result.total_sold) - float(result.total_bought) - float(result.total_fees)
        }
    
    @cached_query(ttl='long', key_prefix='market_summary')
    @query_timer
    def get_market_summary_optimized(self, limit: int = 10) -> List[Dict]:
        """Optimized query for market trading summary"""
        summary_query = text("""
            SELECT 
                symbol,
                COUNT(*) as trade_count,
                COALESCE(SUM(CASE WHEN status = 'filled' THEN total_value END), 0) as volume,
                COALESCE(AVG(CASE WHEN status = 'filled' THEN price END), 0) as avg_price,
                MAX(created_at) as last_trade
            FROM trades 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY symbol 
            ORDER BY volume DESC 
            LIMIT :limit
        """)
        
        results = db.session.execute(summary_query, {'limit': limit}).fetchall()
        
        return [{
            'symbol': row.symbol,
            'trade_count': row.trade_count,
            'volume': float(row.volume),
            'avg_price': float(row.avg_price),
            'last_trade': row.last_trade.isoformat() if row.last_trade else None
        } for row in results]
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a user"""
        patterns = [f'user_trades:{user_id}', f'user_stats:{user_id}']
        for pattern in patterns:
            self.optimizer.invalidate_cache(pattern)
    
    def invalidate_bot_cache(self, bot_id: int):
        """Invalidate all cache entries for a bot"""
        self.optimizer.invalidate_cache(f'bot_performance:{bot_id}')

# Global instance
optimized_queries = OptimizedQueries()
database_optimizer = DatabaseOptimizer()