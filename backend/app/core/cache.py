"""
In-Memory Caching Service

Provides caching functionality without requiring Redis for MVP.
Uses cachetools library for efficient in-memory caching.

Cache Types:
- TTL Cache: Time-based expiration for general data
- LRU Cache: Least Recently Used eviction for limited-size caches
- Rate Limiting Cache: Track API request rates per user/IP

Note: This is an in-memory cache suitable for MVP.
For production with multiple servers, consider Redis.
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import json

from cachetools import TTLCache, LRUCache

from app.config import get_settings


class CacheService:
    """
    In-memory caching service using cachetools.

    Provides multiple cache types for different use cases:
    - Default cache: TTL-based for general caching
    - Session cache: User session data
    - Query cache: Database query results
    - Rate limit cache: API rate limiting
    """

    def __init__(self):
        """Initialize cache service with configured settings."""
        settings = get_settings()

        # Default TTL cache for general use
        self.default_cache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_default_ttl
        )

        # Session cache (shorter TTL, larger size)
        self.session_cache = TTLCache(
            maxsize=5000,
            ttl=1800  # 30 minutes
        )

        # Query result cache (longer TTL for expensive queries)
        self.query_cache = TTLCache(
            maxsize=500,
            ttl=600  # 10 minutes
        )

        # Rate limiting cache (tracks request counts)
        # Key format: "ratelimit:{user_id}:{window_start}"
        self.rate_limit_cache = TTLCache(
            maxsize=10000,
            ttl=settings.rate_limit_window
        )

        # User permission cache (reduce database lookups)
        self.permission_cache = TTLCache(
            maxsize=1000,
            ttl=300  # 5 minutes
        )

    def get(self, key: str, cache_type: str = "default") -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            cache_type: Type of cache to use (default, session, query, permission)

        Returns:
            Cached value or None if not found or expired
        """
        cache = self._get_cache(cache_type)
        return cache.get(key)

    def set(
        self,
        key: str,
        value: Any,
        cache_type: str = "default",
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache to use
            ttl: Optional custom TTL (not supported in cachetools, for API consistency)
        """
        cache = self._get_cache(cache_type)
        cache[key] = value

    def delete(self, key: str, cache_type: str = "default") -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
            cache_type: Type of cache to use
        """
        cache = self._get_cache(cache_type)
        cache.pop(key, None)

    def clear(self, cache_type: str = "default") -> None:
        """
        Clear entire cache.

        Args:
            cache_type: Type of cache to clear
        """
        cache = self._get_cache(cache_type)
        cache.clear()

    def exists(self, key: str, cache_type: str = "default") -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key
            cache_type: Type of cache to use

        Returns:
            True if key exists, False otherwise
        """
        cache = self._get_cache(cache_type)
        return key in cache

    def _get_cache(self, cache_type: str) -> TTLCache:
        """Get the appropriate cache based on type."""
        cache_map = {
            "default": self.default_cache,
            "session": self.session_cache,
            "query": self.query_cache,
            "rate_limit": self.rate_limit_cache,
            "permission": self.permission_cache,
        }
        return cache_map.get(cache_type, self.default_cache)

    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from arguments.

        Creates a consistent hash from the provided arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            MD5 hash of the serialized arguments
        """
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    # Session Management
    def set_session(self, session_id: str, data: dict) -> None:
        """Store session data."""
        self.set(f"session:{session_id}", data, cache_type="session")

    def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data."""
        return self.get(f"session:{session_id}", cache_type="session")

    def delete_session(self, session_id: str) -> None:
        """Delete session data."""
        self.delete(f"session:{session_id}", cache_type="session")

    # Permission Caching
    def set_user_permissions(self, user_id: str, permissions: list) -> None:
        """Cache user permissions."""
        self.set(f"permissions:{user_id}", permissions, cache_type="permission")

    def get_user_permissions(self, user_id: str) -> Optional[list]:
        """Retrieve cached user permissions."""
        return self.get(f"permissions:{user_id}", cache_type="permission")

    def invalidate_user_permissions(self, user_id: str) -> None:
        """Invalidate cached user permissions."""
        self.delete(f"permissions:{user_id}", cache_type="permission")

    # Rate Limiting
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit.

        Args:
            identifier: User ID, IP address, or other identifier
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current_time = datetime.utcnow()
        window_start = current_time.replace(
            second=0,
            microsecond=0
        ).timestamp()

        key = f"ratelimit:{identifier}:{window_start}"
        current_count = self.get(key, cache_type="rate_limit") or 0

        if current_count >= max_requests:
            return False, 0

        # Increment counter
        new_count = current_count + 1
        self.set(key, new_count, cache_type="rate_limit")

        return True, max_requests - new_count


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get the global cache service instance.

    Returns:
        CacheService: The global cache service instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(
    cache_type: str = "default",
    key_prefix: str = "",
    ttl: Optional[int] = None
):
    """
    Decorator for caching function results.

    Args:
        cache_type: Type of cache to use
        key_prefix: Prefix for cache key
        ttl: Optional custom TTL

    Example:
        @cached(cache_type="query", key_prefix="user_by_id")
        def get_user_by_id(user_id: str):
            # Expensive database query
            return user
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_result = cache.get(cache_key, cache_type=cache_type)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, cache_type=cache_type, ttl=ttl)

            return result

        return wrapper
    return decorator
