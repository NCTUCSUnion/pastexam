import logging

from app.utils.redis import get_redis

logger = logging.getLogger(__name__)

KEY_PREFIX = "ratelimit:"


async def get_retry_after(key: str, limit: int) -> int | None:
    """Return seconds until the window resets if `key` has reached `limit`, else None."""
    try:
        redis = get_redis()
        async with redis.pipeline(transaction=False) as pipe:
            pipe.get(f"{KEY_PREFIX}{key}")
            pipe.ttl(f"{KEY_PREFIX}{key}")
            count, ttl = await pipe.execute()
    except Exception:
        # Fail open: an unavailable Redis must not lock users out
        logger.warning("Failed to read rate limit %s", key, exc_info=True)
        return None
    if count is not None and int(count) >= limit:
        return max(ttl, 1)
    return None


async def record_hit(key: str, window_seconds: int) -> None:
    """Count one hit in a fixed window that starts with the first hit."""
    try:
        redis = get_redis()
        async with redis.pipeline(transaction=True) as pipe:
            pipe.incr(f"{KEY_PREFIX}{key}")
            pipe.expire(f"{KEY_PREFIX}{key}", window_seconds, nx=True)
            await pipe.execute()
    except Exception:
        logger.warning("Failed to record rate limit %s", key, exc_info=True)


async def hit(key: str, limit: int, window_seconds: int) -> int | None:
    """Count one hit atomically; return seconds to wait if it went over `limit`.

    Counting before the caller does any work means concurrent requests cannot all
    pass a check made before any of them was recorded.
    """
    try:
        redis = get_redis()
        async with redis.pipeline(transaction=True) as pipe:
            pipe.incr(f"{KEY_PREFIX}{key}")
            pipe.expire(f"{KEY_PREFIX}{key}", window_seconds, nx=True)
            pipe.ttl(f"{KEY_PREFIX}{key}")
            count, _, ttl = await pipe.execute()
    except Exception:
        # Fail open: an unavailable Redis must not lock users out
        logger.warning("Failed to record rate limit %s", key, exc_info=True)
        return None
    if int(count) > limit:
        return max(ttl, 1)
    return None


async def reset(key: str) -> None:
    try:
        await get_redis().delete(f"{KEY_PREFIX}{key}")
    except Exception:
        logger.warning("Failed to reset rate limit %s", key, exc_info=True)


async def consume(key: str, limit: int, window_seconds: int) -> int | None:
    """Record a hit unless the limit is reached; return seconds to wait if limited."""
    return await hit(key, limit, window_seconds)
