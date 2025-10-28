from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.services.statistics import get_system_statistics
from app.models.models import (
    Archive,
    ArchiveType,
    Course,
    CourseCategory,
    User,
)


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

    monkeypatch.setattr(AsyncSession, "execute", failing_execute, raising=False)

    response = await client.get("/statistics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["totalUsers"] == 0


@pytest.mark.asyncio
async def test_get_system_statistics_direct_success(session_maker):
    now = datetime.now(timezone.utc)
    earlier = now - timedelta(days=1)
    unique = uuid.uuid4().hex[:6]

    async with session_maker() as session:
        baseline = await get_system_statistics(db=session)
        base_data = baseline["data"]

        online_user = User(
            name=f"online-user-{unique}",
            email=f"online-{unique}@example.com",
            is_admin=False,
            is_local=True,
            last_login=now,
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
            deleted_at=now,
        )
        session.add_all([active_archive, deleted_archive])
        await session.commit()
        await session.refresh(active_archive)
        await session.refresh(deleted_archive)

        stats = await get_system_statistics(db=session)

        assert stats["success"] is True
        data = stats["data"]
        assert data["totalUsers"] == base_data["totalUsers"] + 2
        assert data["totalCourses"] == base_data["totalCourses"] + 1
        assert data["totalArchives"] == base_data["totalArchives"] + 1
        assert data["totalDownloads"] == base_data["totalDownloads"] + 7
        assert data["onlineUsers"] == base_data["onlineUsers"] + 1
        assert data["activeToday"] == base_data["activeToday"] + 1

        await session.delete(active_archive)
        await session.delete(deleted_archive)
        await session.delete(course)
        await session.delete(online_user)
        await session.delete(offline_user)
        await session.commit()


@pytest.mark.asyncio
async def test_get_system_statistics_direct_handles_exception(monkeypatch, session_maker):
    async with session_maker() as session:
        async def boom(*args, **kwargs):
            raise RuntimeError("broken")

        monkeypatch.setattr(session, "execute", boom)
        stats = await get_system_statistics(db=session)
        assert stats["success"] is False
        assert stats["data"]["totalUsers"] == 0
