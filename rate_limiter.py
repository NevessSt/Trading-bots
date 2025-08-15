#!/usr/bin/env python3
"""
Rate Limiter and API Throttling System for TradingBot Pro
Provides comprehensive rate limiting, request throttling, and API protection
"""

import time
import json
import redis
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
from collections import defaultdict, deque
import threading
from flask import request, jsonify, g
import ipaddress

class RateLimitType(Enum):
    PER_SECOND = "per_second"
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

class LimitScope(Enum):
    GLOBAL = "global"
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_API_KEY = "per_api_key"
    PER_ENDPOINT = "per_endpoint"

@dataclass
class RateLimit:
    limit: int
    window: int  # in seconds
    limit_type: RateLimitType
    scope: LimitScope
    burst_limit: Optional[int] = None
    description: str = ""
    
@dataclass
class ThrottleConfig:
    enabled: bool = True
    max_requests_per_second: int = 100
    max_requests_per_minute: int = 1000
    max_requests_per_hour: int = 10000
    burst_multiplier: float = 1.5
    cooldown_period: int = 300  # seconds
    
@dataclass
class UserTier:
    name: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int
    concurrent_requests: int
    priority: int = 0
    
class RateLimiter:
    def __init__(self, redis_client: redis.Redis = None, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis_client or self._create_redis_client()
        self.config = config or self._get_default_config()
        
        # In-memory storage for when Redis is not available
        self.memory_store = defaultdict(lambda: defaultdict(deque))
        self.token_buckets = defaultdict(dict)
        self.leaky_buckets = defaultdict(dict)
        
        # User tiers configuration
        self.user_tiers = self._initialize_user_tiers()
        
        # Rate limit rules
        self.rate_limits = self._initialize_rate_limits()
        
        # IP whitelist/blacklist
        self.ip_whitelist = set()
        self.ip_blacklist = set()
        
        # Thread locks for thread safety
        self.locks = defaultdict(threading.Lock)
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'throttled_requests': 0,
            'start_time': datetime.now()
        }
        
        self.logger.info("Rate limiter initialized")
    
    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client with fallback to memory storage"""
        try:
            client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                db=self.config.get('redis_db', 0),
                password=self.config.get('redis_password'),
                decode_responses=True,
                socket_timeout=5
            )
            # Test connection
            client.ping()
            self.logger.info("Connected to Redis for rate limiting")
            return client
        except Exception as e:
            self.logger.warning(f"Redis connection failed, using memory storage: {e}")
            return None
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'default_rate_limit': 1000,
            'default_window': 3600,
            'cleanup_interval': 300,
            'enable_statistics': True
        }
    
    def _initialize_user_tiers(self) -> Dict[str, UserTier]:
        """Initialize user tier configurations"""
        return {
            'free': UserTier(
                name='free',
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=100,
                concurrent_requests=5,
                priority=1
            ),
            'basic': UserTier(
                name='basic',
                requests_per_minute=300,
                requests_per_hour=5000,
                requests_per_day=50000,
                burst_limit=500,
                concurrent_requests=10,
                priority=2
            ),
            'pro': UserTier(
                name='pro',
                requests_per_minute=1000,
                requests_per_hour=20000,
                requests_per_day=200000,
                burst_limit=2000,
                concurrent_requests=25,
                priority=3
            ),
            'enterprise': UserTier(
                name='enterprise',
                requests_per_minute=5000,
                requests_per_hour=100000,
                requests_per_day=1000000,
                burst_limit=10000,
                concurrent_requests=100,
                priority=4
            ),
            'admin': UserTier(
                name='admin',
                requests_per_minute=10000,
                requests_per_hour=500000,
                requests_per_day=5000000,
                burst_limit=50000,
                concurrent_requests=500,
                priority=5
            )
        }
    
    def _initialize_rate_limits(self) -> Dict[str, List[RateLimit]]:
        """Initialize rate limit rules for different endpoints"""
        return {
            'auth': [
                RateLimit(5, 60, RateLimitType.PER_MINUTE, LimitScope.PER_IP, description="Login attempts"),
                RateLimit(20, 3600, RateLimitType.PER_HOUR, LimitScope.PER_IP, description="Auth requests per hour")
            ],
            'api': [
                RateLimit(1000, 3600, RateLimitType.PER_HOUR, LimitScope.PER_API_KEY, description="API calls per hour"),
                RateLimit(100, 60, RateLimitType.PER_MINUTE, LimitScope.PER_API_KEY, description="API calls per minute")
            ],
            'trading': [
                RateLimit(10, 60, RateLimitType.PER_MINUTE, LimitScope.PER_USER, description="Trading operations"),
                RateLimit(100, 3600, RateLimitType.PER_HOUR, LimitScope.PER_USER, description="Trading operations per hour")
            ],
            'data': [
                RateLimit(500, 60, RateLimitType.PER_MINUTE, LimitScope.PER_API_KEY, description="Data requests"),
                RateLimit(5000, 3600, RateLimitType.PER_HOUR, LimitScope.PER_API_KEY, description="Data requests per hour")
            ],
            'websocket': [
                RateLimit(1000, 60, RateLimitType.PER_MINUTE, LimitScope.PER_USER, description="WebSocket messages"),
                RateLimit(10, 1, RateLimitType.PER_SECOND, LimitScope.PER_USER, description="WebSocket burst limit")
            ]
        }
    
    def check_rate_limit(self, identifier: str, endpoint: str = 'api', 
                        user_tier: str = 'free', ip_address: str = None) -> Tuple[bool, Dict]:
        """Check if request should be rate limited"""
        try:
            self.stats['total_requests'] += 1
            
            # Check IP blacklist
            if ip_address and self._is_ip_blacklisted(ip_address):
                self.stats['blocked_requests'] += 1
                return False, {
                    'error': 'IP address is blacklisted',
                    'retry_after': None,
                    'limit_type': 'blacklist'
                }
            
            # Check IP whitelist (bypass rate limits)
            if ip_address and self._is_ip_whitelisted(ip_address):
                return True, {'whitelisted': True}
            
            # Get applicable rate limits
            limits = self.rate_limits.get(endpoint, self.rate_limits.get('api', []))
            
            # Add user tier limits
            tier_limits = self._get_user_tier_limits(user_tier)
            limits.extend(tier_limits)
            
            # Check each rate limit
            for rate_limit in limits:
                allowed, info = self._check_single_limit(identifier, rate_limit, ip_address)
                if not allowed:
                    self.stats['blocked_requests'] += 1
                    return False, info
            
            return True, {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiter fails
            return True, {'error': 'Rate limiter error', 'allowed': True}
    
    def _check_single_limit(self, identifier: str, rate_limit: RateLimit, 
                           ip_address: str = None) -> Tuple[bool, Dict]:
        """Check a single rate limit rule"""
        # Determine the key based on scope
        key = self._get_rate_limit_key(identifier, rate_limit.scope, ip_address)
        
        if rate_limit.limit_type == RateLimitType.TOKEN_BUCKET:
            return self._check_token_bucket(key, rate_limit)
        elif rate_limit.limit_type == RateLimitType.LEAKY_BUCKET:
            return self._check_leaky_bucket(key, rate_limit)
        elif rate_limit.limit_type == RateLimitType.SLIDING_WINDOW:
            return self._check_sliding_window(key, rate_limit)
        else:
            return self._check_fixed_window(key, rate_limit)
    
    def _get_rate_limit_key(self, identifier: str, scope: LimitScope, ip_address: str = None) -> str:
        """Generate rate limit key based on scope"""
        if scope == LimitScope.GLOBAL:
            return "global"
        elif scope == LimitScope.PER_IP and ip_address:
            return f"ip:{ip_address}"
        elif scope == LimitScope.PER_USER:
            return f"user:{identifier}"
        elif scope == LimitScope.PER_API_KEY:
            return f"api_key:{identifier}"
        elif scope == LimitScope.PER_ENDPOINT:
            return f"endpoint:{identifier}"
        else:
            return f"default:{identifier}"
    
    def _check_fixed_window(self, key: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Check fixed window rate limit"""
        current_time = int(time.time())
        window_start = current_time - (current_time % rate_limit.window)
        window_key = f"{key}:{window_start}"
        
        try:
            if self.redis_client:
                # Use Redis for distributed rate limiting
                pipe = self.redis_client.pipeline()
                pipe.incr(window_key)
                pipe.expire(window_key, rate_limit.window)
                results = pipe.execute()
                current_count = results[0]
            else:
                # Use memory storage
                with self.locks[key]:
                    if window_key not in self.memory_store[key]:
                        self.memory_store[key][window_key] = 0
                    self.memory_store[key][window_key] += 1
                    current_count = self.memory_store[key][window_key]
                    
                    # Cleanup old windows
                    self._cleanup_memory_windows(key, current_time, rate_limit.window)
            
            if current_count > rate_limit.limit:
                retry_after = rate_limit.window - (current_time % rate_limit.window)
                return False, {
                    'error': 'Rate limit exceeded',
                    'limit': rate_limit.limit,
                    'window': rate_limit.window,
                    'current': current_count,
                    'retry_after': retry_after,
                    'limit_type': rate_limit.limit_type.value
                }
            
            return True, {
                'limit': rate_limit.limit,
                'remaining': rate_limit.limit - current_count,
                'reset_time': window_start + rate_limit.window
            }
            
        except Exception as e:
            self.logger.error(f"Fixed window check failed: {e}")
            return True, {'error': 'Rate limit check failed'}
    
    def _check_sliding_window(self, key: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Check sliding window rate limit"""
        current_time = time.time()
        window_start = current_time - rate_limit.window
        
        try:
            if self.redis_client:
                # Use Redis sorted sets for sliding window
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, rate_limit.window)
                results = pipe.execute()
                current_count = results[1] + 1  # +1 for the current request
            else:
                # Use memory storage with deque
                with self.locks[key]:
                    window_key = f"sliding:{key}"
                    if window_key not in self.memory_store:
                        self.memory_store[window_key] = deque()
                    
                    # Remove old entries
                    while (self.memory_store[window_key] and 
                           self.memory_store[window_key][0] < window_start):
                        self.memory_store[window_key].popleft()
                    
                    # Add current request
                    self.memory_store[window_key].append(current_time)
                    current_count = len(self.memory_store[window_key])
            
            if current_count > rate_limit.limit:
                return False, {
                    'error': 'Rate limit exceeded',
                    'limit': rate_limit.limit,
                    'window': rate_limit.window,
                    'current': current_count,
                    'retry_after': int(rate_limit.window / rate_limit.limit),
                    'limit_type': rate_limit.limit_type.value
                }
            
            return True, {
                'limit': rate_limit.limit,
                'remaining': rate_limit.limit - current_count,
                'window': rate_limit.window
            }
            
        except Exception as e:
            self.logger.error(f"Sliding window check failed: {e}")
            return True, {'error': 'Rate limit check failed'}
    
    def _check_token_bucket(self, key: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Check token bucket rate limit"""
        current_time = time.time()
        
        with self.locks[key]:
            if key not in self.token_buckets:
                self.token_buckets[key] = {
                    'tokens': rate_limit.limit,
                    'last_refill': current_time,
                    'capacity': rate_limit.limit,
                    'refill_rate': rate_limit.limit / rate_limit.window
                }
            
            bucket = self.token_buckets[key]
            
            # Refill tokens based on time elapsed
            time_elapsed = current_time - bucket['last_refill']
            tokens_to_add = time_elapsed * bucket['refill_rate']
            bucket['tokens'] = min(bucket['capacity'], bucket['tokens'] + tokens_to_add)
            bucket['last_refill'] = current_time
            
            # Check if we have tokens available
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True, {
                    'tokens_remaining': int(bucket['tokens']),
                    'capacity': bucket['capacity']
                }
            else:
                retry_after = (1 - bucket['tokens']) / bucket['refill_rate']
                return False, {
                    'error': 'Rate limit exceeded',
                    'retry_after': int(retry_after),
                    'limit_type': rate_limit.limit_type.value
                }
    
    def _check_leaky_bucket(self, key: str, rate_limit: RateLimit) -> Tuple[bool, Dict]:
        """Check leaky bucket rate limit"""
        current_time = time.time()
        
        with self.locks[key]:
            if key not in self.leaky_buckets:
                self.leaky_buckets[key] = {
                    'volume': 0,
                    'last_leak': current_time,
                    'capacity': rate_limit.limit,
                    'leak_rate': rate_limit.limit / rate_limit.window
                }
            
            bucket = self.leaky_buckets[key]
            
            # Leak tokens based on time elapsed
            time_elapsed = current_time - bucket['last_leak']
            tokens_to_leak = time_elapsed * bucket['leak_rate']
            bucket['volume'] = max(0, bucket['volume'] - tokens_to_leak)
            bucket['last_leak'] = current_time
            
            # Check if we can add the request
            if bucket['volume'] < bucket['capacity']:
                bucket['volume'] += 1
                return True, {
                    'volume': bucket['volume'],
                    'capacity': bucket['capacity']
                }
            else:
                retry_after = 1 / bucket['leak_rate']
                return False, {
                    'error': 'Rate limit exceeded',
                    'retry_after': int(retry_after),
                    'limit_type': rate_limit.limit_type.value
                }
    
    def _get_user_tier_limits(self, user_tier: str) -> List[RateLimit]:
        """Get rate limits for user tier"""
        tier = self.user_tiers.get(user_tier, self.user_tiers['free'])
        
        return [
            RateLimit(
                tier.requests_per_minute, 60, 
                RateLimitType.PER_MINUTE, LimitScope.PER_USER,
                description=f"{tier.name} tier per minute"
            ),
            RateLimit(
                tier.requests_per_hour, 3600, 
                RateLimitType.PER_HOUR, LimitScope.PER_USER,
                description=f"{tier.name} tier per hour"
            ),
            RateLimit(
                tier.requests_per_day, 86400, 
                RateLimitType.PER_DAY, LimitScope.PER_USER,
                description=f"{tier.name} tier per day"
            )
        ]
    
    def _is_ip_whitelisted(self, ip_address: str) -> bool:
        """Check if IP is whitelisted"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for whitelisted in self.ip_whitelist:
                if ip in ipaddress.ip_network(whitelisted, strict=False):
                    return True
            return False
        except Exception:
            return False
    
    def _is_ip_blacklisted(self, ip_address: str) -> bool:
        """Check if IP is blacklisted"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for blacklisted in self.ip_blacklist:
                if ip in ipaddress.ip_network(blacklisted, strict=False):
                    return True
            return False
        except Exception:
            return False
    
    def _cleanup_memory_windows(self, key: str, current_time: int, window_size: int):
        """Clean up old memory windows"""
        cutoff_time = current_time - window_size * 2  # Keep some extra for safety
        keys_to_remove = []
        
        for window_key in self.memory_store[key]:
            try:
                window_start = int(window_key.split(':')[-1])
                if window_start < cutoff_time:
                    keys_to_remove.append(window_key)
            except (ValueError, IndexError):
                continue
        
        for window_key in keys_to_remove:
            del self.memory_store[key][window_key]
    
    def add_ip_to_whitelist(self, ip_or_network: str):
        """Add IP or network to whitelist"""
        try:
            # Validate IP/network
            ipaddress.ip_network(ip_or_network, strict=False)
            self.ip_whitelist.add(ip_or_network)
            self.logger.info(f"Added {ip_or_network} to whitelist")
        except Exception as e:
            self.logger.error(f"Invalid IP/network for whitelist: {e}")
    
    def add_ip_to_blacklist(self, ip_or_network: str):
        """Add IP or network to blacklist"""
        try:
            # Validate IP/network
            ipaddress.ip_network(ip_or_network, strict=False)
            self.ip_blacklist.add(ip_or_network)
            self.logger.info(f"Added {ip_or_network} to blacklist")
        except Exception as e:
            self.logger.error(f"Invalid IP/network for blacklist: {e}")
    
    def remove_ip_from_whitelist(self, ip_or_network: str):
        """Remove IP or network from whitelist"""
        self.ip_whitelist.discard(ip_or_network)
        self.logger.info(f"Removed {ip_or_network} from whitelist")
    
    def remove_ip_from_blacklist(self, ip_or_network: str):
        """Remove IP or network from blacklist"""
        self.ip_blacklist.discard(ip_or_network)
        self.logger.info(f"Removed {ip_or_network} from blacklist")
    
    def get_rate_limit_status(self, identifier: str, endpoint: str = 'api') -> Dict:
        """Get current rate limit status for identifier"""
        status = {
            'identifier': identifier,
            'endpoint': endpoint,
            'limits': [],
            'timestamp': datetime.now().isoformat()
        }
        
        limits = self.rate_limits.get(endpoint, [])
        
        for rate_limit in limits:
            key = self._get_rate_limit_key(identifier, rate_limit.scope)
            
            if rate_limit.limit_type == RateLimitType.TOKEN_BUCKET:
                bucket = self.token_buckets.get(key, {})
                status['limits'].append({
                    'type': rate_limit.limit_type.value,
                    'limit': rate_limit.limit,
                    'tokens_remaining': int(bucket.get('tokens', rate_limit.limit)),
                    'capacity': bucket.get('capacity', rate_limit.limit)
                })
            else:
                # For other types, we'd need to check current usage
                status['limits'].append({
                    'type': rate_limit.limit_type.value,
                    'limit': rate_limit.limit,
                    'window': rate_limit.window,
                    'description': rate_limit.description
                })
        
        return status
    
    def get_statistics(self) -> Dict:
        """Get rate limiter statistics"""
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            'total_requests': self.stats['total_requests'],
            'blocked_requests': self.stats['blocked_requests'],
            'throttled_requests': self.stats['throttled_requests'],
            'block_rate': (self.stats['blocked_requests'] / max(self.stats['total_requests'], 1)) * 100,
            'uptime_seconds': int(uptime.total_seconds()),
            'requests_per_second': self.stats['total_requests'] / max(uptime.total_seconds(), 1),
            'memory_buckets': len(self.token_buckets) + len(self.leaky_buckets),
            'whitelist_size': len(self.ip_whitelist),
            'blacklist_size': len(self.ip_blacklist)
        }
    
    def reset_limits(self, identifier: str = None, endpoint: str = None):
        """Reset rate limits for identifier or endpoint"""
        if identifier and endpoint:
            # Reset specific identifier for endpoint
            limits = self.rate_limits.get(endpoint, [])
            for rate_limit in limits:
                key = self._get_rate_limit_key(identifier, rate_limit.scope)
                
                # Clear from all storage types
                if self.redis_client:
                    self.redis_client.delete(key)
                
                self.token_buckets.pop(key, None)
                self.leaky_buckets.pop(key, None)
                self.memory_store.pop(key, None)
            
            self.logger.info(f"Reset limits for {identifier} on {endpoint}")
        
        elif identifier:
            # Reset all limits for identifier
            keys_to_remove = []
            for key in list(self.token_buckets.keys()) + list(self.leaky_buckets.keys()):
                if identifier in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                if self.redis_client:
                    self.redis_client.delete(key)
                
                self.token_buckets.pop(key, None)
                self.leaky_buckets.pop(key, None)
                self.memory_store.pop(key, None)
            
            self.logger.info(f"Reset all limits for {identifier}")
        
        else:
            # Reset all limits
            if self.redis_client:
                # This is dangerous in production - consider pattern-based deletion
                pass
            
            self.token_buckets.clear()
            self.leaky_buckets.clear()
            self.memory_store.clear()
            
            self.logger.info("Reset all rate limits")
    
    def update_user_tier(self, tier_name: str, tier_config: UserTier):
        """Update or add user tier configuration"""
        self.user_tiers[tier_name] = tier_config
        self.logger.info(f"Updated user tier: {tier_name}")
    
    def add_rate_limit_rule(self, endpoint: str, rate_limit: RateLimit):
        """Add new rate limit rule for endpoint"""
        if endpoint not in self.rate_limits:
            self.rate_limits[endpoint] = []
        
        self.rate_limits[endpoint].append(rate_limit)
        self.logger.info(f"Added rate limit rule for {endpoint}: {rate_limit.description}")
    
    def remove_rate_limit_rule(self, endpoint: str, rule_index: int = None):
        """Remove rate limit rule from endpoint"""
        if endpoint in self.rate_limits:
            if rule_index is not None and 0 <= rule_index < len(self.rate_limits[endpoint]):
                removed = self.rate_limits[endpoint].pop(rule_index)
                self.logger.info(f"Removed rate limit rule from {endpoint}: {removed.description}")
            else:
                self.rate_limits[endpoint].clear()
                self.logger.info(f"Removed all rate limit rules from {endpoint}")

