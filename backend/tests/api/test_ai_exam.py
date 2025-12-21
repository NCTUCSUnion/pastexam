import asyncio
import json
import threading
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import Update
from starlette.websockets import WebSocketDisconnect

from app.api.services.ai_exam import JobStatus
from app.main import app
from app.models.models import User, UserRoles
from app.utils.auth import get_current_user


class FakeRedis:
    def __init__(self):
        self.metadata: dict[bytes, bytes] = {}
        self.expirations: dict[bytes, int | None] = {}
        self.enqueue_calls: list[tuple[str, dict]] = []
        self.job_statuses: dict[str, JobStatus | None] = {}
        self.results: dict[str, dict] = {}
        self.streams: dict[str, list[tuple[str, dict[bytes, bytes]]]] = {}
        self.stream_events: dict[str, threading.Event] = {}
        self.stream_seq = 0

    async def scan_iter(self, match: str | None = None):
        prefix = None
        if match:
            prefix = match.rstrip("*")
        for key in list(self.metadata.keys()):
            key_str = key.decode("utf-8")
            if prefix and not key_str.startswith(prefix):
                continue
            yield key

    async def get(self, key: str | bytes):
        key_bytes = key if isinstance(key, bytes) else key.encode("utf-8")
        return self.metadata.get(key_bytes)

    async def set(self, key: str | bytes, value, ex: int | None = None):
        key_bytes = key if isinstance(key, bytes) else key.encode("utf-8")
        if isinstance(value, str):
            value_bytes = value.encode("utf-8")
        elif isinstance(value, bytes):
            value_bytes = value
        else:
            value_bytes = json.dumps(value).encode("utf-8")
        self.metadata[key_bytes] = value_bytes
        self.expirations[key_bytes] = ex
        return True

    async def enqueue_job(self, name: str, task_data: dict):
        job_id = f"job-{len(self.enqueue_calls) + 1}"
        self.enqueue_calls.append((name, task_data))
        self.job_statuses[job_id] = JobStatus.queued
        return SimpleNamespace(job_id=job_id)

    async def delete(self, key: str | bytes):
        key_bytes = key if isinstance(key, bytes) else key.encode("utf-8")
        self.metadata.pop(key_bytes, None)
        self.expirations.pop(key_bytes, None)
        return 1

    async def xadd(
        self,
        name: str,
        fields: dict,
        maxlen: int | None = None,
        approximate: bool = True,
    ):
        self.stream_seq += 1
        entry_id = f"{self.stream_seq}-0"
        encoded: dict[bytes, bytes] = {}
        for k, v in fields.items():
            key_b = k if isinstance(k, bytes) else str(k).encode("utf-8")
            val_b = v if isinstance(v, bytes) else str(v).encode("utf-8")
            encoded[key_b] = val_b

        stream = self.streams.setdefault(name, [])
        stream.append((entry_id, encoded))
        if maxlen and len(stream) > maxlen:
            self.streams[name] = stream[-maxlen:]

        event = self.stream_events.setdefault(name, threading.Event())
        event.set()
        return entry_id

    async def xread(
        self, streams: dict, count: int | None = None, block: int | None = None
    ):
        (name, last_id) = next(iter(streams.items()))

        def parse_id(val: str) -> int:
            try:
                return int(str(val).split("-", 1)[0])
            except Exception:
                return 0

        last_num = parse_id(last_id)

        def get_entries():
            out = []
            for entry_id, fields in self.streams.get(name, []):
                if parse_id(entry_id) > last_num:
                    out.append((entry_id, fields))
            return out

        entries = get_entries()
        if not entries and block:
            event = self.stream_events.setdefault(name, threading.Event())
            event.clear()
            await asyncio.to_thread(event.wait, block / 1000.0)
            entries = get_entries()

        if count:
            entries = entries[:count]

        if not entries:
            return []
        return [(name, entries)]

    async def expire(self, _key: str, _seconds: int):
        return True


class FakeJob:
    def __init__(self, job_id: str, redis: FakeRedis):
        self.job_id = job_id
        self.redis = redis

    async def status(self):
        return self.redis.job_statuses.get(self.job_id)

    async def result(self):
        return self.redis.results.get(self.job_id)


