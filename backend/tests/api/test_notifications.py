import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.main import app
from app.models.models import (
    Notification,
    NotificationCreate,
    NotificationSeverity,
    NotificationUpdate,
    UserRoles,
)
from app.api.services.notifications import (
    create_notification,
    delete_notification,
    get_active_notifications,
    list_admin_notifications,
    list_public_notifications,
    update_notification,
)
from app.utils.auth import get_current_user


async def _create_notification(session_maker, **overrides):
    now = datetime.now(timezone.utc)
    data = NotificationCreate(
        title=f"Test Notification {uuid.uuid4().hex[:6]}",
        body="Hello world",
        severity=NotificationSeverity.INFO,
        is_active=True,
        starts_at=overrides.pop("starts_at", now - timedelta(minutes=5)),
        ends_at=overrides.pop("ends_at", now + timedelta(minutes=5)),
    )
    for field, value in overrides.items():
        setattr(data, field, value)

    async with session_maker() as session:
        notification = Notification(
            **data.model_dump(),
            created_at=now,
            updated_at=now,
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification


def _override_user(user):
    async def _get_current_user():
        return UserRoles(user_id=user["id"], is_admin=user["is_admin"])

    return _get_current_user


@pytest.mark.asyncio
async def test_public_notification_endpoints_return_active_only(
    client: AsyncClient,
    session_maker,
):
    active = await _create_notification(session_maker)
    await _create_notification(
        session_maker,
        is_active=False,
        starts_at=datetime.now(timezone.utc) - timedelta(days=2),
        ends_at=datetime.now(timezone.utc) - timedelta(days=1),
    )

    for path in ("/notifications", "/notifications/active"):
        response = await client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == active.id

    async with session_maker() as session:
        await session.execute(delete(Notification))
        await session.commit()


@pytest.mark.asyncio
async def test_admin_can_crud_notifications(
    client: AsyncClient,
    session_maker,
    make_user,
):
    admin = await make_user(is_admin=True)
    app.dependency_overrides[get_current_user] = _override_user(
        {"id": admin.id, "is_admin": True}
    )

    created_id = None

    try:
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        payload = {
            "title": "Site maintenance",
            "body": "Expected downtime",
            "severity": NotificationSeverity.DANGER.value,
            "is_active": True,
            "starts_at": start_time.isoformat(),
            "ends_at": end_time.isoformat(),
        }
        response = await client.post(
            "/notifications/admin/notifications",
            json=payload,
        )
        assert response.status_code == 201
        created = response.json()
        created_id = created["id"]
        assert created["title"] == payload["title"]

        update_payload = {"title": "Updated title", "is_active": False}
        response = await client.put(
            f"/notifications/admin/notifications/{created_id}",
            json=update_payload,
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["title"] == "Updated title"
        assert updated["is_active"] is False

        response = await client.get("/notifications/admin/notifications")
        assert response.status_code == 200
        admin_list = response.json()
        assert any(item["id"] == created_id for item in admin_list)

        response = await client.delete(
            f"/notifications/admin/notifications/{created_id}"
        )
        assert response.status_code == 204
        created_id = None
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Notification))
            await session.commit()


@pytest.mark.asyncio
async def test_update_notification_not_found(client: AsyncClient, make_user):
    admin = await make_user(is_admin=True)
    app.dependency_overrides[get_current_user] = _override_user(
        {"id": admin.id, "is_admin": True}
    )

    try:
        response = await client.put(
            "/notifications/admin/notifications/99999",
            json={"title": "Missing"},
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_notification_not_found(client: AsyncClient, make_user):
    admin = await make_user(is_admin=True)
    app.dependency_overrides[get_current_user] = _override_user(
        {"id": admin.id, "is_admin": True}
    )

    try:
        response = await client.delete(
            "/notifications/admin/notifications/424242"
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_admin_notifications_require_admin(
    client: AsyncClient,
    session_maker,
    make_user,
):
    user = await make_user()
    app.dependency_overrides[get_current_user] = _override_user(
        {"id": user.id, "is_admin": False}
    )

    try:
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        payload = {
            "title": "Forbidden",
            "body": "Nope",
            "severity": NotificationSeverity.INFO.value,
            "is_active": True,
            "starts_at": start_time.isoformat(),
            "ends_at": end_time.isoformat(),
        }

        response = await client.get("/notifications/admin/notifications")
        assert response.status_code == 403

        response = await client.post(
            "/notifications/admin/notifications", json=payload
        )
        assert response.status_code == 403

        response = await client.put(
            "/notifications/admin/notifications/1", json={"title": "Nope"}
        )
        assert response.status_code == 403

        response = await client.delete("/notifications/admin/notifications/1")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(delete(Notification))
            await session.commit()


@pytest.mark.asyncio
async def test_list_public_notifications_direct(session_maker):
    async with session_maker() as session:
        await session.execute(delete(Notification))
        await session.commit()

        visible = await _create_notification(session_maker)
        await _create_notification(
            session_maker,
            starts_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

    async with session_maker() as session:
        results = await list_public_notifications(db=session)
        assert [item.id for item in results] == [visible.id]

    async with session_maker() as session:
        await session.execute(delete(Notification))
        await session.commit()


@pytest.mark.asyncio
async def test_get_active_notifications_direct(session_maker):
    async with session_maker() as session:
        await session.execute(delete(Notification))
        await session.commit()

        active = await _create_notification(session_maker)
        await _create_notification(
            session_maker,
            is_active=False,
            ends_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

    async with session_maker() as session:
        results = await get_active_notifications(db=session)
        assert [item.id for item in results] == [active.id]

    async with session_maker() as session:
        await session.execute(delete(Notification))
        await session.commit()


@pytest.mark.asyncio
async def test_create_update_delete_notifications_direct(session_maker):
    admin = UserRoles(user_id=1, is_admin=True)
    async with session_maker() as session:
        created = await create_notification(
            notification_data=NotificationCreate(
                title="Direct",
                body="Body",
                severity=NotificationSeverity.DANGER,
                is_active=True,
            ),
            db=session,
            current_user=admin,
        )
        assert created.title == "Direct"

        updated = await update_notification(
            notification_id=created.id,
            notification_data=NotificationUpdate(title="Updated"),
            db=session,
            current_user=admin,
        )
        assert updated.title == "Updated"

        await delete_notification(
            notification_id=created.id,
            db=session,
            current_user=admin,
        )
        remaining = await session.get(Notification, created.id)
        assert remaining is None


@pytest.mark.asyncio
async def test_list_admin_notifications_direct(session_maker):
    async with session_maker() as session:
        await session.execute(delete(Notification))
        await session.commit()

        note = await _create_notification(session_maker)

    async with session_maker() as session:
        results = await list_admin_notifications(
            db=session,
            current_user=UserRoles(user_id=1, is_admin=True),
        )
        assert [item.id for item in results] == [note.id]

    async with session_maker() as session:
        await session.execute(delete(Notification))
        await session.commit()