# Flask decorator for rate limiting
def rate_limit(endpoint: str = 'api', user_tier_func=None, identifier_func=None):
    """Decorator for Flask routes to apply rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limiter instance (should be initialized in app context)
            rate_limiter = getattr(g, 'rate_limiter', None)
            if not rate_limiter:
                # If no rate limiter, allow request
                return f(*args, **kwargs)
            
            # Determine identifier
            if identifier_func:
                identifier = identifier_func()
            else:
                # Default: use API key or user ID or IP
                identifier = (
                    request.headers.get('X-API-Key') or
                    getattr(g, 'user_id', None) or
                    request.remote_addr
                )
            
            # Determine user tier
            if user_tier_func:
                user_tier = user_tier_func()
            else:
                user_tier = getattr(g, 'user_tier', 'free')
            
            # Check rate limit
            allowed, info = rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint,
                user_tier=user_tier,
                ip_address=request.remote_addr
            )
            
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': info.get('error', 'Too many requests'),
                    'limit_info': info
                })
                response.status_code = 429
                
                # Add rate limit headers
                if 'retry_after' in info:
                    response.headers['Retry-After'] = str(info['retry_after'])
                if 'limit' in info:
                    response.headers['X-RateLimit-Limit'] = str(info['limit'])
                if 'remaining' in info:
                    response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                if 'reset_time' in info:
                    response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
                
                return response
            
            # Add rate limit info to response headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers') and isinstance(info, dict):
                if 'limit' in info:
                    response.headers['X-RateLimit-Limit'] = str(info['limit'])
                if 'remaining' in info:
                    response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                if 'reset_time' in info:
                    response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
            
            return response
        
        return decorated_function
    return decorator

# Context manager for rate limiting
class RateLimitContext:
    def __init__(self, rate_limiter: RateLimiter, identifier: str, 
                 endpoint: str = 'api', user_tier: str = 'free'):
        self.rate_limiter = rate_limiter
        self.identifier = identifier
        self.endpoint = endpoint
        self.user_tier = user_tier
        self.allowed = False
        self.info = {}
    
    def __enter__(self):
        self.allowed, self.info = self.rate_limiter.check_rate_limit(
            self.identifier, self.endpoint, self.user_tier
        )
        
        if not self.allowed:
            raise RateLimitExceeded(self.info)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Could implement cleanup or logging here
        pass

class RateLimitExceeded(Exception):
    def __init__(self, info: Dict):
        self.info = info
        super().__init__(info.get('error', 'Rate limit exceeded'))

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

def init_rate_limiter(redis_client: redis.Redis = None, config: Dict = None) -> RateLimiter:
    """Initialize global rate limiter"""
    global _rate_limiter
    _rate_limiter = RateLimiter(redis_client, config)
    return _rate_limiter

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingBot Rate Limiter')
    parser.add_argument('action', choices=['test', 'stats', 'reset'])
    parser.add_argument('--identifier', help='Identifier to test/reset')
    parser.add_argument('--endpoint', default='api', help='Endpoint to test')
    parser.add_argument('--requests', type=int, default=10, help='Number of test requests')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    rate_limiter = RateLimiter()
    
    if args.action == 'test':
        identifier = args.identifier or 'test_user'
        print(f"Testing rate limiter with {args.requests} requests for {identifier}")
        
        for i in range(args.requests):
            allowed, info = rate_limiter.check_rate_limit(identifier, args.endpoint)
            status = "ALLOWED" if allowed else "BLOCKED"
            print(f"Request {i+1}: {status} - {info}")
            time.sleep(0.1)
    
    elif args.action == 'stats':
        stats = rate_limiter.get_statistics()
        print(json.dumps(stats, indent=2))
    
    elif args.action == 'reset':
        if args.identifier:
            rate_limiter.reset_limits(args.identifier, args.endpoint)
            print(f"Reset limits for {args.identifier} on {args.endpoint}")
        else:
            rate_limiter.reset_limits()
            print("Reset all limits")