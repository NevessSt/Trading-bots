import time
import redis
from flask import current_app
from typing import Dict, Optional
import json

class RateLimiter:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_store = {}  # Fallback for when Redis is not available
        
    def init_app(self, app, redis_client=None):
        """Initialize with Flask app"""
        if redis_client:
            self.redis_client = redis_client
        else:
            # Try to connect to Redis, fallback to memory if not available
            try:
                import redis
                redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
            except Exception:
                current_app.logger.warning("Redis not available, using memory store for rate limiting")
                self.redis_client = None
    
    def _get_key(self, identifier: str, window: int) -> str:
        """Generate Redis key for rate limiting"""
        current_window = int(time.time()) // window
        return f"rate_limit:{identifier}:{current_window}"
    
    def is_allowed(self, identifier: str, max_requests: int, window: int) -> bool:
        """Check if request is allowed under rate limit"""
        if self.redis_client:
            return self._redis_is_allowed(identifier, max_requests, window)
        else:
            return self._memory_is_allowed(identifier, max_requests, window)
    
    def _redis_is_allowed(self, identifier: str, max_requests: int, window: int) -> bool:
        """Redis-based rate limiting"""
        try:
            key = self._get_key(identifier, window)
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = pipe.execute()
            
            current_requests = results[0]
            return current_requests <= max_requests
            
        except Exception as e:
            current_app.logger.error(f"Redis rate limiting error: {e}")
            # Fallback to allowing request if Redis fails
            return True
    
    def _memory_is_allowed(self, identifier: str, max_requests: int, window: int) -> bool:
        """Memory-based rate limiting (fallback)"""
        current_time = time.time()
        current_window = int(current_time) // window
        
        # Clean old entries
        self._cleanup_memory_store(current_time, window)
        
        key = f"{identifier}:{current_window}"
        
        if key not in self.memory_store:
            self.memory_store[key] = {
                'count': 1,
                'window_start': current_window * window
            }
            return True
        
        self.memory_store[key]['count'] += 1
        return self.memory_store[key]['count'] <= max_requests
    
    def _cleanup_memory_store(self, current_time: float, window: int):
        """Clean expired entries from memory store"""
        cutoff_time = current_time - (window * 2)  # Keep 2 windows worth of data
        
        keys_to_remove = []
        for key, data in self.memory_store.items():
            if data['window_start'] < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.memory_store[key]
    
    def get_remaining_requests(self, identifier: str, max_requests: int, window: int) -> Optional[int]:
        """Get remaining requests for identifier"""
        if self.redis_client:
            try:
                key = self._get_key(identifier, window)
                current_requests = self.redis_client.get(key)
                if current_requests is None:
                    return max_requests
                return max(0, max_requests - int(current_requests))
            except Exception:
                return None
        else:
            current_window = int(time.time()) // window
            key = f"{identifier}:{current_window}"
            if key in self.memory_store:
                return max(0, max_requests - self.memory_store[key]['count'])
            return max_requests
    
    def reset_limit(self, identifier: str, window: int) -> bool:
        """Reset rate limit for identifier"""
        if self.redis_client:
            try:
                key = self._get_key(identifier, window)
                self.redis_client.delete(key)
                return True
            except Exception:
                return False
        else:
            current_window = int(time.time()) // window
            key = f"{identifier}:{current_window}"
            if key in self.memory_store:
                del self.memory_store[key]
            return True

# Global instance
rate_limiter = RateLimiter()