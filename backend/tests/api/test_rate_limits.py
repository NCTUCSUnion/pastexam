import io
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.config import settings
from app.main import app
from app.models.models import (
    Archive,
    ArchiveDiscussionMessage,
    ArchiveType,
    Course,
    CourseCategory,
    UserRoles,
)
from app.utils.auth import get_current_user
from app.utils.rate_limit import KEY_PREFIX
from app.utils.redis import get_redis


@pytest.mark.asyncio
async def test_login_is_locked_after_repeated_failures(
    client: AsyncClient, make_user, monkeypatch
):
    user = await make_user()
    monkeypatch.setattr(settings, "LOGIN_FAILURE_LIMIT", 2)
    key = f"{KEY_PREFIX}login:{user.name.lower()}"

    try:
        for _ in range(2):
            response = await client.post(
                "/auth/login", data={"username": user.name, "password": "wrong"}
            )
            assert response.status_code == 401

        # Even the correct password is rejected until the window resets
        response = await client.post(
            "/auth/login", data={"username": user.name, "password": user.password}
        )
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) > 0
    finally:
        await get_redis().delete(key)


@pytest.mark.asyncio
async def test_successful_login_does_not_count(
    client: AsyncClient, make_user, monkeypatch
):
    user = await make_user()
    monkeypatch.setattr(settings, "LOGIN_FAILURE_LIMIT", 1)

    for _ in range(3):
        response = await client.post(
            "/auth/login", data={"username": user.name, "password": user.password}
        )
        assert response.status_code == 200


async def _upload(client: AsyncClient, subject: str):
    return await client.post(
        "/archives/upload",
        files={"file": ("sample.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={
            "subject": subject,
            "category": CourseCategory.GENERAL.value,
            "professor": "Prof. Limit",
            "archive_type": "final",
            "has_answers": "false",
            "filename": "Limited",
            "academic_year": 2024,
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("is_admin", [False, True])
async def test_upload_limit_applies_to_regular_users_only(
    client: AsyncClient, session_maker, make_user, monkeypatch, is_admin
):
    user = await make_user(is_admin=is_admin)
    subject = f"Rate Limit Course {uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(settings, "UPLOAD_LIMIT_PER_HOUR", 1)

    class FakeStorage:
        def put_object(self, **kwargs):
            return None

    monkeypatch.setattr(
        "app.api.services.archives.get_storage_client", lambda: FakeStorage()
    )

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=is_admin)

    app.dependency_overrides[get_current_user] = fake_get_current_user
    try:
        assert (await _upload(client, subject)).status_code == 200
        second = await _upload(client, subject)
        if is_admin:
            assert second.status_code == 200
        else:
            assert second.status_code == 429
            assert int(second.headers["Retry-After"]) > 0
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        await get_redis().delete(f"{KEY_PREFIX}upload:{user.id}")
        async with session_maker() as session:
            await session.execute(delete(Archive).where(Archive.uploader_id == user.id))
            await session.execute(delete(Course).where(Course.name == subject))
            await session.commit()


@pytest.mark.asyncio
async def test_discussion_messages_are_rate_limited(
    client, session_maker, make_user, monkeypatch
):
    user = await make_user()
    monkeypatch.setattr(settings, "DISCUSSION_MESSAGE_LIMIT_PER_MINUTE", 1)

    async with session_maker() as session:
        course = Course(
            name=f"Discussion Limit {uuid.uuid4().hex[:8]}",
            category=CourseCategory.FRESHMAN,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)
        archive = Archive(
            name="Exam",
            academic_year=2024,
            archive_type=ArchiveType.FINAL,
            professor="Prof",
            has_answers=False,
            object_name="limit.pdf",
            uploader_id=user.id,
            course_id=course.id,
        )
        session.add(archive)
        await session.commit()
        await session.refresh(archive)
        course_id, archive_id = course.id, archive.id

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    monkeypatch.setattr(
        "app.api.services.courses.get_ws_token_payload", fake_ws_payload
    )

    try:
        with TestClient(app) as ws_client, ws_client.websocket_connect(
            f"/courses/{course_id}/archives/{archive_id}/discussion/ws"
        ) as ws:
            ws.receive_json()  # history
            ws.send_text(json.dumps({"type": "send", "content": "first"}))
            assert ws.receive_json()["type"] == "message"

            ws.send_text(json.dumps({"type": "send", "content": "second"}))
            error = ws.receive_json()

        assert error["type"] == "error"
        assert error["code"] == "rate_limited"
    finally:
        async with session_maker() as session:
            await session.execute(
                delete(ArchiveDiscussionMessage).where(
                    ArchiveDiscussionMessage.archive_id == archive_id
                )
            )
            await session.execute(delete(Archive).where(Archive.id == archive_id))
            await session.execute(delete(Course).where(Course.id == course_id))
            await session.commit()
        await get_redis().delete(f"{KEY_PREFIX}discussion:{user.id}")
