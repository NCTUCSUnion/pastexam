import asyncio
import subprocess
from contextlib import asynccontextmanager

import pytest

from app.core.config import settings
from app.db import init_db
from app.models.models import Course, CourseCategory, Meme, User


@asynccontextmanager
async def _no_lock():
    yield


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalar(self):
        return self._value


class FakeSession:
    def __init__(self, admin_exists=False, course_count=0, meme_count=0):
        self.admin = (
            User(
                name=settings.DEFAULT_ADMIN_NAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
            )
            if admin_exists
            else None
        )
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
            {
                "name": "Seed Course A",
                "category": CourseCategory.GENERAL.name,
            },
            {
                "name": "Seed Course B",
                "category": CourseCategory.GRADUATE.name,
            },
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

    monkeypatch.setattr(init_db, "_migration_lock", _no_lock)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: Result(),
    )
    monkeypatch.setattr(
        init_db,
        "load_seed_data",
        lambda: seed_payload,
        raising=False,
    )
    monkeypatch.setattr(
        init_db,
        "AsyncSessionLocal",
        lambda: fake_session_factory(),
        raising=False,
    )

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


def _patch_init_db(monkeypatch, *, returncode, stderr, fake_session):
    class Result:
        stdout = ""

    Result.returncode = returncode
    Result.stderr = stderr

    @asynccontextmanager
    async def fake_session_factory():
        async with fake_session:
            yield fake_session

    monkeypatch.setattr(init_db, "_migration_lock", _no_lock)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Result())
    monkeypatch.setattr(
        init_db, "load_seed_data", lambda: {"courses": [], "memes": []}, raising=False
    )
    monkeypatch.setattr(
        init_db, "AsyncSessionLocal", lambda: fake_session_factory(), raising=False
    )


@pytest.mark.asyncio
async def test_init_db_refuses_to_start_when_migration_fails(monkeypatch):
    init_db.load_seed_data.cache_clear()
    fake_session = FakeSession(admin_exists=True, course_count=1, meme_count=1)
    _patch_init_db(
        monkeypatch, returncode=1, stderr="relation already exists", fake_session=fake_session
    )

    with pytest.raises(RuntimeError, match="relation already exists"):
        await init_db.init_db()


@pytest.mark.asyncio
async def test_init_db_starts_when_database_is_newer_than_the_code(monkeypatch):
    init_db.load_seed_data.cache_clear()
    fake_session = FakeSession(admin_exists=True, course_count=1, meme_count=1)
    _patch_init_db(
        monkeypatch,
        returncode=1,
        stderr="Can't locate revision identified by 'ffffffffffff'",
        fake_session=fake_session,
    )

    # A rollback to an older release must still boot
    await init_db.init_db()


@pytest.mark.asyncio
async def test_migration_lock_lets_one_worker_migrate_at_a_time(monkeypatch):
    from app.db import session as db_session

    # Use the per-test engine from conftest
    monkeypatch.setattr(init_db, "engine", db_session.engine)
    events: list[str] = []

    async def migrate(name: str):
        async with init_db._migration_lock():
            events.append(f"{name}-start")
            await asyncio.sleep(0.2)
            events.append(f"{name}-end")

    await asyncio.gather(migrate("a"), migrate("b"))

    # The second worker only starts after the first one released the lock
    assert events[0].endswith("-start") and events[1].endswith("-end")
    assert events[0][0] == events[1][0]
    assert events[2][0] == events[3][0] != events[0][0]
