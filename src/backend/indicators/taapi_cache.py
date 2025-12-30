"""
TAAPI Cache - Simple in-memory cache for TAAPI indicator results
Reduces redundant API calls and respects rate limits
"""

import time
import logging
import json
from typing import Dict, Optional, Any

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.backend.config_loader import CONFIG

logger = logging.getLogger(__name__)


class TAAPICache:
    """
    Cache for TAAPI indicator results.
    Supports both in-memory (default) and Redis backends.
    
    Cache keys: f"{asset}:{interval}"
    TTL: configurable (default 60 seconds)
    """
    
    def __init__(self, ttl: int = 60):
        """
        Initialize cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 60)
        """
        self.ttl = ttl
        self.redis_client = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        redis_url = CONFIG.get("redis_url")
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info(f"TAAPI Cache initialized with Redis backend (TTL={ttl}s)")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}. Falling back to in-memory cache.")
                self.redis_client = None
        
        if not self.redis_client:
            logger.info(f"TAAPI Cache initialized with in-memory backend (TTL={ttl}s)")
    
    def get(self, asset: str, interval: str) -> Optional[Dict[str, Any]]:
        """
        Get cached indicators for asset and interval.
        
        Args:
            asset: Asset symbol (e.g., "BTC", "ETH")
            interval: Time interval (e.g., "5m", "1h")
            
        Returns:
            Cached data dict or None if expired/missing
        """
        key = f"taapi:{asset}:{interval}"
        
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return json.loads(data)
                logger.debug(f"Cache MISS (Redis): {key}")
                return None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return None
        
        # In-memory fallback
        if key not in self._cache:
            logger.debug(f"Cache MISS: {key}")
            return None
        
        entry = self._cache[key]
        age = time.time() - entry['timestamp']
        
        if age > self.ttl:
            logger.debug(f"Cache EXPIRED: {key} (age: {age:.1f}s)")
            del self._cache[key]
            return None
        
        logger.debug(f"Cache HIT: {key} (age: {age:.1f}s)")
        return entry['data']
    
    def set(self, asset: str, interval: str, data: Dict[str, Any]) -> None:
        """
        Store indicators in cache.
        
        Args:
            asset: Asset symbol
            interval: Time interval
            data: Indicator data to cache
        """
        key = f"taapi:{asset}:{interval}"
        
        if self.redis_client:
            try:
                self.redis_client.setex(key, self.ttl, json.dumps(data))
                logger.debug(f"Cache SET (Redis): {key}")
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # In-memory fallback
        self._cache[key] = {
            'timestamp': time.time(),
            'data': data
        }
        
        logger.debug(f"Cache SET: {key}")
    
    def clear(self) -> None:
        """Clear all cached data"""
        if self.redis_client:
            # We don't want to flush all redis, just our keys
            # But for simplicity in this context, we might not implement full clear for Redis
            # or use keys pattern matching which is slow.
            # Ideally we'd use a prefix or a separate DB.
            # Here we will just log a warning that clear is partial.
             logger.warning("Cache clear called but full Redis flush is unsafe. Skipping Redis flush.")
        
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"In-memory cache cleared ({count} entries removed)")
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        if self.redis_client:
             return {
                'backend': 'redis',
                'ttl_seconds': self.ttl,
                'status': 'connected'
            }

        now = time.time()
        active = 0
        expired = 0
        
        for entry in self._cache.values():
            age = now - entry['timestamp']
            if age <= self.ttl:
                active += 1
            else:
                expired += 1
        
        return {
            'backend': 'memory',
            'total_entries': len(self._cache),
            'active_entries': active,
            'expired_entries': expired,
            'ttl_seconds': self.ttl
        }


# Global cache instance
_cache_instance: Optional[TAAPICache] = None


def get_cache(ttl: int = 60) -> TAAPICache:
    """
    Get or create global TAAPI cache instance.
    
    Args:
        ttl: Time-to-live in seconds
        
    Returns:
        TAAPICache instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = TAAPICache(ttl=ttl)
    
    return _cache_instance
