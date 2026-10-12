import asyncio
from weakref import WeakKeyDictionary

import redis.asyncio as aioredis

from app.core.config import settings

_clients: WeakKeyDictionary[asyncio.AbstractEventLoop, aioredis.Redis] = (
    WeakKeyDictionary()
)


def get_redis() -> aioredis.Redis:
    """Return a Redis client bound to the running event loop."""
    # Connections cannot be shared across event loops (tests run several)
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        _clients[loop] = client
    return client
