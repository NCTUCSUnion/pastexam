import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import delete

from app.api.services.users import (
    create_user,
    delete_user,
    get_users,
    update_user,
)
from app.main import app
from app.models.models import User, UserCreate, UserRoles, UserUpdate
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

        delete_response = await client.delete(f"{ADMIN_PATH}/{created['id']}")
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


@pytest.mark.asyncio
async def test_get_users_direct_requires_admin(session_maker):
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await get_users(
                current_user=UserRoles(user_id=1, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_users_direct_returns_users(session_maker):
    async with session_maker() as session:
        user = User(
            name="direct-list",
            email="direct-list@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add(user)
        await session.commit()

        users = await get_users(
            current_user=UserRoles(user_id=2, is_admin=True),
            db=session,
        )
        assert any(item.id == user.id for item in users)

        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
async def test_create_user_direct_duplicate_email(session_maker):
    async with session_maker() as session:
        existing = User(
            name="dup-email-existing",
            email="dup-email@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add(existing)
        await session.commit()

        with pytest.raises(HTTPException) as exc:
            await create_user(
                user_data=UserCreate(
                    name="dup-email-new",
                    email="dup-email@example.com",
                    password="irrelevant",
                    is_admin=False,
                ),
                current_user=UserRoles(user_id=1, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

        await session.delete(existing)
        await session.commit()


@pytest.mark.asyncio
async def test_create_user_direct_duplicate_name(session_maker):
    async with session_maker() as session:
        existing = User(
            name="dup-name",
            email="dup-name-existing@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add(existing)
        await session.commit()

        with pytest.raises(HTTPException) as exc:
            await create_user(
                user_data=UserCreate(
                    name="dup-name",
                    email="dup-name-new@example.com",
                    password="irrelevant",
                    is_admin=False,
                ),
                current_user=UserRoles(user_id=1, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

        await session.delete(existing)
        await session.commit()


@pytest.mark.asyncio
async def test_create_user_direct_success(monkeypatch, session_maker):
    async with session_maker() as session:
        monkeypatch.setattr(
            "app.api.services.users.get_password_hash",
            lambda password: f"hashed-{password}",
        )
        created = await create_user(
            user_data=UserCreate(
                name="direct-create",
                email="direct-create@example.com",
                password="SecretPass1!",
                is_admin=True,
            ),
            current_user=UserRoles(user_id=1, is_admin=True),
            db=session,
        )
        assert created.password_hash == "hashed-SecretPass1!"
        assert created.is_admin is True

        await session.delete(created)
        await session.commit()


@pytest.mark.asyncio
async def test_update_user_direct_not_found(session_maker):
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await update_user(
                user_id=99999,
                user_data=UserUpdate(name="missing"),
                current_user=UserRoles(user_id=1, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_user_direct_duplicate_name(session_maker):
    async with session_maker() as session:
        existing = User(
            name="existing-name",
            email="existing-name@example.com",
            is_admin=False,
            is_local=True,
        )
        target = User(
            name="target-name",
            email="target-name@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add_all([existing, target])
        await session.commit()
        await session.refresh(target)

        with pytest.raises(HTTPException) as exc:
            await update_user(
                user_id=target.id,
                user_data=UserUpdate(name="existing-name"),
                current_user=UserRoles(user_id=1, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

        await session.delete(existing)
        await session.delete(target)
        await session.commit()


@pytest.mark.asyncio
async def test_update_user_direct_duplicate_email(session_maker):
    async with session_maker() as session:
        existing = User(
            name="existing-email",
            email="existing-email@example.com",
            is_admin=False,
            is_local=True,
        )
        target = User(
            name="target-email",
            email="target-email@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add_all([existing, target])
        await session.commit()
        await session.refresh(target)

        with pytest.raises(HTTPException) as exc:
            await update_user(
                user_id=target.id,
                user_data=UserUpdate(email="existing-email@example.com"),
                current_user=UserRoles(user_id=1, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400

        await session.delete(existing)
        await session.delete(target)
        await session.commit()


@pytest.mark.asyncio
async def test_update_user_direct_updates_fields(monkeypatch, session_maker):
    async with session_maker() as session:
        user = User(
            name="update-direct",
            email="update-direct@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        monkeypatch.setattr(
            "app.api.services.users.get_password_hash",
            lambda password: f"hashed-{password}",
        )

        updated = await update_user(
            user_id=user.id,
            user_data=UserUpdate(
                name="update-direct-new",
                email="update-direct-new@example.com",
                password="NewPass!",
                is_admin=True,
            ),
            current_user=UserRoles(user_id=1, is_admin=True),
            db=session,
        )
        assert updated.name == "update-direct-new"
        assert updated.email == "update-direct-new@example.com"
        assert updated.password_hash == "hashed-NewPass!"
        assert updated.is_admin is True

        await session.delete(updated)
        await session.commit()


@pytest.mark.asyncio
async def test_update_user_direct_requires_admin(session_maker):
    async with session_maker() as session:
        user = User(
            name="update-requires-admin",
            email="update-requires-admin@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        with pytest.raises(HTTPException) as exc:
            await update_user(
                user_id=user.id,
                user_data=UserUpdate(name="nope"),
                current_user=UserRoles(user_id=2, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 403

        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
async def test_delete_user_direct_requires_admin(session_maker):
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await delete_user(
                user_id=1,
                current_user=UserRoles(user_id=2, is_admin=False),
                db=session,
            )
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_direct_self_forbidden(session_maker):
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await delete_user(
                user_id=5,
                current_user=UserRoles(user_id=5, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_user_direct_not_found(session_maker):
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await delete_user(
                user_id=12345,
                current_user=UserRoles(user_id=1, is_admin=True),
                db=session,
            )
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_direct_success(session_maker):
    async with session_maker() as session:
        unique = uuid.uuid4().hex[:8]
        user = User(
            name=f"delete-direct-{unique}",
            email=f"delete-direct-{unique}@example.com",
            is_admin=False,
            is_local=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        response = await delete_user(
            user_id=user.id,
            current_user=UserRoles(user_id=1, is_admin=True),
            db=session,
        )
        assert response["detail"] == "User deleted successfully"

        remaining = await session.get(User, user.id)
        assert remaining is not None
        assert remaining.deleted_at is not None
