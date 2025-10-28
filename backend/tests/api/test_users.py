import uuid

import pytest

from sqlalchemy import delete

from app.main import app
from app.models.models import User, UserRoles
from app.utils.auth import get_current_user

ADMIN_PATH = "/users/admin/users"


@pytest.mark.asyncio
async def test_admin_can_create_and_delete_user(client):
    unique_suffix = uuid.uuid4().hex[:8]
    payload = {
        "name": f"test-user-{unique_suffix}",
        "email": f"test-{unique_suffix}@example.com",
        "password": "StrongPass123",
        "is_admin": False,
    }
    app.dependency_overrides[get_current_user] = lambda: UserRoles(
        user_id=1,
        is_admin=True,
    )

    try:
        create_response = await client.post(ADMIN_PATH, json=payload)
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["email"] == payload["email"]
        assert created["name"] == payload["name"]

        delete_response = await client.delete(
            f"{ADMIN_PATH}/{created['id']}"
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["detail"] == "User deleted successfully"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_user_routes(client):
    app.dependency_overrides[get_current_user] = lambda: UserRoles(
        user_id=2,
        is_admin=False,
    )

    try:
        list_response = await client.get(ADMIN_PATH)
        assert list_response.status_code == 403

        payload = {
            "name": "no-admin",
            "email": "no-admin@example.com",
            "password": "password123",
            "is_admin": False,
        }
        create_response = await client.post(ADMIN_PATH, json=payload)
        assert create_response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_admin_can_list_users(client):
    app.dependency_overrides[get_current_user] = lambda: UserRoles(
        user_id=1,
        is_admin=True,
    )

    try:
        response = await client.get(ADMIN_PATH)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data, "Expected at least one user in seed data"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_admin_can_update_user(client, session_maker):
    unique = uuid.uuid4().hex[:8]
    async with session_maker() as session:
        user = User(
            name=f"update-target-{unique}",
            email=f"update-{unique}@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    app.dependency_overrides[get_current_user] = lambda: UserRoles(
        user_id=1,
        is_admin=True,
    )

    try:
        response = await client.put(
            f"{ADMIN_PATH}/{user_id}",
            json={"name": f"updated-{unique}", "is_admin": True},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == f"updated-{unique}"
        assert body["is_admin"] is True
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            record = await session.get(User, user_id)
            await session.delete(record)
            await session.commit()


@pytest.mark.asyncio
async def test_update_user_prevents_duplicate_email(client, session_maker):
    unique = uuid.uuid4().hex[:8]
    other = uuid.uuid4().hex[:8]
    async with session_maker() as session:
        existing = User(
            name=f"existing-user-{unique}",
            email=f"existing-{unique}@example.com",
            is_admin=False,
            is_local=True,
        )
        target = User(
            name=f"target-user-{other}",
            email=f"target-{other}@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add_all([existing, target])
        await session.commit()
        await session.refresh(target)
        target_id = target.id

    app.dependency_overrides[get_current_user] = lambda: UserRoles(
        user_id=1,
        is_admin=True,
    )

    try:
        response = await client.put(
            f"{ADMIN_PATH}/{target_id}",
            json={"email": f"existing-{unique}@example.com"},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        async with session_maker() as session:
            await session.execute(
                delete(User).where(
                    User.email.in_(
                        [
                            f"existing-{unique}@example.com",
                            f"target-{other}@example.com",
                        ]
                    )
                )
            )
            await session.commit()


@pytest.mark.asyncio
async def test_delete_user_cannot_delete_self(client):
    app.dependency_overrides[get_current_user] = lambda: UserRoles(
        user_id=5,
        is_admin=True,
    )

    try:
        response = await client.delete(f"{ADMIN_PATH}/5")
        assert response.status_code == 400
        assert response.json()["detail"] == "Cannot delete yourself"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_delete_user_not_found(client):
    app.dependency_overrides[get_current_user] = lambda: UserRoles(
        user_id=1,
        is_admin=True,
    )

    try:
        response = await client.delete(f"{ADMIN_PATH}/999999")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
