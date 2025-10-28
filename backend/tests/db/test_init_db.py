import subprocess
from contextlib import asynccontextmanager

import pytest
from app.core.config import settings
from app.db import init_db
from app.models.models import Course, Meme, User, CourseCategory


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalar(self):
        return self._value


class FakeSession:
    def __init__(self, admin_exists=False, course_count=0, meme_count=0):
        self.admin = User(name=settings.DEFAULT_ADMIN_NAME, email=settings.DEFAULT_ADMIN_EMAIL) if admin_exists else None
        self.course_count = course_count
        self.meme_count = meme_count
        self.added_courses: list[Course] = []
        self.added_memes: list[Meme] = []
        self.execute_step = 0
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, _query):
        if self.execute_step == 0:
            self.execute_step += 1
            return FakeScalarResult(self.admin)
        if self.execute_step == 1:
            self.execute_step += 1
            return FakeScalarResult(self.course_count)
        if self.execute_step == 2:
            self.execute_step += 1
            return FakeScalarResult(self.meme_count)
        raise AssertionError("Unexpected execute call")

    def add(self, obj):
        if isinstance(obj, User):
            self.admin = obj

    def add_all(self, objs):
        for obj in objs:
            if isinstance(obj, Course):
                self.added_courses.append(obj)
            elif isinstance(obj, Meme):
                self.added_memes.append(obj)

    async def commit(self):
        self.commits += 1

    async def refresh(self, _obj):
        return None


@pytest.mark.asyncio
async def test_init_db_creates_admin_and_seeds(monkeypatch):
    original_loader = init_db.load_seed_data
    original_loader.cache_clear()

    seed_payload = {
        "courses": [
            {"name": "Seed Course A", "category": CourseCategory.GENERAL.name},
            {"name": "Seed Course B", "category": CourseCategory.GRADUATE.name},
        ],
        "memes": [
            {"content": "Study hard!", "language": "en"},
        ],
    }

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    fake_session = FakeSession()

    @asynccontextmanager
    async def fake_session_factory():
        async with fake_session:
            yield fake_session

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Result())
    monkeypatch.setattr(init_db, "load_seed_data", lambda: seed_payload, raising=False)
    monkeypatch.setattr(init_db, "AsyncSessionLocal", lambda: fake_session_factory(), raising=False)

    await init_db.init_db()

    assert fake_session.admin is not None
    assert fake_session.admin.email == settings.DEFAULT_ADMIN_EMAIL
    assert len(fake_session.added_courses) == 2
    assert {course.name for course in fake_session.added_courses} == {
        "Seed Course A",
        "Seed Course B",
    }
    assert len(fake_session.added_memes) == 1
    assert fake_session.added_memes[0].content == "Study hard!"

    original_loader.cache_clear()


@pytest.mark.asyncio
async def test_init_db_fallback_when_migration_fails(monkeypatch):
    original_loader = init_db.load_seed_data
    original_loader.cache_clear()

    class FailResult:
        returncode = 1
        stdout = ""
        stderr = "boom"

    fake_session = FakeSession(admin_exists=True, course_count=1, meme_count=1)

    @asynccontextmanager
    async def fake_session_factory():
        async with fake_session:
            yield fake_session

    class FakeConnection:
        def __init__(self, tracker):
            self.tracker = tracker

        async def run_sync(self, fn):
            self.tracker["create_all"] += 1
            return None

        async def commit(self):
            return None

    class FakeEngine:
        def __init__(self, tracker):
            self.tracker = tracker

        def begin(self):
            tracker = self.tracker

            @asynccontextmanager
            async def ctx():
                yield FakeConnection(tracker)

            return ctx()

    tracker = {"create_all": 0}

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: FailResult())
    monkeypatch.setattr(init_db, "load_seed_data", lambda: {"courses": [], "memes": []}, raising=False)
    monkeypatch.setattr(init_db, "AsyncSessionLocal", lambda: fake_session_factory(), raising=False)
    monkeypatch.setattr(init_db, "engine", FakeEngine(tracker), raising=False)

    await init_db.init_db()

    assert tracker["create_all"] == 1
    original_loader.cache_clear()
