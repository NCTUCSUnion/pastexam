import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from app.utils.discussion_hub import DiscussionHub


class FakeWebSocket:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.messages: list[dict] = []

    async def send_json(self, payload):
        if self.fail:
            raise RuntimeError("socket closed")
        self.messages.append(payload)


def _archive_id() -> int:
    # Avoid colliding with other test runs sharing the same Redis
    return uuid.uuid4().int % 1_000_000_000


async def _wait_for(predicate, timeout: float = 2.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("condition not met in time")
        await asyncio.sleep(0.02)


@pytest.mark.asyncio
async def test_event_published_by_one_worker_reaches_another():
    worker_a, worker_b = DiscussionHub(), DiscussionHub()
    archive_id = _archive_id()
    ws_a, ws_b = FakeWebSocket(), FakeWebSocket()
    try:
        await worker_a.connect(archive_id, ws_a)
        await worker_b.connect(archive_id, ws_b)

        await worker_b.publish(archive_id, {"type": "message", "id": 1})

        await _wait_for(lambda: ws_a.messages and ws_b.messages)
        assert ws_a.messages == [{"type": "message", "id": 1}]
        assert ws_b.messages == [{"type": "message", "id": 1}]
    finally:
        await worker_a.close()
        await worker_b.close()


@pytest.mark.asyncio
async def test_events_only_reach_sockets_of_the_same_archive():
    hub = DiscussionHub()
    archive_id, other_archive_id = _archive_id(), _archive_id()
    ws, other_ws = FakeWebSocket(), FakeWebSocket()
    try:
        await hub.connect(archive_id, ws)
        await hub.connect(other_archive_id, other_ws)

        await hub.publish(archive_id, {"type": "delete", "message_id": 3})

        await _wait_for(lambda: ws.messages)
        await asyncio.sleep(0.1)
        assert other_ws.messages == []
    finally:
        await hub.close()


@pytest.mark.asyncio
async def test_publish_failure_falls_back_to_local_delivery():
    hub = DiscussionHub()
    archive_id = _archive_id()
    ws = FakeWebSocket()
    try:
        await hub.connect(archive_id, ws)
        hub._client.publish = AsyncMock(side_effect=ConnectionError("redis down"))

        await hub.publish(archive_id, {"type": "message", "id": 2})

        assert ws.messages == [{"type": "message", "id": 2}]
    finally:
        await hub.close()


@pytest.mark.asyncio
async def test_dead_and_disconnected_sockets_are_removed():
    hub = DiscussionHub()
    archive_id = _archive_id()
    alive, dead, gone = FakeWebSocket(), FakeWebSocket(fail=True), FakeWebSocket()
    try:
        await hub.connect(archive_id, alive)
        await hub.connect(archive_id, dead)
        await hub.connect(archive_id, gone)
        hub.disconnect(archive_id, gone)

        await hub.publish(archive_id, {"type": "message", "id": 4})

        await _wait_for(lambda: alive.messages)
        assert gone.messages == []
        assert hub._sockets[archive_id] == {alive}
    finally:
        await hub.close()
