import io
import uuid

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import delete, select, func
from starlette.datastructures import UploadFile

from app.api.services.archives import upload_archive
from app.main import app
from app.models.models import Archive, Course, CourseCategory, User, UserRoles
from app.utils.auth import get_current_user


@pytest.mark.asyncio
async def test_upload_archive_creates_course_and_archive(
    client: AsyncClient,
    session_maker,
    make_user,
    monkeypatch,
):
    unique = uuid.uuid4().hex[:8]
    user = await make_user()
    user_id = user.id

    async def fake_get_current_user():
        return UserRoles(user_id=user_id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    fake_pdf = io.BytesIO(b"%PDF-1.4 test content")
    unique_course = f"Test Course {unique}"

    class FakeMinio:
        def put_object(self, **kwargs):
            return None

    monkeypatch.setattr(
        "app.api.services.archives.get_minio_client",
        lambda: FakeMinio(),
    )

    try:
        response = await client.post(
            "/archives/upload",
            files={"file": ("sample.pdf", fake_pdf, "application/pdf")},
            data={
                "subject": unique_course,
                "category": CourseCategory.GENERAL.value,
                "professor": "Prof. Test",
                "archive_type": "final",
                "has_answers": "true",
                "filename": f"Final Exam {unique}",
                "academic_year": 2024,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        archive_data = body["archive"]
        assert archive_data["name"] == f"Final Exam {unique}"
        assert archive_data["professor"] == "Prof. Test"

        async with session_maker() as session:
            result = await session.execute(
                select(Course).where(Course.name == unique_course)
            )
            course = result.scalar_one_or_none()
            assert course is not None

            result = await session.execute(
                select(Archive).where(Archive.id == archive_data["id"])
            )
            archive = result.scalar_one_or_none()
            assert archive is not None
            assert archive.course_id == course.id
            assert archive.uploader_id == user_id
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_archive_returns_404_when_user_missing(
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
        response = await client.post(
            "/archives/upload",
            files={
                "file": (
                    "sample.pdf",
                    io.BytesIO(b"%PDF-1.4"),
                    "application/pdf",
                )
            },
            data={
                "subject": "Missing User Course",
                "category": CourseCategory.GENERAL.value,
                "professor": "Prof. Missing",
                "archive_type": "midterm",
                "has_answers": "false",
                "filename": "Should Fail",
                "academic_year": 2024,
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_archive_reuses_existing_course(
    client: AsyncClient,
    session_maker,
    make_user,
    monkeypatch,
):
    user = await make_user()
    subject = "Existing Course"

    async with session_maker() as session:
        course = Course(name=subject, category=CourseCategory.GENERAL)
        session.add(course)
        await session.commit()
        await session.refresh(course)

    class FakeMinio:
        def put_object(self, **kwargs):
            return None

    monkeypatch.setattr(
        "app.api.services.archives.get_minio_client",
        lambda: FakeMinio(),
    )

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    try:
        response = await client.post(
            "/archives/upload",
            files={
                "file": (
                    "sample.pdf",
                    io.BytesIO(b"%PDF-1.4 reuse"),
                    "application/pdf",
                )
            },
            data={
                "subject": subject,
                "category": CourseCategory.GENERAL.value,
                "professor": "Prof. Existing",
                "archive_type": "quiz",
                "has_answers": "false",
                "filename": "Reuse Archive",
                "academic_year": 2023,
            },
        )
        assert response.status_code == 200

        async with session_maker() as session:
            count = await session.execute(
                select(func.count()).where(Course.name == subject)
            )
            assert count.scalar() == 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.uploader_id == user.id)
            )
            await session.execute(delete(Course).where(Course.name == subject))
            await session.commit()


@pytest.mark.asyncio
async def test_upload_archive_rejects_large_file(
    client: AsyncClient,
    make_user,
    session_maker,
    monkeypatch,
):
    user = await make_user()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    class FakeMinio:
        def put_object(self, **kwargs):
            raise AssertionError("should not upload oversized file")

    monkeypatch.setattr(
        "app.api.services.archives.get_minio_client",
        lambda: FakeMinio(),
    )

    try:
        big_content = b"x" * (10 * 1024 * 1024 + 1)
        response = await client.post(
            "/archives/upload",
            files={
                "file": (
                    "huge.pdf",
                    io.BytesIO(big_content),
                    "application/pdf",
                )
            },
            data={
                "subject": "Oversized Course",
                "category": CourseCategory.GENERAL.value,
                "professor": "Prof. Big",
                "archive_type": "midterm",
                "has_answers": "true",
                "filename": "Too Large",
                "academic_year": 2024,
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "File size exceeds 10MB limit"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Course).where(Course.name == "Oversized Course")
            )
            await session.commit()


@pytest.mark.asyncio
async def test_upload_archive_handles_storage_failure(
    client: AsyncClient,
    make_user,
    session_maker,
    monkeypatch,
):
    user = await make_user()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    class FailingMinio:
        def put_object(self, **kwargs):
            raise RuntimeError("minio unavailable")

    monkeypatch.setattr(
        "app.api.services.archives.get_minio_client",
        lambda: FailingMinio(),
    )

    try:
        response = await client.post(
            "/archives/upload",
            files={
                "file": (
                    "sample.pdf",
                    io.BytesIO(b"%PDF-1.4 fake"),
                    "application/pdf",
                )
            },
            data={
                "subject": "Fail Course",
                "category": CourseCategory.GENERAL.value,
                "professor": "Prof. Fail",
                "archive_type": "final",
                "has_answers": "false",
                "filename": "Failure",
                "academic_year": 2024,
            },
        )
        assert response.status_code == 500
        assert "Failed to upload file" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(Course).where(Course.name == "Fail Course")
            )
            await session.commit()


@pytest.mark.asyncio
async def test_upload_archive_function_covers_creation_and_reuse(
    session_maker,
    make_user,
    monkeypatch,
):
    user = await make_user()
    uploads = []
    first_id = None
    second_id = None
    course_id = None

    class RecordingMinio:
        def __init__(self):
            self.calls = []

        def put_object(self, **kwargs):
            self.calls.append(kwargs)

    monkeypatch.setattr(
        "app.api.services.archives.get_minio_client",
        lambda: RecordingMinio(),
    )

    async with session_maker() as session:
        uploader = UserRoles(user_id=user.id, is_admin=False)

        async def _call(subject, filename):
            upload = UploadFile(
                filename=filename,
                file=io.BytesIO(b"%PDF-1.4 direct test"),
            )
            uploads.append(upload)
            return await upload_archive(
                file=upload,
                subject=subject,
                category=CourseCategory.GENERAL,
                professor="Prof. Direct",
                archive_type="final",
                has_answers=True,
                filename=filename,
                academic_year=2024,
                current_user=uploader,
                db=session,
            )

        first = await _call("Direct Subject", "Direct Archive.pdf")
        second = await _call("Direct Subject", "Second Archive.pdf")

        assert first["success"] is True
        assert second["success"] is True
        assert first["archive"]["name"] == "Direct Archive.pdf"
        assert second["archive"]["name"] == "Second Archive.pdf"

        # Ensure both archives share the same course
        first_id = first["archive"]["id"]
        second_id = second["archive"]["id"]
        first_archive = await session.get(Archive, first_id)
        second_archive = await session.get(Archive, second_id)
        assert first_archive.course_id == second_archive.course_id
        course_id = first_archive.course_id

    if first_id and second_id and course_id:
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(
                    Archive.id.in_([first_id, second_id])
                )
            )
            await session.execute(
                delete(Course).where(Course.id == course_id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_upload_archive_requires_pdf(
    client: AsyncClient,
    make_user,
):
    user = await make_user()

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    try:
        response = await client.post(
            "/archives/upload",
            files={"file": ("sample.txt", io.BytesIO(b"text"), "text/plain")},
            data={
                "subject": "Non PDF Course",
                "category": CourseCategory.GENERAL.value,
                "professor": "Prof. Fake",
                "archive_type": "midterm",
                "has_answers": "false",
                "filename": "Not PDF",
                "academic_year": 2024,
            },
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Only PDF files are allowed"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_archive_function_user_missing(
    session_maker,
    make_user,
):
    user = await make_user()
    async with session_maker() as session:
        db_user = await session.get(User, user.id)
        await session.delete(db_user)
        await session.commit()

    upload = UploadFile(
        filename="missing.pdf",
        file=io.BytesIO(b"%PDF missing user"),
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await upload_archive(
                file=upload,
                subject="Missing Subject",
                category=CourseCategory.GENERAL,
                professor="Prof. Missing",
                archive_type="midterm",
                has_answers=False,
                filename="Missing Archive",
                academic_year=2024,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_upload_archive_function_rejects_non_pdf(
    session_maker,
    make_user,
):
    user = await make_user()
    upload = UploadFile(filename="invalid.txt", file=io.BytesIO(b"text"))

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await upload_archive(
                file=upload,
                subject="Bad File",
                category=CourseCategory.GENERAL,
                professor="Prof. Text",
                archive_type="midterm",
                has_answers=False,
                filename="Bad File",
                academic_year=2024,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_upload_archive_function_handles_storage_error(
    session_maker,
    make_user,
    monkeypatch,
):
    user = await make_user()

    class FailingMinio:
        def put_object(self, **kwargs):
            raise RuntimeError("storage down")

    monkeypatch.setattr(
        "app.api.services.archives.get_minio_client",
        lambda: FailingMinio(),
    )

    upload = UploadFile(filename="fail.pdf", file=io.BytesIO(b"%PDF fail"))

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await upload_archive(
                file=upload,
                subject="Failure",
                category=CourseCategory.GENERAL,
                professor="Prof. Fail",
                archive_type="final",
                has_answers=False,
                filename="Failure",
                academic_year=2024,
                current_user=UserRoles(user_id=user.id, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 500
