import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.services import statistics
from app.api.services.statistics import get_system_statistics
from app.models.models import (
    Archive,
    ArchiveType,
    Course,
    CourseCategory,
    User,
)
from app.utils import activity
from app.utils.redis import get_redis


@pytest_asyncio.fixture(autouse=True)
async def clear_statistics_cache():
    await get_redis().delete(statistics.CACHE_KEY)
    yield
    await get_redis().delete(statistics.CACHE_KEY)


@pytest_asyncio.fixture
async def statistics_records(session_maker):
    unique = uuid.uuid4().hex[:6]
    archive_ids: list[int] = []
    course_ids: list[int] = []
    user_id = None

    try:
        async with session_maker() as session:
            user = User(
                name=f"stats-user-{unique}",
                email=f"stats-{unique}@example.com",
                is_admin=False,
                is_local=True,
            )
            course = Course(
                name=f"Stats Course {unique}",
                category=CourseCategory.GENERAL,
            )
            empty_course = Course(
                name=f"Empty Stats Course {unique}",
                category=CourseCategory.GENERAL,
            )
            session.add_all([user, course, empty_course])
            await session.commit()
            for obj in (user, course, empty_course):
                await session.refresh(obj)

            user_id = user.id
            course_ids = [course.id, empty_course.id]

            active_archive = Archive(
                name="Active Archive",
                academic_year=2024,
                archive_type=ArchiveType.FINAL,
                professor="Professor X",
                has_answers=True,
                object_name=f"archives/test-{unique}.pdf",
                download_count=7,
                course_id=course.id,
                uploader_id=user.id,
            )
            deleted_archive = Archive(
                name="Deleted Archive",
                academic_year=2024,
                archive_type=ArchiveType.MIDTERM,
                professor="Professor Y",
                has_answers=False,
                object_name=f"archives/deleted-{unique}.pdf",
                download_count=3,
                course_id=course.id,
                uploader_id=user.id,
                deleted_at=datetime.now(UTC),
            )
            session.add_all([active_archive, deleted_archive])
            await session.commit()
            await session.refresh(active_archive)
            await session.refresh(deleted_archive)
            archive_ids = [active_archive.id, deleted_archive.id]

        yield
    finally:
        async with session_maker() as session:
            if archive_ids:
                await session.execute(delete(Archive).where(Archive.id.in_(archive_ids)))
            if course_ids:
                await session.execute(delete(Course).where(Course.id.in_(course_ids)))
            if user_id is not None:
                await session.execute(delete(User).where(User.id == user_id))
            await session.commit()


@pytest_asyncio.fixture
async def activity_user_ids():
    """Fake user ids whose activity keys are removed after the test."""
    ids = [900_000_000 + uuid.uuid4().int % 1_000_000 for _ in range(3)]
    dates: list[str] = []
    yield ids, dates
    await get_redis().zrem(activity.ONLINE_KEY, *[str(i) for i in ids])
    await get_redis().delete(*[f"{activity.SEEN_KEY_PREFIX}{i}" for i in ids])
    for date in dates:
        await get_redis().delete(f"{activity.ACTIVE_KEY_PREFIX}{date}")


@pytest.mark.asyncio
async def test_statistics_endpoint_has_basic_fields(client):
    response = await client.get("/statistics")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    for key in (
        "totalUsers",
        "totalDownloads",
        "onlineUsers",
        "totalArchives",
        "totalCourses",
        "activeToday",
    ):
        assert key in data


