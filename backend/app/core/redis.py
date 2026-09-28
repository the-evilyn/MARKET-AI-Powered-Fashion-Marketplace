import logging
from typing import AsyncGenerator, Optional
import redis.asyncio as aioredis
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    """Get or create singleton async Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    return redis_client


async def close_redis() -> None:
    """Close Redis connection pool gracefully."""
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency that yields async Redis client."""
    client = get_redis_client()
    yield client


async def check_redis_health() -> bool:
    """Ping Redis to test connectivity."""
    try:
        client = get_redis_client()
        return await client.ping() is True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False
