import uuid

import pytest

from app.main import app
from app.models.models import UserRoles
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