@pytest.mark.asyncio
async def test_statistics_endpoint_handles_errors(monkeypatch, client):
    async def failing_execute(self, *args, **kwargs):
        raise RuntimeError("db error")

    monkeypatch.setattr(
        AsyncSession,
        "execute",
        failing_execute,
        raising=False,
    )

    response = await client.get("/statistics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == "Failed to fetch statistics."
    assert payload["data"]["totalUsers"] == 0
    # Failures are not cached
    assert await get_redis().get(statistics.CACHE_KEY) is None


@pytest.mark.asyncio
async def test_statistics_counts(session_maker, statistics_records):
    async with session_maker() as session:
        stats = await get_system_statistics(db=session)

        assert stats["success"] is True
        data = stats["data"]

        total_users = await session.scalar(
            select(func.count(User.id)).where(User.deleted_at.is_(None))
        )
        courses_with_archives = await session.scalar(
            select(func.count(func.distinct(Archive.course_id)))
            .join(Course, Course.id == Archive.course_id)
            .where(Archive.deleted_at.is_(None), Course.deleted_at.is_(None))
        )
        total_archives = await session.scalar(
            select(func.count(Archive.id)).where(Archive.deleted_at.is_(None))
        )
        all_downloads = await session.scalar(
            select(func.coalesce(func.sum(Archive.download_count), 0))
        )

        assert data["totalUsers"] == total_users
        # The empty course is not counted
        assert data["totalCourses"] == courses_with_archives
        assert data["totalArchives"] == total_archives
        # Downloads of the deleted archive still count
        assert data["totalDownloads"] == all_downloads


@pytest.mark.asyncio
async def test_statistics_are_cached(session_maker, statistics_records, monkeypatch):
    async with session_maker() as session:
        first = await get_system_statistics(db=session)

        async def boom(*args, **kwargs):
            raise RuntimeError("should be served from cache")

        monkeypatch.setattr(session, "execute", boom)
        second = await get_system_statistics(db=session)

    assert second == first


@pytest.mark.asyncio
async def test_statistics_survive_redis_failure(session_maker, monkeypatch):
    async def broken(*args, **kwargs):
        raise ConnectionError("redis down")

    class BrokenRedis:
        get = set = staticmethod(broken)

    monkeypatch.setattr(statistics, "get_redis", lambda: BrokenRedis())
    monkeypatch.setattr(statistics, "count_online_users", broken)

    async with session_maker() as session:
        stats = await get_system_statistics(db=session)

    assert stats["success"] is True
    assert stats["data"]["onlineUsers"] == 0


@pytest.mark.asyncio
async def test_online_users_only_counts_recent_activity(activity_user_ids):
    ids, _ = activity_user_ids
    now = datetime.now(UTC)

    await activity.record_activity(ids[0], now=now)
    await activity.record_activity(ids[1], now=now - timedelta(minutes=10))

    members = {
        m for m, _ in await get_redis().zrangebyscore(
            activity.ONLINE_KEY, now.timestamp() - 300, "+inf", withscores=True
        )
    }
    assert str(ids[0]) in members
    assert str(ids[1]) not in members

    online = await activity.count_online_users(now=now)
    # The stale entry is pruned
    assert await get_redis().zscore(activity.ONLINE_KEY, str(ids[1])) is None
    assert online >= 1


@pytest.mark.asyncio
async def test_active_today_uses_taiwan_date(activity_user_ids):
    ids, dates = activity_user_ids
    dates += ["2024-01-01", "2024-01-02"]

    # 2024-01-01 16:30 UTC is already 2024-01-02 00:30 in Taiwan
    await activity.record_activity(ids[0], now=datetime(2024, 1, 1, 16, 30, tzinfo=UTC))
    # 2024-01-01 15:00 UTC is still 2024-01-01 23:00 in Taiwan
    await activity.record_activity(ids[1], now=datetime(2024, 1, 1, 15, 0, tzinfo=UTC))

    jan_2_taiwan = datetime(2024, 1, 1, 17, 0, tzinfo=UTC)
    jan_1_taiwan = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    assert await activity.count_active_today(now=jan_2_taiwan) == 1
    assert await activity.count_active_today(now=jan_1_taiwan) == 1


@pytest.mark.asyncio
async def test_record_activity_is_throttled(activity_user_ids):
    ids, _ = activity_user_ids
    now = datetime.now(UTC)

    await activity.record_activity(ids[2], now=now)
    await activity.record_activity(ids[2], now=now + timedelta(seconds=30))

    score = await get_redis().zscore(activity.ONLINE_KEY, str(ids[2]))
    assert score == pytest.approx(now.timestamp())


@pytest.mark.asyncio
async def test_record_activity_never_raises(monkeypatch):
    async def broken(*args, **kwargs):
        raise ConnectionError("redis down")

    class BrokenRedis:
        set = staticmethod(broken)

    monkeypatch.setattr(activity, "get_redis", lambda: BrokenRedis())
    await activity.record_activity(123)
