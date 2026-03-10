"""Redis connection and caching utilities."""

from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """Get or create Redis client."""
    global _redis_client
    
    if _redis_client is None:
        logger.info(
            "Creating Redis client",
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
        )
        _redis_client = await redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
    
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client."""
    global _redis_client
    
    if _redis_client is not None:
        logger.info("Closing Redis client")
        await _redis_client.close()
        _redis_client = None


async def cache_get(key: str) -> Optional[str]:
    """Get value from cache."""
    client = await get_redis_client()
    return await client.get(key)


async def cache_set(key: str, value: str, ttl: Optional[int] = None) -> None:
    """Set value in cache with optional TTL."""
    client = await get_redis_client()
    if ttl:
        await client.setex(key, ttl, value)
    else:
        await client.set(key, value)


async def cache_delete(key: str) -> None:
    """Delete key from cache."""
    client = await get_redis_client()
    await client.delete(key)


async def cache_exists(key: str) -> bool:
    """Check if key exists in cache."""
    client = await get_redis_client()
    return bool(await client.exists(key))
