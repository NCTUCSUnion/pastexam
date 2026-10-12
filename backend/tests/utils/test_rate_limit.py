import uuid

import pytest

from app.utils import rate_limit
from app.utils.redis import get_redis


@pytest.fixture
def key():
    return f"test:{uuid.uuid4().hex}"


@pytest.mark.asyncio
async def test_consume_allows_up_to_limit_then_blocks(key):
    try:
        assert await rate_limit.consume(key, limit=3, window_seconds=60) is None
        assert await rate_limit.consume(key, limit=3, window_seconds=60) is None
        assert await rate_limit.consume(key, limit=3, window_seconds=60) is None

        retry_after = await rate_limit.consume(key, limit=3, window_seconds=60)
        assert retry_after is not None
        assert 0 < retry_after <= 60
    finally:
        await get_redis().delete(f"{rate_limit.KEY_PREFIX}{key}")


@pytest.mark.asyncio
async def test_window_starts_at_first_hit(key):
    try:
        await rate_limit.record_hit(key, window_seconds=60)
        await rate_limit.record_hit(key, window_seconds=600)
        # A later hit does not extend the window
        assert await get_redis().ttl(f"{rate_limit.KEY_PREFIX}{key}") <= 60
    finally:
        await get_redis().delete(f"{rate_limit.KEY_PREFIX}{key}")


@pytest.mark.asyncio
async def test_rate_limit_fails_open_when_redis_is_down(monkeypatch, key):
    class BrokenRedis:
        def pipeline(self, *args, **kwargs):
            raise ConnectionError("redis down")

    monkeypatch.setattr(rate_limit, "get_redis", lambda: BrokenRedis())

    assert await rate_limit.get_retry_after(key, limit=1) is None
    await rate_limit.record_hit(key, window_seconds=60)
    assert await rate_limit.consume(key, limit=1, window_seconds=60) is None
