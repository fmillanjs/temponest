"""Redis cache client with async support for TempoNest services.

This module provides a unified Redis caching interface that can be used
across all TempoNest services for caching JWT tokens, user permissions,
RAG query results, health checks, and dashboard metrics.
"""

import json
import hashlib
from typing import Any, Optional, Union
from redis.asyncio import Redis, ConnectionPool
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis cache client with JSON serialization support.

    Features:
    - Automatic JSON serialization/deserialization
    - Connection pooling for better performance
    - TTL (time-to-live) management
    - Pattern-based key deletion
    - Error handling and logging

    Example:
        ```python
        cache = RedisCache(url="redis://localhost:6379/0")
        await cache.connect()

        # Set value with 60 second TTL
        await cache.set("user:123", {"name": "John"}, ttl=60)

        # Get value
        user = await cache.get("user:123")

        # Delete by pattern
        await cache.delete("user:*")

        await cache.close()
        ```
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        max_connections: int = 10,
        decode_responses: bool = True,
    ):
        """Initialize Redis cache client.

        Args:
            url: Redis connection URL (default: redis://localhost:6379/0)
            max_connections: Maximum number of connections in pool
            decode_responses: Whether to decode responses to strings
        """
        self.url = url
        self.pool: Optional[ConnectionPool] = None
        self.redis: Optional[Redis] = None
        self.max_connections = max_connections
        self.decode_responses = decode_responses

    async def connect(self) -> None:
        """Establish connection pool to Redis."""
        try:
            self.pool = ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
            )
            self.redis = Redis(connection_pool=self.pool)
            # Test connection
            await self.redis.ping()
            logger.info(f"Connected to Redis at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("Closed Redis connection")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if key doesn't exist or expired
        """
        if not self.redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            value = await self.redis.get(key)
            if value is None:
                return None

            # If decode_responses is True, value is already a string
            return json.loads(value) if isinstance(value, str) else json.loads(value.decode())
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
    ) -> bool:
        """Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 3600 = 1 hour)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            serialized = json.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    async def delete(self, pattern: str) -> int:
        """Delete keys matching pattern.

        Args:
            pattern: Key pattern (supports wildcards like "user:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            keys = await self.redis.keys(pattern)
            if not keys:
                return 0

            deleted = await self.redis.delete(*keys)
            logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting keys with pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Update TTL for existing key.

        Args:
            key: Cache key
            ttl: New time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            return bool(await self.redis.expire(key, ttl))
        except Exception as e:
            logger.error(f"Error updating TTL for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        if not self.redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -2

    async def clear_all(self) -> bool:
        """Clear all keys from the current database.

        WARNING: This will delete ALL keys in the Redis database.
        Use with caution, preferably only in development/testing.

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")

        try:
            await self.redis.flushdb()
            logger.warning("Cleared all keys from Redis database")
            return True
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False

    @staticmethod
    def make_key(*parts: Union[str, int]) -> str:
        """Create a cache key from parts.

        Example:
            make_key("user", 123, "profile") -> "user:123:profile"

        Args:
            *parts: Key parts to join with colons

        Returns:
            Formatted cache key
        """
        return ":".join(str(part) for part in parts)

    @staticmethod
    def hash_key(value: str) -> str:
        """Create SHA256 hash of a value for use as cache key.

        Useful for long values like JWT tokens or query strings.

        Args:
            value: Value to hash

        Returns:
            Hex digest of SHA256 hash
        """
        return hashlib.sha256(value.encode()).hexdigest()
