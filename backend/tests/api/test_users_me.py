import pytest

from app.main import app
from app.models.models import User, UserRoles
from app.utils.auth import get_current_user


def _override_user(user_id: int):
    async def _get_current_user():
        return UserRoles(user_id=user_id, is_admin=False)

    return _get_current_user


@pytest.mark.asyncio
async def test_get_me_sets_nickname_when_missing(client, session_maker, make_user):
    user = await make_user(nickname=None)
    app.dependency_overrides[get_current_user] = _override_user(user.id)

    try:
        response = await client.get("/users/me")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == user.id
        assert body["nickname"] == user.name

        async with session_maker() as session:
            stored = await session.get(User, user.id)
            assert stored.nickname == user.name
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_me_returns_404_when_user_missing(client, make_user, session_maker):
    user = await make_user()
    async with session_maker() as session:
        stored = await session.get(User, user.id)
        await session.delete(stored)
        await session.commit()

    app.dependency_overrides[get_current_user] = _override_user(user.id)
    try:
        response = await client.get("/users/me")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_my_nickname_trims_and_updates(client, make_user):
    user = await make_user()
    app.dependency_overrides[get_current_user] = _override_user(user.id)

    try:
        response = await client.patch(
            "/users/me/nickname", json={"nickname": "  New Nick  "}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == user.id
        assert body["nickname"] == "New Nick"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_my_nickname_empty_resets_to_name(client, make_user):
    user = await make_user()
    app.dependency_overrides[get_current_user] = _override_user(user.id)

    try:
        response = await client.patch("/users/me/nickname", json={"nickname": "   "})
        assert response.status_code == 200
        body = response.json()
        assert body["nickname"] == user.name
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_my_nickname_rejects_too_long(client, make_user):
    user = await make_user()
    app.dependency_overrides[get_current_user] = _override_user(user.id)

    try:
        response = await client.patch("/users/me/nickname", json={"nickname": "a" * 16})
        assert response.status_code == 400
        assert "暱稱超出" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_my_nickname_404_when_user_missing(
    client, make_user, session_maker
):
    user = await make_user()
    async with session_maker() as session:
        stored = await session.get(User, user.id)
        await session.delete(stored)
        await session.commit()

    app.dependency_overrides[get_current_user] = _override_user(user.id)
    try:
        response = await client.patch("/users/me/nickname", json={"nickname": "Nick"})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)