@pytest.fixture
def fake_redis(monkeypatch) -> FakeRedis:
    redis = FakeRedis()

    async def get_pool():
        return redis

    monkeypatch.setattr("app.worker.get_redis_pool", get_pool)
    monkeypatch.setattr("app.api.services.ai_exam.Job", FakeJob)
    monkeypatch.setattr("arq.jobs.Job", FakeJob)
    return redis


@pytest.mark.asyncio
async def test_submit_generate_task_requires_archive_ids(
    client: AsyncClient,
    make_user,
):
    user = await make_user()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    try:
        response = await client.post(
            "/ai-exam/generate",
            json={"archive_ids": [], "prompt": "ignored"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "At least 1 archive is required"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_submit_generate_task_enqueues_job(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
):
    user = await make_user()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    try:
        payload = {
            "archive_ids": [1, 2],
            "prompt": "Generate exam.",
            "temperature": 0.5,
        }
        response = await client.post("/ai-exam/generate", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending"
        task_id = body["task_id"]
        assert task_id == "job-1"

        assert fake_redis.enqueue_calls == [
            ("generate_ai_exam_task", {**payload, "user_id": user.id})
        ]

        metadata_key = f"task_metadata:{task_id}".encode("utf-8")
        assert metadata_key in fake_redis.metadata
        metadata = json.loads(fake_redis.metadata[metadata_key].decode("utf-8"))
        assert metadata["user_id"] == user.id
        assert metadata["archive_ids"] == [1, 2]
        assert metadata["status"] == "pending"
        assert fake_redis.expirations[metadata_key] == 86400
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_submit_generate_task_conflict_when_active_job(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
):
    user = await make_user()
    await fake_redis.set(
        "task_metadata:job-existing",
        {"user_id": user.id, "status": "pending"},
    )
    fake_redis.job_statuses["job-existing"] = JobStatus.in_progress

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    try:
        response = await client.post(
            "/ai-exam/generate",
            json={"archive_ids": [1], "prompt": "Test"},
        )
        assert response.status_code == 409
        assert "active task" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_submit_generate_task_ignores_missing_metadata(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
):
    user = await make_user()
    fake_redis.metadata[b"task_metadata:stale"] = None

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    try:
        response = await client.post(
            "/ai-exam/generate",
            json={"archive_ids": [1], "prompt": "Test"},
        )
        assert response.status_code == 200
        assert response.json()["task_id"] == "job-1"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_task_status_returns_result(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
    monkeypatch,
):
    user = await make_user()

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    task_id = "task-123"
    created_at = datetime.utcnow().isoformat()

    await fake_redis.set(
        f"task_metadata:{task_id}",
        json.dumps(
            {
                "user_id": user.id,
                "archive_ids": [1],
                "created_at": created_at,
            }
        ),
        ex=86400,
    )
    fake_redis.job_statuses[task_id] = JobStatus.complete
    fake_redis.results[task_id] = {"success": True, "generated_content": "Example"}

    try:
        monkeypatch.setattr(
            "app.api.services.ai_exam.get_ws_token_payload", fake_ws_payload
        )
        with TestClient(app) as ws_client:
            with ws_client.websocket_connect(f"/ai-exam/ws/task/{task_id}") as ws:
                body = ws.receive_json()
        assert body["task_id"] == task_id
        assert body["status"] == "complete"
        assert body["created_at"] == created_at
        assert body["result"] == {
            "success": True,
            "generated_content": "Example",
        }
        assert body["completed_at"] is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_task_status_reports_not_found_when_job_missing(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
    monkeypatch,
):
    user = await make_user()
    task_id = "job-missing"

    await fake_redis.set(
        f"task_metadata:{task_id}",
        json.dumps(
            {
                "user_id": user.id,
                "created_at": datetime.utcnow().isoformat(),
            }
        ),
    )
    fake_redis.job_statuses[task_id] = None

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    try:
        monkeypatch.setattr(
            "app.api.services.ai_exam.get_ws_token_payload", fake_ws_payload
        )
        with TestClient(app) as ws_client:
            with ws_client.websocket_connect(f"/ai-exam/ws/task/{task_id}") as ws:
                body = ws.receive_json()
        assert body["status"] == "not_found"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_task_status_stream_emits_in_progress_transition(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
    monkeypatch,
):
    user = await make_user()

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    monkeypatch.setattr(
        "app.api.services.ai_exam.get_ws_token_payload", fake_ws_payload
    )

    task_id = "job-transition"
    created_at = datetime.utcnow().isoformat()
    await fake_redis.set(
        f"task_metadata:{task_id}",
        json.dumps({"user_id": user.id, "created_at": created_at}),
    )

    fake_redis.job_statuses[task_id] = JobStatus.queued

    with TestClient(app) as ws_client:
        with ws_client.websocket_connect(f"/ai-exam/ws/task/{task_id}") as ws:
            first = ws.receive_json()
            assert first["status"] == "pending"

            await fake_redis.xadd(
                f"ai_exam:task_events:{task_id}",
                {"status": "in_progress"},
            )
            second = ws.receive_json()
            assert second["status"] == "in_progress"

            fake_redis.job_statuses[task_id] = JobStatus.complete
            fake_redis.results[task_id] = {
                "success": True,
                "generated_content": "Example",
            }
            await fake_redis.xadd(
                f"ai_exam:task_events:{task_id}",
                {
                    "status": "complete",
                },
            )
            final = ws.receive_json()
            assert final["status"] == "complete"
            assert final["result"]["generated_content"] == "Example"


@pytest.mark.asyncio
async def test_get_task_status_handles_result_error(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
    monkeypatch,
):
    user = await make_user()
    task_id = "job-error"
    created_at = datetime.utcnow().isoformat()

    await fake_redis.set(
        f"task_metadata:{task_id}",
        json.dumps({"user_id": user.id, "created_at": created_at}),
    )
    fake_redis.job_statuses[task_id] = JobStatus.complete
    fake_redis.results[task_id] = None

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    try:
        monkeypatch.setattr(
            "app.api.services.ai_exam.get_ws_token_payload", fake_ws_payload
        )
        with TestClient(app) as ws_client:
            with ws_client.websocket_connect(f"/ai-exam/ws/task/{task_id}") as ws:
                body = ws.receive_json()
        assert body["status"] == "complete"
        assert body["result"] is None
        assert body["completed_at"] is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_api_key_persists_value(
    client: AsyncClient,
    make_user,
    session_maker,
    monkeypatch,
):
    user = await make_user(gemini_api_key=None)

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    class FakeModels:
        def __init__(self):
            self.calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(text="ok")

    class FakeClient:
        instances = []

        def __init__(self, api_key):
            self.api_key = api_key
            self.models = FakeModels()
            FakeClient.instances.append(self)

    monkeypatch.setattr("google.genai.Client", FakeClient)

    try:
        new_key = "abc12345XYZ"
        response = await client.put(
            "/ai-exam/api-key",
            json={"gemini_api_key": new_key},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["has_api_key"] is True
        assert body["api_key_masked"] == f"****{new_key[-4:]}"
        assert FakeClient.instances and FakeClient.instances[0].api_key == new_key
        assert FakeClient.instances[0].models.calls

        async with session_maker() as session:
            refreshed = await session.get(User, user.id)
            assert refreshed.gemini_api_key == new_key
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_task_success(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
):
    user = await make_user()
    task_id = "job-42"

    await fake_redis.set(
        f"task_metadata:{task_id}",
        json.dumps({"user_id": user.id}),
    )
    fake_redis.results[f"arq:result:{task_id}"] = {"some": "data"}

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    try:
        response = await client.delete(f"/ai-exam/task/{task_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert f"task_metadata:{task_id}".encode("utf-8") not in fake_redis.metadata
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_task_forbidden(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
):
    user = await make_user()
    await fake_redis.set(
        "task_metadata:job-owner",
        json.dumps({"user_id": user.id + 1}),
    )

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    try:
        response = await client.delete("/ai-exam/task/job-owner")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_task_not_found(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
):
    user = await make_user()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    try:
        response = await client.delete("/ai-exam/task/unknown")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_task_status_not_found(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
    monkeypatch,
):
    user = await make_user()

    try:

        async def fake_ws_payload(websocket):
            return {"uid": user.id, "exp": 4102444800}

        monkeypatch.setattr(
            "app.api.services.ai_exam.get_ws_token_payload", fake_ws_payload
        )
        with TestClient(app) as ws_client:
            with pytest.raises(WebSocketDisconnect) as exc:
                with ws_client.websocket_connect("/ai-exam/ws/task/missing") as ws:
                    ws.receive_json()
        assert exc.value.code == 1008
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_task_status_forbidden(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
    monkeypatch,
):
    user = await make_user()
    await fake_redis.set(
        "task_metadata:job-secret",
        json.dumps({"user_id": user.id + 99}),
    )

    try:

        async def fake_ws_payload(websocket):
            return {"uid": user.id, "exp": 4102444800}

        monkeypatch.setattr(
            "app.api.services.ai_exam.get_ws_token_payload", fake_ws_payload
        )
        with TestClient(app) as ws_client:
            with pytest.raises(WebSocketDisconnect) as exc:
                with ws_client.websocket_connect("/ai-exam/ws/task/job-secret") as ws:
                    ws.receive_json()
        assert exc.value.code == 1008
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_task_status_handles_exception(
    monkeypatch,
    client,
    make_user,
):
    user = await make_user()

    async def raise_error():
        raise RuntimeError("boom")

    try:

        async def fake_ws_payload(websocket):
            return {"uid": user.id, "exp": 4102444800}

        monkeypatch.setattr(
            "app.api.services.ai_exam.get_ws_token_payload", fake_ws_payload
        )
        monkeypatch.setattr("app.worker.get_redis_pool", raise_error)
        with TestClient(app) as ws_client:
            with pytest.raises(WebSocketDisconnect) as exc:
                with ws_client.websocket_connect("/ai-exam/ws/task/any") as ws:
                    ws.receive_json()
        assert exc.value.code == 1011
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_task_handles_exception(
    monkeypatch,
    client,
    make_user,
):
    user = await make_user()

    async def raise_error():
        raise RuntimeError("boom")

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    monkeypatch.setattr("app.worker.get_redis_pool", raise_error)

    try:
        response = await client.delete("/ai-exam/task/any")
        assert response.status_code == 500
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_api_key_status_with_key(
    client: AsyncClient,
    make_user,
):
    user = await make_user(gemini_api_key="secret-1234")

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    try:
        response = await client.get("/ai-exam/api-key")
        assert response.status_code == 200
        body = response.json()
        assert body["has_api_key"] is True
        assert body["api_key_masked"] == "****1234"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_api_key_status_user_missing(
    client: AsyncClient,
    make_user,
    session_maker,
):
    user = await make_user()

    async with session_maker() as session:
        db_user = await session.get(User, user.id)
        await session.delete(db_user)
        await session.commit()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    try:
        response = await client.get("/ai-exam/api-key")
        assert response.status_code == 200
        body = response.json()
        assert body == {"has_api_key": False, "api_key_masked": None}
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_api_key_invalid_key(
    client: AsyncClient,
    make_user,
    monkeypatch,
):
    user = await make_user()

    class ErrorClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = self

        def generate_content(self, **kwargs):
            raise ValueError("API key invalid")

    monkeypatch.setattr("google.genai.Client", ErrorClient)

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    try:
        response = await client.put(
            "/ai-exam/api-key",
            json={"gemini_api_key": "bad-key"},
        )
        assert response.status_code == 400
        assert "Invalid API Key" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_api_key_handles_other_errors(
    client: AsyncClient,
    make_user,
    monkeypatch,
):
    user = await make_user()

    class NoopClient:
        def __init__(self, api_key):
            self.api_key = api_key
            self.models = self

        def generate_content(self, **kwargs):
            return SimpleNamespace(text="ok")

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    original_execute = AsyncSession.execute

    async def failing_execute(self, statement, *args, **kwargs):
        if isinstance(statement, Update):
            raise RuntimeError("db down")
        return await original_execute(self, statement, *args, **kwargs)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    monkeypatch.setattr("google.genai.Client", NoopClient)
    monkeypatch.setattr(
        AsyncSession,
        "execute",
        failing_execute,
        raising=False,
    )

    try:
        response = await client.put(
            "/ai-exam/api-key",
            json={"gemini_api_key": "123"},
        )
        assert response.status_code == 500
    finally:
        app.dependency_overrides.pop(get_current_user, None)
