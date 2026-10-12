from types import SimpleNamespace

import pytest

from app import worker


class FakeSession:
    def __init__(self, results):
        self._results = results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, _query):
        if not self._results:
            raise AssertionError("No more results configured")
        return self._results.pop(0)


class FakeObject:
    def __init__(self, data: bytes):
        self._data = data
        self.closed = False
        self.released = False

    def read(self):
        return self._data

    def close(self):
        self.closed = True

    def release_conn(self):
        self.released = True


class FakeStorage:
    def __init__(self):
        self.requests: list[tuple[str, str]] = []

    def get_object(self, bucket_name, object_name):
        self.requests.append((bucket_name, object_name))
        return FakeObject(b"%PDF-1.4 fake data")


class FakeGenAIClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.uploads: list[bytes] = []
        self.deleted: list[str] = []
        self.last_contents = None

        client = self

        class Files:
            def upload(self, *, file, config):
                data = file.read()
                client.uploads.append(data)
                return SimpleNamespace(name=f"uploaded-{len(client.uploads)}")

            def delete(self, *, name):
                client.deleted.append(name)

        class Models:
            def generate_content(self, *, model, contents, config):
                client.last_model = model
                client.last_config = config
                client.last_contents = contents
                if client.should_fail:
                    raise RuntimeError("generation failed")
                return SimpleNamespace(text="Generated exam content")

        self.files = Files()
        self.models = Models()


def _user_result(user):
    return SimpleNamespace(scalar_one_or_none=lambda: user)


def _archives_result(items):
    return SimpleNamespace(all=lambda: items)


@pytest.mark.asyncio
async def test_generate_exam_content_success(monkeypatch):
    user = SimpleNamespace(gemini_api_key="API_KEY")
    archive = SimpleNamespace(
        id=1,
        name="Midterm",
        object_name="archives/1.pdf",
        professor="Prof X",
        academic_year=2024,
        archive_type="final",
        deleted_at=None,
    )
    course = SimpleNamespace(name="Algorithms", deleted_at=None)
    fake_session = FakeSession(
        [_user_result(user), _archives_result([(archive, course)])]
    )

    monkeypatch.setattr(
        worker,
        "AsyncSession",
        lambda *_args, **_kwargs: fake_session,
    )
    monkeypatch.setattr(
        worker,
        "load_default_prompt_template",
        lambda: "Prompt {professor} {course_name} "
        "{archives_count} {archives_details}",
    )

    fake_storage = FakeStorage()
    monkeypatch.setattr(worker, "get_storage_client", lambda: fake_storage)

    fake_client = FakeGenAIClient()
    monkeypatch.setattr(worker.genai, "Client", lambda api_key: fake_client)

    result = await worker.generate_exam_content(
        archive_ids=[1],
        user_id=7,
        prompt=None,
        temperature=0.5,
    )

    assert result["success"] is True
    assert result["generated_content"].startswith("⚠️ 注意事項")
    assert len(result["archives_used"]) == 1
    assert fake_client.uploads
    assert fake_client.deleted == ["uploaded-1"]
    assert fake_storage.requests == [
        (worker.settings.RUSTFS_BUCKET_NAME, "archives/1.pdf")
    ]
    assert fake_client.last_model == worker.settings.GEMINI_MODEL
    assert fake_client.last_config == {"temperature": 0.5}

    # Without an explicit temperature the model's own default is used
    fake_client.uploads.clear()
    fake_client.deleted.clear()
    fake_session._results = [_user_result(user), _archives_result([(archive, course)])]
    await worker.generate_exam_content(archive_ids=[1], user_id=7)
    assert fake_client.last_config is None


@pytest.mark.asyncio
async def test_generate_exam_content_missing_user(monkeypatch):
    fake_session = FakeSession([_user_result(None)])
    monkeypatch.setattr(
        worker,
        "AsyncSession",
        lambda *_args, **_kwargs: fake_session,
    )

    with pytest.raises(ValueError, match="API key not found"):
        await worker.generate_exam_content(
            archive_ids=[1],
            user_id=99,
            prompt=None,
            temperature=0.7,
        )


@pytest.mark.asyncio
async def test_generate_exam_content_missing_archives(monkeypatch):
    user = SimpleNamespace(gemini_api_key="KEY")
    fake_session = FakeSession([_user_result(user), _archives_result([])])
    monkeypatch.setattr(
        worker,
        "AsyncSession",
        lambda *_args, **_kwargs: fake_session,
    )

    with pytest.raises(ValueError, match="Archives not found"):
        await worker.generate_exam_content(
            archive_ids=[1],
            user_id=8,
            prompt=None,
            temperature=0.7,
        )


@pytest.mark.asyncio
async def test_generate_exam_content_cleans_up_on_failure(monkeypatch):
    user = SimpleNamespace(gemini_api_key="KEY")
    archive = SimpleNamespace(
        id=1,
        name="Midterm",
        object_name="archives/1.pdf",
        professor="Prof",
        academic_year=2024,
        archive_type="final",
        deleted_at=None,
    )
    course = SimpleNamespace(name="Algorithms", deleted_at=None)
    fake_session = FakeSession(
        [_user_result(user), _archives_result([(archive, course)])]
    )
    monkeypatch.setattr(
        worker,
        "AsyncSession",
        lambda *_args, **_kwargs: fake_session,
    )
    monkeypatch.setattr(
        worker,
        "load_default_prompt_template",
        lambda: "Prompt {professor}",
    )
    monkeypatch.setattr(worker, "get_storage_client", FakeStorage)

    failing_client = FakeGenAIClient(should_fail=True)
    monkeypatch.setattr(worker.genai, "Client", lambda api_key: failing_client)

    with pytest.raises(RuntimeError, match="generation failed"):
        await worker.generate_exam_content(
            archive_ids=[1],
            user_id=1,
            prompt=None,
            temperature=1.0,
        )

    assert failing_client.deleted == ["uploaded-1"]


@pytest.mark.asyncio
async def test_generate_ai_exam_task_calls_generate(monkeypatch):
    called = {}

    async def fake_generate(**kwargs):
        called["kwargs"] = kwargs
        return {"success": True}

    monkeypatch.setattr(worker, "generate_exam_content", fake_generate)

    result = await worker.generate_ai_exam_task(
        None,
        {"archive_ids": [1, 2], "user_id": 3, "temperature": 0.9},
    )

    assert result == {"success": True}
    assert called["kwargs"]["archive_ids"] == [1, 2]
    assert called["kwargs"]["user_id"] == 3
    assert called["kwargs"]["temperature"] == 0.9


@pytest.mark.asyncio
async def test_get_redis_pool(monkeypatch):
    async def fake_create_pool(settings):
        return f"pool-for-{settings}"

    monkeypatch.setattr(worker, "create_pool", fake_create_pool)
    pool = await worker.get_redis_pool()
    assert pool == f"pool-for-{worker.WorkerSettings.redis_settings}"
