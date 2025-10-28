import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import delete

from app.api.services.courses import (
    create_course,
    delete_archive,
    delete_course,
    get_archive_download_url,
    get_archive_preview_url,
    get_categorized_courses,
    get_course_archives,
    list_all_courses,
    update_archive,
    update_archive_course,
    update_course,
)
from app.main import app
from app.models.models import (
    Archive,
    ArchiveType,
    ArchiveUpdateCourse,
    Course,
    CourseCategory,
    CourseCreate,
    CourseUpdate,
    UserRoles,
)
from app.utils.auth import get_current_user


async def _create_course(
    session_maker,
    *,
    name=None,
    category=CourseCategory.GENERAL,
):
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
    course = await _create_course(
        session_maker,
        category=CourseCategory.GENERAL,
    )

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
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
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
            await session.execute(
                delete(Archive).where(Archive.course_id == course.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
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
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
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
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
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
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
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
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
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
                await session.execute(
                    delete(Course).where(Course.id == course_id)
                )
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
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_transfers_to_existing_course(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course_a = await _create_course(session_maker, name="Course A")
    course_b = await _create_course(session_maker, name="Course B")
    archive = await _create_archive(
        session_maker,
        course_id=course_a.id,
        uploader_id=admin.id,
    )

    app.dependency_overrides[get_current_user] = _override_user(admin)

    try:
        response = await client.patch(
            f"/courses/{course_a.id}/archives/{archive.id}/course",
            json={"course_id": course_b.id},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["new_course_id"] == course_b.id

        async with session_maker() as session:
            refreshed = await session.get(Archive, archive.id)
            assert refreshed.course_id == course_b.id
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(
                    Course.id.in_([course_a.id, course_b.id])
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_creates_new_course_when_missing(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    original = await _create_course(session_maker, name="Original Course")
    archive = await _create_archive(
        session_maker,
        course_id=original.id,
        uploader_id=admin.id,
    )

    app.dependency_overrides[get_current_user] = _override_user(admin)

    try:
        response = await client.patch(
            f"/courses/{original.id}/archives/{archive.id}/course",
            json={
                "course_name": "New Course",
                "course_category": CourseCategory.GENERAL.value,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["message"].startswith("Archive moved to course")

        async with session_maker() as session:
            refreshed = await session.get(Archive, archive.id)
            assert refreshed.course_id != original.id
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(
                    Course.name.in_(["Original Course", "New Course"])
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_rejects_same_course(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker, name="SameCourse")
    archive = await _create_archive(
        session_maker,
        course_id=course.id,
        uploader_id=admin.id,
    )

    app.dependency_overrides[get_current_user] = _override_user(admin)

    try:
        response = await client.patch(
            f"/courses/{course.id}/archives/{archive.id}/course",
            json={"course_id": course.id},
        )
        assert response.status_code == 400
        assert "same course" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_delete_archive_admin_success(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker,
        course_id=course.id,
        uploader_id=admin.id,
    )

    app.dependency_overrides[get_current_user] = _override_user(admin)

    try:
        response = await client.delete(
            f"/courses/{course.id}/archives/{archive.id}"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Archive deleted successfully"

        async with session_maker() as session:
            refreshed = await session.get(Archive, archive.id)
            assert refreshed.deleted_at is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_get_categorized_courses_direct(session_maker, make_user):
    user = await make_user()
    course_general = await _create_course(
        session_maker,
        category=CourseCategory.GENERAL,
    )
    course_graduate = await _create_course(
        session_maker,
        category=CourseCategory.GRADUATE,
    )

    try:
        async with session_maker() as session:
            result = await get_categorized_courses(
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        payload = result.model_dump()
        assert any(
            item["id"] == course_general.id
            for item in payload["general"]
        )
        assert any(
            item["id"] == course_graduate.id
            for item in payload["graduate"]
        )
    finally:
        async with session_maker() as session:
            await session.execute(
                delete(Course).where(
                    Course.id.in_([course_general.id, course_graduate.id])
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_get_course_archives_direct_errors_when_course_missing(
    session_maker,
    make_user,
):
    user = await make_user()
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await get_course_archives(
                course_id=999999,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_archive_preview_and_download_direct(
    session_maker,
    make_user,
    monkeypatch,
):
    user = await make_user()
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=user.id
    )

    preview_url = "https://example.com/preview"
    download_url = "https://example.com/download"

    def fake_presigned(object_name: str, *, expires):
        if expires.total_seconds() == 1800:
            return preview_url
        return download_url

    monkeypatch.setattr(
        "app.api.services.courses.presigned_get_url",
        fake_presigned,
    )

    try:
        async with session_maker() as session:
            preview = await get_archive_preview_url(
                course.id,
                archive.id,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
            download = await get_archive_download_url(
                course.id,
                archive.id,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
            assert preview == {"url": preview_url}
            assert download == {"url": download_url}

        async with session_maker() as session:
            refreshed = await session.get(Archive, archive.id)
            assert refreshed.download_count == 1
    finally:
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_get_archive_preview_url_not_found(
    client: AsyncClient,
    make_user,
):
    user = await make_user()

    app.dependency_overrides[get_current_user] = _override_user(user)
    try:
        response = await client.get("/courses/999/archives/1/preview")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_archive_download_url_not_found(
    client: AsyncClient,
    make_user,
):
    user = await make_user()

    app.dependency_overrides[get_current_user] = _override_user(user)
    try:
        response = await client.get("/courses/123/archives/456/download")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_archive_direct_sets_fields(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=admin.id
    )

    try:
        async with session_maker() as session:
            updated = await update_archive(
                course_id=course.id,
                archive_id=archive.id,
                name="Flashcards",
                professor="Prof. Direct",
                archive_type=ArchiveType.QUIZ,
                has_answers=True,
                academic_year=2026,
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
            assert updated.name == "Flashcards"
            assert updated.professor == "Prof. Direct"
            assert updated.archive_type == ArchiveType.QUIZ
            assert updated.has_answers is True
            assert updated.academic_year == 2026
    finally:
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_update_archive_direct_404_when_missing(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_archive(
                course_id=course.id,
                archive_id=9999,
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 404

    async with session_maker() as session:
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_requires_admin(session_maker, make_user):
    user = await make_user()
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=user.id
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_archive_course(
                course_id=course.id,
                archive_id=archive.id,
                course_update=ArchiveUpdateCourse(course_id=course.id + 1),
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 403

    async with session_maker() as session:
        await session.execute(delete(Archive).where(Archive.id == archive.id))
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_missing_payload_raises(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=admin.id
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_archive_course(
                course_id=course.id,
                archive_id=archive.id,
                course_update=ArchiveUpdateCourse(),
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

    async with session_maker() as session:
        await session.execute(delete(Archive).where(Archive.id == archive.id))
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_target_course_missing(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=admin.id
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_archive_course(
                course_id=course.id,
                archive_id=archive.id,
                course_update=ArchiveUpdateCourse(course_id=999999),
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 404

    async with session_maker() as session:
        await session.execute(delete(Archive).where(Archive.id == archive.id))
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_same_course_by_name_rejected(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker, name="OverlapCourse")
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=admin.id
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_archive_course(
                course_id=course.id,
                archive_id=archive.id,
                course_update=ArchiveUpdateCourse(
                    course_name=course.name,
                    course_category=course.category,
                ),
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

    async with session_maker() as session:
        await session.execute(delete(Archive).where(Archive.id == archive.id))
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_update_archive_course_archive_missing(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_archive_course(
                course_id=course.id,
                archive_id=123456,
                course_update=ArchiveUpdateCourse(course_id=course.id),
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 404

    async with session_maker() as session:
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_delete_archive_direct_forbidden_for_non_owner(
    session_maker,
    make_user,
):
    owner = await make_user()
    other = await make_user()
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker, course_id=course.id, uploader_id=owner.id
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await delete_archive(
                course_id=course.id,
                archive_id=archive.id,
                current_user=UserRoles(user_id=other.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 403

    async with session_maker() as session:
        await session.execute(delete(Archive).where(Archive.id == archive.id))
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_create_course_duplicate_rejected(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(
        session_maker,
        name="Duplicate Course",
        category=CourseCategory.GENERAL,
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await create_course(
                course_data=CourseCreate(
                    name="Duplicate Course",
                    category=CourseCategory.GENERAL,
                ),
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

    async with session_maker() as session:
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_update_course_duplicate_name_rejected(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    original = await _create_course(session_maker, name="Original-Name")
    other = await _create_course(session_maker, name="Existing-Name")

    try:
        async with session_maker() as session:
            with pytest.raises(HTTPException) as exc:
                await update_course(
                    course_id=original.id,
                    course_data=CourseUpdate(name="Existing-Name"),
                    current_user=UserRoles(user_id=admin.id, is_admin=True),
                    db=session,
                )
            assert exc.value.status_code == 400
    finally:
        async with session_maker() as session:
            await session.execute(
                delete(Course).where(Course.id.in_([original.id, other.id]))
            )
            await session.commit()


@pytest.mark.asyncio
async def test_update_course_not_found_direct(session_maker, make_user):
    admin = await make_user(is_admin=True)

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_course(
                course_id=424242,
                course_data=CourseUpdate(name="Missing"),
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_course_not_found_direct(session_maker, make_user):
    admin = await make_user(is_admin=True)

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await delete_course(
                course_id=123123,
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_course_soft_deletes_archives(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker)
    archive = await _create_archive(
        session_maker,
        course_id=course.id,
        uploader_id=admin.id,
    )

    app.dependency_overrides[get_current_user] = _override_user(admin)
    try:
        response = await client.delete(
            f"/courses/admin/courses/{course.id}"
        )
        assert response.status_code == 200
        body = response.json()
        assert "1 associated archives" in body["message"]

        async with session_maker() as session:
            refreshed_course = await session.get(Course, course.id)
            refreshed_archive = await session.get(Archive, archive.id)
            assert refreshed_course.deleted_at is not None
            assert refreshed_archive.deleted_at is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.id == archive.id)
            )
            await session.execute(
                delete(Course).where(Course.id == course.id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_list_all_courses_direct_returns_courses(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker, name="Visible Course")

    try:
        async with session_maker() as session:
            courses = await list_all_courses(
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
            assert any(item.id == course.id for item in courses)
    finally:
        async with session_maker() as session:
            await session.execute(delete(Course).where(Course.id == course.id))
            await session.commit()


@pytest.mark.asyncio
async def test_get_course_archives_not_found_direct(
    session_maker,
    make_user,
):
    user = await make_user()
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await get_course_archives(
                course_id=999999,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_archive_preview_url_not_found_direct(
    session_maker,
    make_user,
):
    user = await make_user()
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await get_archive_preview_url(
                course_id=1,
                archive_id=2,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_archive_download_url_not_found_direct(
    session_maker,
    make_user,
):
    user = await make_user()
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await get_archive_download_url(
                course_id=1,
                archive_id=2,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_archive_course_creates_new_course_direct(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker, name="Direct Course")
    archive = await _create_archive(
        session_maker,
        course_id=course.id,
        uploader_id=admin.id,
    )

    async with session_maker() as session:
        response = await update_archive_course(
            course_id=course.id,
            archive_id=archive.id,
            course_update=ArchiveUpdateCourse(
                course_name="Brand New Course",
                course_category=CourseCategory.GRADUATE,
            ),
            current_user=UserRoles(user_id=admin.id, is_admin=True),
            db=session,
        )
        new_course_id = response["new_course_id"]
        new_course = await session.get(Course, new_course_id)
        assert new_course.name == "Brand New Course"

        await session.execute(delete(Archive).where(Archive.id == archive.id))
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.execute(delete(Course).where(Course.id == new_course_id))
        await session.commit()


@pytest.mark.asyncio
async def test_create_course_duplicate_direct(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(
        session_maker,
        name="Duplicate Direct",
        category=CourseCategory.GENERAL,
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await create_course(
                course_data=CourseCreate(
                    name="Duplicate Direct",
                    category=CourseCategory.GENERAL,
                ),
                current_user=UserRoles(user_id=admin.id, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

    async with session_maker() as session:
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()


@pytest.mark.asyncio
async def test_delete_course_soft_deletes_direct(
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    course = await _create_course(session_maker, name="Delete Direct")
    archive = await _create_archive(
        session_maker,
        course_id=course.id,
        uploader_id=admin.id,
    )

    async with session_maker() as session:
        result = await delete_course(
            course_id=course.id,
            current_user=UserRoles(user_id=admin.id, is_admin=True),
            db=session,
        )
        assert "associated archives" in result["message"]

        refreshed_course = await session.get(Course, course.id)
        refreshed_archive = await session.get(Archive, archive.id)
        assert refreshed_course.deleted_at is not None
        assert refreshed_archive.deleted_at is not None

        await session.execute(delete(Archive).where(Archive.id == archive.id))
        await session.execute(delete(Course).where(Course.id == course.id))
        await session.commit()
