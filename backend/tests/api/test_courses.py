import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.main import app
from app.models.models import Archive, ArchiveType, Course, CourseCategory, UserRoles
from app.utils.auth import get_current_user


async def _create_course(session_maker, *, name=None, category=CourseCategory.GENERAL):
    async with session_maker() as session:
        course = Course(
            name=name or f"Course {uuid.uuid4().hex[:6]}",
            category=category,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)
        return course


async def _create_archive(
    session_maker,
    *,
    course_id: int,
    uploader_id: int,
    name=None,
    deleted: bool = False,
):
    async with session_maker() as session:
        archive = Archive(
            name=name or f"Archive {uuid.uuid4().hex[:6]}",
            academic_year=2024,
            archive_type=ArchiveType.FINAL,
            professor="Prof. Test",
            has_answers=False,
            object_name=f"archives/{course_id}/{uuid.uuid4().hex}.pdf",
            course_id=course_id,
            uploader_id=uploader_id,
        )
        if deleted:
            archive.deleted_at = datetime.now(timezone.utc)
        session.add(archive)
        await session.commit()
        await session.refresh(archive)
        return archive


def _override_user(user):
    async def _get_current_user():
        return UserRoles(user_id=user.id, is_admin=user.is_admin)

    return _get_current_user


@pytest.mark.asyncio
async def test_get_categorized_courses_returns_courses(
    client: AsyncClient,
    session_maker,
    make_user,
):
    user = await make_user()
    course = await _create_course(session_maker, category=CourseCategory.GENERAL)

    app.dependency_overrides[get_current_user] = _override_user(user)
    try:
        response = await client.get("/courses")
        assert response.status_code == 200
        body = response.json()
        general_courses = body["general"]
        assert any(item["id"] == course.id for item in general_courses)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()


@pytest.mark.asyncio
async def test_get_course_archives_returns_active_archives(
    client: AsyncClient,
    session_maker,
    make_user,
):
    user = await make_user()
    course = await _create_course(session_maker)
    active_archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=user.id
    )
    await _create_archive(
        session_maker,
        course_id=course.id,
        uploader_id=user.id,
        deleted=True,
    )

    app.dependency_overrides[get_current_user] = _override_user(user)
    try:
        response = await client.get(f"/courses/{course.id}/archives")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == active_archive.id
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Archive).where(Archive.course_id == course.id))
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()


@pytest.mark.asyncio
async def test_get_archive_preview_url_returns_presigned_link(
    client: AsyncClient,
    session_maker,
    make_user,
    monkeypatch,
):
    user = await make_user()
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=user.id
    )

    preview_url = "https://preview.example.com/resource"

    def fake_presigned(obj_name, *, expires):
        assert obj_name == archive.object_name
        assert expires.total_seconds() == 1800
        return preview_url

    monkeypatch.setattr(
        "app.api.services.courses.presigned_get_url", fake_presigned
    )
    app.dependency_overrides[get_current_user] = _override_user(user)
    try:
        response = await client.get(
            f"/courses/{course.id}/archives/{archive.id}/preview"
        )
        assert response.status_code == 200
        assert response.json() == {"url": preview_url}
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Archive).where(Archive.id == archive.id))
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()


@pytest.mark.asyncio
async def test_get_archive_download_url_increments_count(
    client: AsyncClient,
    session_maker,
    make_user,
    monkeypatch,
):
    user = await make_user()
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=user.id
    )

    download_url = "https://download.example.com/file"

    def fake_presigned(obj_name, *, expires):
        assert obj_name == archive.object_name
        assert expires.total_seconds() == 3600
        return download_url

    monkeypatch.setattr(
        "app.api.services.courses.presigned_get_url", fake_presigned
    )
    app.dependency_overrides[get_current_user] = _override_user(user)
    try:
        response = await client.get(
            f"/courses/{course.id}/archives/{archive.id}/download"
        )
        assert response.status_code == 200
        assert response.json() == {"url": download_url}

        async with session_maker() as session:
            refreshed = await session.get(Archive, archive.id)
            assert refreshed.download_count == 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Archive).where(Archive.id == archive.id))
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()


@pytest.mark.asyncio
async def test_update_archive_requires_admin(
    client: AsyncClient,
    session_maker,
    make_user,
):
    user = await make_user()
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=user.id
    )

    app.dependency_overrides[get_current_user] = _override_user(user)
    try:
        response = await client.patch(
            f"/courses/{course.id}/archives/{archive.id}",
            data={"name": "New Name"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Archive).where(Archive.id == archive.id))
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()


@pytest.mark.asyncio
async def test_admin_update_archive_changes_fields(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=admin.id
    )

    app.dependency_overrides[get_current_user] = _override_user(admin)
    try:
        response = await client.patch(
            f"/courses/{course.id}/archives/{archive.id}",
            data={
                "name": "Updated Archive",
                "professor": "Prof. New",
                "archive_type": ArchiveType.MIDTERM.value,
                "has_answers": "true",
                "academic_year": 2025,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Updated Archive"
        assert body["professor"] == "Prof. New"
        assert body["archive_type"] == ArchiveType.MIDTERM.value
        assert body["has_answers"] is True
        assert body["academic_year"] == 2025
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Archive).where(Archive.id == archive.id))
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()


@pytest.mark.asyncio
async def test_admin_course_crud_flow(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    app.dependency_overrides[get_current_user] = _override_user(admin)

    course_name = f"Course {uuid.uuid4().hex[:6]}"
    course_id = None

    try:
        response = await client.post(
            "/courses/admin/courses",
            json={
                "name": course_name,
                "category": CourseCategory.GENERAL.value,
            },
        )
        assert response.status_code == 200
        created = response.json()
        course_id = created["id"]

        response = await client.put(
            f"/courses/admin/courses/{course_id}",
            json={"name": f"{course_name} Updated"},
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == f"{course_name} Updated"

        response = await client.get("/courses/admin/courses")
        assert response.status_code == 200
        all_courses = response.json()
        assert any(course["id"] == course_id for course in all_courses)

        response = await client.delete(f"/courses/admin/courses/{course_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        async with session_maker() as session:
            soft_deleted = await session.get(Course, course_id)
            assert soft_deleted.deleted_at is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        if course_id is not None:
            async with session_maker() as session:
                await session.execute(
                    delete(Archive).where(Archive.course_id == course_id)
                )
                await session.execute(delete(Course).where(Course.id == course_id))
                await session.commit()


@pytest.mark.asyncio
async def test_admin_course_endpoints_require_admin(
    client: AsyncClient,
    session_maker,
    make_user,
):
    user = await make_user()
    course = await _create_course(session_maker)
    app.dependency_overrides[get_current_user] = _override_user(user)

    try:
        response = await client.post(
            "/courses/admin/courses",
            json={
                "name": f"Forbidden {uuid.uuid4().hex[:4]}",
                "category": CourseCategory.GENERAL.value,
            },
        )
        assert response.status_code == 403

        response = await client.put(
            f"/courses/admin/courses/{course.id}",
            json={"name": "Should Not Update"},
        )
        assert response.status_code == 403

        response = await client.delete(f"/courses/admin/courses/{course.id}")
        assert response.status_code == 403

        response = await client.get("/courses/admin/courses")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()
