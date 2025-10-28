import io
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.main import app
from app.models.models import Archive, Course, CourseCategory, User, UserRoles
from app.utils.auth import get_password_hash, get_current_user


@pytest.mark.asyncio
async def test_upload_archive_creates_course_and_archive(
    client: AsyncClient,
    session_maker,
    monkeypatch,
):
    unique = uuid.uuid4().hex[:8]
    username = f"uploader-{unique}"
    email = f"{username}@example.com"
    plaintext = "VeryStrongPassword123!"

    async with session_maker() as session:
        user = User(
            name=username,
            email=email,
            password_hash=get_password_hash(plaintext),
            is_local=True,
            is_admin=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    async def fake_get_current_user():
        return UserRoles(user_id=user_id, is_admin=False)

    app.dependency_overrides[get_current_user] = fake_get_current_user

    fake_pdf = io.BytesIO(b"%PDF-1.4 test content")
    unique_course = f"Test Course {unique}"

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
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.name == f"Final Exam {unique}")
            )
            await session.execute(
                delete(Course).where(Course.name == unique_course)
            )
            await session.execute(
                delete(User).where(User.id == user_id)
            )
            await session.commit()


@pytest.mark.asyncio
async def test_upload_archive_requires_pdf(client: AsyncClient, session_maker):
    async with session_maker() as session:
        user = User(
            name="non-pdf-tester",
            email=f"non-pdf-{uuid.uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("StrongPass123!"),
            is_local=True,
            is_admin=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    async def fake_get_current_user():
        return UserRoles(user_id=user_id, is_admin=False)

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
        async with session_maker() as session:
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
