import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlmodel import select

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


def _override_user(user_id: int, *, is_admin: bool = False):
    async def _get_current_user():
        return UserRoles(user_id=user_id, is_admin=is_admin)

    return _get_current_user


@pytest.mark.asyncio
async def test_discussion_ws_sends_history_and_ignores_blank(
    client, session_maker, make_user, monkeypatch
):
    user = await make_user(name="ws-user", nickname="Nick")

    async with session_maker() as session:
        course = Course(name="Course", category=CourseCategory.FRESHMAN)
        session.add(course)
        await session.commit()
        await session.refresh(course)

        archive = Archive(
            name="Exam",
            academic_year=2024,
            archive_type=ArchiveType.FINAL,
            professor="Prof",
            has_answers=False,
            object_name="obj.pdf",
            uploader_id=user.id,
            course_id=course.id,
        )
        session.add(archive)
        await session.commit()
        await session.refresh(archive)

        archive_id = archive.id
        course_id = course.id

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    monkeypatch.setattr(
        "app.api.services.courses.get_ws_token_payload", fake_ws_payload
    )

    with TestClient(app) as ws_client:
        with ws_client.websocket_connect(
            f"/courses/{course_id}/archives/{archive_id}/discussion/ws"
        ) as ws:
            first = ws.receive_json()
            assert first["type"] == "history"
            assert first["messages"] == []

            ws.send_text(json.dumps({"type": "send", "content": "   "}))

    async with session_maker() as session:
        result = await session.execute(
            select(ArchiveDiscussionMessage).where(
                ArchiveDiscussionMessage.archive_id == archive_id
            )
        )
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_discussion_ws_accepts_padded_message_within_limit(
    client, session_maker, make_user, monkeypatch
):
    user = await make_user(name="ws-user-2", nickname="Nick2")

    async with session_maker() as session:
        course = Course(name="Course2", category=CourseCategory.FRESHMAN)
        session.add(course)
        await session.commit()
        await session.refresh(course)

        archive = Archive(
            name="Exam2",
            academic_year=2024,
            archive_type=ArchiveType.FINAL,
            professor="Prof",
            has_answers=False,
            object_name="obj2.pdf",
            uploader_id=user.id,
            course_id=course.id,
        )
        session.add(archive)
        await session.commit()
        await session.refresh(archive)

        archive_id = archive.id
        course_id = course.id

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    monkeypatch.setattr(
        "app.api.services.courses.get_ws_token_payload", fake_ws_payload
    )

    content = "a" * 200
    raw = f"  {content}  "

    with TestClient(app) as ws_client:
        with ws_client.websocket_connect(
            f"/courses/{course_id}/archives/{archive_id}/discussion/ws"
        ) as ws:
            ws.receive_json()  # history
            ws.send_text(json.dumps({"type": "send", "content": raw}))
            msg = ws.receive_json()

    assert msg["type"] == "message"
    assert msg["message"]["content"] == content
    assert msg["message"]["user_name"] == "Nick2"

    async with session_maker() as session:
        await session.execute(
            delete(ArchiveDiscussionMessage).where(
                ArchiveDiscussionMessage.archive_id == archive_id
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_discussion_ws_rejects_message_too_long(
    client, session_maker, make_user, monkeypatch
):
    user = await make_user(name="ws-user-3", nickname="Nick3")

    async with session_maker() as session:
        course = Course(name="Course3", category=CourseCategory.FRESHMAN)
        session.add(course)
        await session.commit()
        await session.refresh(course)

        archive = Archive(
            name="Exam3",
            academic_year=2024,
            archive_type=ArchiveType.FINAL,
            professor="Prof",
            has_answers=False,
            object_name="obj3.pdf",
            uploader_id=user.id,
            course_id=course.id,
        )
        session.add(archive)
        await session.commit()
        await session.refresh(archive)

        archive_id = archive.id
        course_id = course.id

    async def fake_ws_payload(websocket):
        return {"uid": user.id, "exp": 4102444800}

    monkeypatch.setattr(
        "app.api.services.courses.get_ws_token_payload", fake_ws_payload
    )

    with TestClient(app) as ws_client:
        with ws_client.websocket_connect(
            f"/courses/{course_id}/archives/{archive_id}/discussion/ws"
        ) as ws:
            ws.receive_json()  # history
            ws.send_text(json.dumps({"type": "send", "content": "a" * 201}))
            err = ws.receive_json()

    assert err["type"] == "error"
    assert err["code"] == "message_too_long"

    async with session_maker() as session:
        await session.execute(
            delete(ArchiveDiscussionMessage).where(
                ArchiveDiscussionMessage.archive_id == archive_id
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_discussion_delete_requires_owner_or_admin(
    client, session_maker, make_user
):
    owner = await make_user(name="owner", nickname="Owner")
    other = await make_user(name="other", nickname="Other")

    async with session_maker() as session:
        course = Course(name="Course4", category=CourseCategory.FRESHMAN)
        session.add(course)
        await session.commit()
        await session.refresh(course)

        archive = Archive(
            name="Exam4",
            academic_year=2024,
            archive_type=ArchiveType.FINAL,
            professor="Prof",
            has_answers=False,
            object_name="obj4.pdf",
            uploader_id=owner.id,
            course_id=course.id,
        )
        session.add(archive)
        await session.commit()
        await session.refresh(archive)

        message = ArchiveDiscussionMessage(
            archive_id=archive.id,
            user_id=owner.id,
            content="hello",
            created_at=datetime.now(timezone.utc),
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)

        course_id = course.id
        archive_id = archive.id
        message_id = message.id

    app.dependency_overrides[get_current_user] = _override_user(
        other.id, is_admin=False
    )
    try:
        response = await client.delete(
            f"/courses/{course_id}/archives/{archive_id}/discussion/{message_id}"
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    app.dependency_overrides[get_current_user] = _override_user(
        owner.id, is_admin=False
    )
    try:
        response = await client.delete(
            f"/courses/{course_id}/archives/{archive_id}/discussion/{message_id}"
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    async with session_maker() as session:
        await session.execute(
            delete(ArchiveDiscussionMessage).where(
                ArchiveDiscussionMessage.archive_id == archive_id
            )
        )
        await session.commit()
