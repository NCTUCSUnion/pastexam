import logging
from datetime import UTC, datetime, timedelta, timezone

from app.utils.redis import get_redis

logger = logging.getLogger(__name__)

# Taiwan has no daylight saving time, so a fixed offset is exact
TAIPEI = timezone(timedelta(hours=8))

ONLINE_KEY = "stats:online"
ONLINE_WINDOW_SECONDS = 5 * 60
ACTIVE_KEY_PREFIX = "stats:active:"
ACTIVE_KEY_TTL_SECONDS = 3 * 24 * 60 * 60
SEEN_KEY_PREFIX = "stats:seen:"
SEEN_THROTTLE_SECONDS = 60


def _active_key(now: datetime) -> str:
    return f"{ACTIVE_KEY_PREFIX}{now.astimezone(TAIPEI):%Y-%m-%d}"


async def record_activity(user_id: int, now: datetime | None = None) -> None:
    """Mark a user as active; never fails the request that triggered it."""
    now = now or datetime.now(UTC)
    try:
        # Write at most once per user per minute
        redis = get_redis()
        first_seen = await redis.set(
            f"{SEEN_KEY_PREFIX}{user_id}", 1, nx=True, ex=SEEN_THROTTLE_SECONDS
        )
        if not first_seen:
            return

        active_key = _active_key(now)
        async with redis.pipeline(transaction=False) as pipe:
            pipe.zadd(ONLINE_KEY, {str(user_id): now.timestamp()})
            pipe.pfadd(active_key, str(user_id))
            pipe.expire(active_key, ACTIVE_KEY_TTL_SECONDS)
            await pipe.execute()
    except Exception:
        logger.warning("Failed to record user activity", exc_info=True)


async def count_online_users(now: datetime | None = None) -> int:
    cutoff = (now or datetime.now(UTC)).timestamp() - ONLINE_WINDOW_SECONDS
    async with get_redis().pipeline(transaction=False) as pipe:
        pipe.zremrangebyscore(ONLINE_KEY, "-inf", cutoff)
        pipe.zcard(ONLINE_KEY)
        _, count = await pipe.execute()
    return count


async def count_active_today(now: datetime | None = None) -> int:
    return await get_redis().pfcount(_active_key(now or datetime.now(UTC)))
