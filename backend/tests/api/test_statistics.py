import uuid
from datetime import datetime, timedelta, timezone

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


@pytest.fixture
def statistics_now(monkeypatch):
    frozen_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return frozen_now.replace(tzinfo=None)
            return frozen_now.astimezone(tz)

    monkeypatch.setattr(statistics, "datetime", FrozenDatetime)
    return frozen_now


@pytest_asyncio.fixture
async def statistics_records(session_maker, statistics_now):
    earlier = statistics_now - timedelta(days=1)
    unique = uuid.uuid4().hex[:6]
    archive_ids: list[int] = []
    user_ids: list[int] = []
    course_id = None

    try:
        async with session_maker() as session:
            online_user = User(
                name=f"online-user-{unique}",
                email=f"online-{unique}@example.com",
                is_admin=False,
                is_local=True,
                last_login=statistics_now,
                last_logout=None,
            )
            offline_user = User(
                name=f"offline-user-{unique}",
                email=f"offline-{unique}@example.com",
                is_admin=False,
                is_local=True,
                last_login=earlier,
                last_logout=earlier,
            )
            course = Course(
                name=f"Stats Course {unique}",
                category=CourseCategory.GENERAL,
            )
            session.add_all([online_user, offline_user, course])
            await session.commit()
            await session.refresh(online_user)
            await session.refresh(offline_user)
            await session.refresh(course)

            user_ids = [online_user.id, offline_user.id]
            course_id = course.id

            active_archive = Archive(
                name="Active Archive",
                academic_year=2024,
                archive_type=ArchiveType.FINAL,
                professor="Professor X",
                has_answers=True,
                object_name=f"archives/test-{unique}.pdf",
                download_count=7,
                course_id=course.id,
                uploader_id=online_user.id,
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
                uploader_id=online_user.id,
                deleted_at=statistics_now,
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
            if course_id is not None:
                await session.execute(delete(Course).where(Course.id == course_id))
            if user_ids:
                await session.execute(delete(User).where(User.id.in_(user_ids)))
            await session.commit()


@pytest.mark.asyncio
async def test_statistics_endpoint_has_basic_fields(client):
    response = await client.get("/statistics")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    for key in {
        "totalUsers",
        "totalDownloads",
        "onlineUsers",
        "totalArchives",
        "totalCourses",
        "activeToday",
    }:
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


@pytest.mark.asyncio
async def test_get_system_statistics_direct_success(session_maker, statistics_records):
    async with session_maker() as session:
        stats = await get_system_statistics(db=session)

        assert stats["success"] is True
        data = stats["data"]

        total_users = await session.scalar(
            select(func.count(User.id)).where(User.deleted_at.is_(None))
        )
        total_courses = await session.scalar(select(func.count(Course.id)))
        total_archives = await session.scalar(
            select(func.count(Archive.id)).where(Archive.deleted_at.is_(None))
        )
        total_downloads = await session.scalar(
            select(func.coalesce(func.sum(Archive.download_count), 0)).where(
                Archive.deleted_at.is_(None)
            )
        )

        assert data["totalUsers"] == total_users
        assert data["totalCourses"] == total_courses
        assert data["totalArchives"] == total_archives
        assert data["totalDownloads"] == total_downloads
        assert data["onlineUsers"] >= 1
        assert data["activeToday"] >= 1


@pytest.mark.asyncio
async def test_get_system_statistics_direct_handles_exception(
    monkeypatch,
    session_maker,
):
    async with session_maker() as session:

        async def boom(*args, **kwargs):
            raise RuntimeError("broken")

        monkeypatch.setattr(session, "execute", boom)
        stats = await get_system_statistics(db=session)
        assert stats["success"] is False
        assert stats["error"] == "Failed to fetch statistics."
        assert stats["data"]["totalUsers"] == 0
