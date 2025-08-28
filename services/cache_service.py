"""
Redis-based Distributed Cache Service
Scalable caching with fallback mechanisms and monitoring
"""

import json
import pickle
import hashlib
import logging
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError

from backend.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based distributed cache service with fallback support
    Provides async operations, versioning, and metrics
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self._initialized = False
        self._fallback_cache: Dict[str, Any] = {}  # In-memory fallback
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "fallback_hits": 0,
            "evictions": 0
        }
        
    async def initialize(self) -> bool:
        """Initialize Redis connection with retry logic"""
        if self._initialized:
            return True
        
        if not settings.cache_enabled:
            logger.info("Cache disabled by configuration")
            return False
        
        if not settings.redis_url:
            logger.warning("Redis URL not configured, using in-memory fallback")
            return False
        
        try:
            # Create connection pool
            self.connection_pool = ConnectionPool.from_url(
                settings.redis_url,
                password=settings.redis_password,
                db=settings.redis_db,
                max_connections=settings.redis_pool_size,
                decode_responses=False,  # We'll handle encoding/decoding
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.redis_client.ping()
            
            self._initialized = True
            logger.info("✅ Redis cache initialized")
            return True
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Failed to initialize Redis: {e}")
            logger.info("Using in-memory fallback cache")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing cache: {e}")
            return False
    
    def _generate_key(self, namespace: str, key: str, version: Optional[int] = 1) -> str:
        """Generate cache key with namespace and version"""
        return f"{namespace}:v{version}:{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Try JSON first (more portable)
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data)
    
    async def get(
        self,
        key: str,
        namespace: str = "default",
        version: int = 1
    ) -> Optional[Any]:
        """Get value from cache with fallback support"""
        cache_key = self._generate_key(namespace, key, version)
        
        try:
            if self._initialized and self.redis_client:
                # Try Redis first
                data = await self.redis_client.get(cache_key)
                if data:
                    self._metrics["hits"] += 1
                    return self._deserialize(data)
                else:
                    self._metrics["misses"] += 1
                    return None
            else:
                # Use fallback cache
                if cache_key in self._fallback_cache:
                    value, expiry = self._fallback_cache[cache_key]
                    if expiry > datetime.now():
                        self._metrics["fallback_hits"] += 1
                        return value
                    else:
                        del self._fallback_cache[cache_key]
                        self._metrics["evictions"] += 1
                
                self._metrics["misses"] += 1
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._metrics["errors"] += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default",
        version: int = 1
    ) -> bool:
        """Set value in cache with TTL"""
        cache_key = self._generate_key(namespace, key, version)
        ttl = ttl or settings.cache_ttl
        
        try:
            if self._initialized and self.redis_client:
                # Use Redis
                serialized = self._serialize(value)
                await self.redis_client.setex(cache_key, ttl, serialized)
                return True
            else:
                # Use fallback cache
                expiry = datetime.now() + timedelta(seconds=ttl)
                self._fallback_cache[cache_key] = (value, expiry)
                
                # Clean up old entries if cache is too large
                if len(self._fallback_cache) > 1000:
                    self._cleanup_fallback_cache()
                
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._metrics["errors"] += 1
            return False
    
    async def delete(
        self,
        key: str,
        namespace: str = "default",
        version: int = 1
    ) -> bool:
        """Delete value from cache"""
        cache_key = self._generate_key(namespace, key, version)
        
        try:
            if self._initialized and self.redis_client:
                await self.redis_client.delete(cache_key)
            else:
                self._fallback_cache.pop(cache_key, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self._metrics["errors"] += 1
            return False
    
    async def exists(
        self,
        key: str,
        namespace: str = "default",
        version: int = 1
    ) -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_key(namespace, key, version)
        
        try:
            if self._initialized and self.redis_client:
                return await self.redis_client.exists(cache_key) > 0
            else:
                if cache_key in self._fallback_cache:
                    _, expiry = self._fallback_cache[cache_key]
                    return expiry > datetime.now()
                return False
                
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        pattern = f"{namespace}:*"
        count = 0
        
        try:
            if self._initialized and self.redis_client:
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor, match=pattern, count=100
                    )
                    if keys:
                        await self.redis_client.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            else:
                # Clear from fallback cache
                keys_to_delete = [k for k in self._fallback_cache if k.startswith(f"{namespace}:")]
                for key in keys_to_delete:
                    del self._fallback_cache[key]
                    count += 1
            
            self._metrics["evictions"] += count
            return count
            
        except Exception as e:
            logger.error(f"Cache clear namespace error: {e}")
            return 0
    
    async def increment(
        self,
        key: str,
        delta: int = 1,
        namespace: str = "counters",
        ttl: Optional[int] = None
    ) -> Optional[int]:
        """Atomic increment operation"""
        cache_key = self._generate_key(namespace, key, 1)
        
        try:
            if self._initialized and self.redis_client:
                value = await self.redis_client.incrby(cache_key, delta)
                if ttl:
                    await self.redis_client.expire(cache_key, ttl)
                return value
            else:
                # Fallback increment (not truly atomic)
                current = await self.get(key, namespace)
                new_value = (current or 0) + delta
                await self.set(key, new_value, ttl, namespace)
                return new_value
                
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    async def get_many(
        self,
        keys: List[str],
        namespace: str = "default",
        version: int = 1
    ) -> Dict[str, Any]:
        """Get multiple values at once"""
        result = {}
        
        if self._initialized and self.redis_client:
            cache_keys = [self._generate_key(namespace, k, version) for k in keys]
            
            try:
                values = await self.redis_client.mget(cache_keys)
                for key, value in zip(keys, values):
                    if value:
                        result[key] = self._deserialize(value)
                        self._metrics["hits"] += 1
                    else:
                        self._metrics["misses"] += 1
            except Exception as e:
                logger.error(f"Cache get_many error: {e}")
                self._metrics["errors"] += 1
        else:
            # Fallback to individual gets
            for key in keys:
                value = await self.get(key, namespace, version)
                if value is not None:
                    result[key] = value
        
        return result
    
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
        namespace: str = "default",
        version: int = 1
    ) -> bool:
        """Set multiple values at once"""
        ttl = ttl or settings.cache_ttl
        
        try:
            if self._initialized and self.redis_client:
                pipeline = self.redis_client.pipeline()
                for key, value in items.items():
                    cache_key = self._generate_key(namespace, key, version)
                    serialized = self._serialize(value)
                    pipeline.setex(cache_key, ttl, serialized)
                await pipeline.execute()
                return True
            else:
                # Fallback to individual sets
                for key, value in items.items():
                    await self.set(key, value, ttl, namespace, version)
                return True
                
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            self._metrics["errors"] += 1
            return False
    
    def _cleanup_fallback_cache(self):
        """Clean up expired entries from fallback cache"""
        now = datetime.now()
        expired_keys = [
            k for k, (_, expiry) in self._fallback_cache.items()
            if expiry <= now
        ]
        for key in expired_keys:
            del self._fallback_cache[key]
            self._metrics["evictions"] += 1
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics"""
        total_requests = self._metrics["hits"] + self._metrics["misses"]
        hit_rate = (
            (self._metrics["hits"] / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        metrics = {
            **self._metrics,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "is_redis": self._initialized,
            "fallback_size": len(self._fallback_cache)
        }
        
        if self._initialized and self.redis_client:
            try:
                info = await self.redis_client.info()
                metrics["redis_memory"] = info.get("used_memory_human", "N/A")
                metrics["redis_clients"] = info.get("connected_clients", 0)
            except:
                pass
        
        return metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check cache health"""
        try:
            if self._initialized and self.redis_client:
                await self.redis_client.ping()
                return {
                    "status": "healthy",
                    "type": "redis",
                    "connected": True
                }
            else:
                return {
                    "status": "healthy",
                    "type": "fallback",
                    "connected": False
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "type": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        self._initialized = False
        logger.info("Cache connections closed")


# Global cache instance
cache = CacheService()


# Cache decorator
def cached(
    ttl: int = 3600,
    namespace: str = "default",
    version: int = 1,
    key_prefix: str = ""
):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = hashlib.md5(
                ":".join(key_parts).encode()
            ).hexdigest()
            
            # Try to get from cache
            result = await cache.get(cache_key, namespace, version)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl, namespace, version)
            
            return result
        
        return wrapper
    return decorator
