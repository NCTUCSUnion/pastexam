import json
from datetime import datetime
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.main import app
from app.models.models import User, UserRoles
from app.utils.auth import get_current_user
from app.api.services.ai_exam import JobStatus


class FakeRedis:
    def __init__(self):
        self.metadata: dict[bytes, bytes] = {}
        self.expirations: dict[bytes, int | None] = {}
        self.enqueue_calls: list[tuple[str, dict]] = []
        self.job_statuses: dict[str, JobStatus | None] = {}
        self.results: dict[str, dict] = {}

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
        payload = {"archive_ids": [1, 2], "prompt": "Generate exam.", "temperature": 0.5}
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
async def test_get_task_status_returns_result(
    client: AsyncClient,
    make_user,
    fake_redis: FakeRedis,
):
    user = await make_user()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

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
        response = await client.get(f"/ai-exam/task/{task_id}")
        assert response.status_code == 200, response.json()
        body = response.json()
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
