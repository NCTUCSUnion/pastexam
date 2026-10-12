import asyncio
import json
import logging
from contextlib import suppress

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "discussion:"
READY_TIMEOUT_SECONDS = 1.0
RETRY_DELAY_SECONDS = 1.0


class DiscussionHub:
    """
    Fan out discussion events to WebSocket clients across all uvicorn workers.

    Each worker only holds its own connections, so events are published to Redis and
    every worker delivers them to its local sockets. If Redis is unavailable, events
    are delivered to this worker's sockets only.
    """

    def __init__(self) -> None:
        self._sockets: dict[int, set[WebSocket]] = {}
        self._client: aioredis.Redis | None = None
        self._listener: asyncio.Task | None = None
        self._ready: asyncio.Event | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, archive_id: int, websocket: WebSocket) -> None:
        self._sockets.setdefault(archive_id, set()).add(websocket)
        await self._ensure_listener()

    def disconnect(self, archive_id: int, websocket: WebSocket) -> None:
        sockets = self._sockets.get(archive_id)
        if sockets:
            sockets.discard(websocket)
            if not sockets:
                self._sockets.pop(archive_id, None)

    async def publish(self, archive_id: int, payload: dict) -> None:
        await self._ensure_listener()
        # Without a live subscription this worker would miss its own event
        if not self._ready.is_set():
            await self._deliver_local(archive_id, payload)
        try:
            await self._client.publish(
                f"{CHANNEL_PREFIX}{archive_id}", json.dumps(payload)
            )
        except Exception:
            logger.warning("Failed to publish discussion event", exc_info=True)
            if self._ready.is_set():
                await self._deliver_local(archive_id, payload)

    async def close(self) -> None:
        if self._listener is not None:
            self._listener.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await self._listener
        if self._client is not None:
            with suppress(Exception):
                await self._client.aclose()
        self._listener = None
        self._client = None
        self._ready = None
        self._loop = None

    async def _ensure_listener(self) -> None:
        loop = asyncio.get_running_loop()
        # A new event loop (e.g. a fresh test client) cannot reuse the old connection
        if self._listener is None or self._listener.done() or self._loop is not loop:
            self._loop = loop
            self._ready = asyncio.Event()
            self._client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            self._listener = loop.create_task(self._listen(self._client, self._ready))

        with suppress(TimeoutError):
            await asyncio.wait_for(self._ready.wait(), timeout=READY_TIMEOUT_SECONDS)

    async def _listen(self, client: aioredis.Redis, ready: asyncio.Event) -> None:
        while True:
            pubsub = client.pubsub()
            try:
                await pubsub.psubscribe(f"{CHANNEL_PREFIX}*")
                ready.set()
                async for message in pubsub.listen():
                    if message.get("type") != "pmessage":
                        continue
                    try:
                        archive_id = int(message["channel"].removeprefix(CHANNEL_PREFIX))
                        payload = json.loads(message["data"])
                    except (ValueError, TypeError):
                        continue
                    await self._deliver_local(archive_id, payload)
            except asyncio.CancelledError:
                raise
            except Exception:
                ready.clear()
                logger.warning("Discussion subscription lost, retrying", exc_info=True)
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            finally:
                with suppress(Exception):
                    await pubsub.aclose()

    async def _deliver_local(self, archive_id: int, payload: dict) -> None:
        sockets = self._sockets.get(archive_id)
        if not sockets:
            return

        dead: list[WebSocket] = []
        for ws in list(sockets):
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001 - a disconnected socket is removed
                dead.append(ws)

        for ws in dead:
            self.disconnect(archive_id, ws)


discussion_hub = DiscussionHub()
