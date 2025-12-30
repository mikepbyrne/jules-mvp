"""Redis configuration and connection management."""

import json
from typing import Any

import redis.asyncio as redis

from src.config import get_settings

settings = get_settings()


class RedisClient:
    """Redis client wrapper with helper methods."""

    def __init__(self) -> None:
        """Initialize Redis client."""
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set JSON value in Redis."""
        serialized = json.dumps(value)
        if ttl:
            await self.client.setex(key, ttl, serialized)
        else:
            await self.client.set(key, serialized)

    async def get_json(self, key: str) -> Any | None:
        """Get JSON value from Redis."""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def delete(self, *keys: str) -> None:
        """Delete keys from Redis."""
        if keys:
            await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return bool(await self.client.exists(key))

    async def set_with_ttl(self, key: str, value: str, ttl: int) -> None:
        """Set value with TTL."""
        await self.client.setex(key, ttl, value)

    async def get(self, key: str) -> str | None:
        """Get string value."""
        return await self.client.get(key)

    async def incr(self, key: str) -> int:
        """Increment counter."""
        return await self.client.incr(key)

    async def expire(self, key: str, ttl: int) -> None:
        """Set expiration on key."""
        await self.client.expire(key, ttl)

    async def keys(self, pattern: str) -> list[str]:
        """Get keys matching pattern."""
        return await self.client.keys(pattern)


# Global Redis client instance
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Dependency to get Redis client."""
    return redis_client
