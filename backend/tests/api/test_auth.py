import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.api.services import auth as auth_service
from app.main import app
from app.models.models import User, UserRoles
from app.utils.auth import get_current_user


@pytest.mark.asyncio
async def test_local_login_success(client, make_user):
    user = await make_user()

    response = await client.post(
        "/auth/login",
        data={
            "username": user.name,
            "password": user.password,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


@pytest.mark.asyncio
async def test_local_login_failure(client):
    response = await client.post(
        "/auth/login",
        data={"username": f"unknown-{uuid.uuid4().hex[:8]}", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_oauth_login_and_callback_creates_user(
    client,
    monkeypatch,
    session_maker,
):
    login_response = await client.get(
        "/auth/oauth/login",
        follow_redirects=False,
    )
    assert login_response.status_code in {302, 307}

    location = login_response.headers["location"]
    parsed = urlparse(location)
    query = parse_qs(parsed.query)
    state = query["state"][0]

    async def fake_oauth_callback(code, state_param, stored_state):
        assert code == "dummy-code"
        assert state_param == state
        assert stored_state == state
        return {
            "provider": "nycu",
            "sub": "oauth-subject",
            "email": "oauthuser@example.com",
            "name": "OAuth User",
        }

    monkeypatch.setattr(
        "app.api.services.auth.oauth_callback",
        fake_oauth_callback,
    )

    callback_response = await client.get(
        "/auth/oauth/callback",
        params={"code": "dummy-code", "state": state},
        follow_redirects=False,
    )
    assert callback_response.status_code in {302, 307}
    redirect_url = callback_response.headers["location"]
    assert "/login/callback" in redirect_url
    assert "token=" not in redirect_url
    code = parse_qs(urlparse(redirect_url).query)["code"][0]

    # Another browser (no session cookie) cannot redeem the code
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as other_browser:
        stolen = await other_browser.post("/auth/oauth/exchange", json={"code": code})
    assert stolen.status_code == 400

    exchange = await client.post("/auth/oauth/exchange", json={"code": code})
    assert exchange.status_code == 200
    assert exchange.json()["access_token"]

    # One-time use
    replay = await client.post("/auth/oauth/exchange", json={"code": code})
    assert replay.status_code == 400

    async with session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == "oauthuser@example.com")
        )
        created_user = result.scalar_one_or_none()
        assert created_user is not None
        assert created_user.oauth_provider == "nycu"
        assert created_user.oauth_sub == "oauth-subject"
        await session.execute(
            delete(User).where(User.email == "oauthuser@example.com")
        )
        await session.commit()


@pytest.mark.asyncio
async def test_oauth_callback_invalid_response_redirects_with_error(
    client,
    monkeypatch,
):
    login_response = await client.get(
        "/auth/oauth/login",
        follow_redirects=False,
    )
    location = login_response.headers["location"]
    state = parse_qs(urlparse(location).query)["state"][0]

    async def fake_invalid_callback(code, state_param, stored_state):
        assert state_param == state
        return {}

    monkeypatch.setattr(
        "app.api.services.auth.oauth_callback",
        fake_invalid_callback,
    )

    callback_response = await client.get(
        "/auth/oauth/callback",
        params={"code": "bad-code", "state": state},
        follow_redirects=False,
    )
    assert callback_response.status_code in {302, 307}
    query = parse_qs(urlparse(callback_response.headers["location"]).query)
    assert query == {"error": ["provider"]}


@pytest.mark.asyncio
async def test_oauth_callback_updates_existing_user(
    client,
    monkeypatch,
    session_maker,
):
    async def trigger_callback(return_info):
        login_response = await client.get(
            "/auth/oauth/login",
            follow_redirects=False,
        )
        assert login_response.status_code in {302, 307}
        location = login_response.headers["location"]
        state = parse_qs(urlparse(location).query)["state"][0]

        async def fake_oauth_callback(code, state_param, stored_state):
            assert state_param == state == stored_state
            return return_info

        monkeypatch.setattr(
            "app.api.services.auth.oauth_callback",
            fake_oauth_callback,
        )

        return await client.get(
            "/auth/oauth/callback",
            params={"code": "dummy", "state": state},
            follow_redirects=False,
        )

    unique_email = f"{uuid.uuid4().hex}@example.com"
    info = {
        "provider": "nycu",
        "sub": "existing-sub",
        "email": unique_email,
        "name": "Existing User",
    }

    async with session_maker() as session:
        await session.execute(delete(User).where(User.email == unique_email))
        await session.commit()
    create_response = await trigger_callback(info)
    assert create_response.status_code in {302, 307}

    async with session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == info["email"])
        )
        user = result.scalar_one()
        first_login = user.last_login
        user_id = user.id

    update_info = {
        "provider": "nycu",
        "sub": "existing-sub",
        "email": unique_email,
        "name": "Existing User",
    }
    update_response = await trigger_callback(update_info)
    assert update_response.status_code in {302, 307}

    async with session_maker() as session:
        refreshed = await session.get(User, user_id)
        assert refreshed.last_login is not None
        assert refreshed.last_login >= first_login
        await session.delete(refreshed)
        await session.commit()


@pytest.mark.asyncio
async def test_logout_updates_last_logout_and_blacklists(
    client,
    make_user,
    session_maker,
    monkeypatch,
):
    user = await make_user()
    captured_tokens: list[str] = []

    async def fake_blacklist(token: str):
        captured_tokens.append(token)

    async def fake_get_current_user():
        return UserRoles(user_id=user.id, is_admin=False)

    monkeypatch.setattr(
        "app.api.services.auth.blacklist_token",
        fake_blacklist,
    )
    app.dependency_overrides[get_current_user] = fake_get_current_user

    try:
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer token-123"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
        assert captured_tokens == ["token-123"]

        async with session_maker() as session:
            refreshed = await session.get(User, user.id)
            assert refreshed.last_logout is not None
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_login_direct_returns_token(
    monkeypatch,
    make_user,
    session_maker,
):
    user = await make_user()
    captured = {}

    def fake_encode(payload, key, algorithm):
        captured["payload"] = payload
        return "fake-token"

    monkeypatch.setattr("app.api.services.auth.jwt.encode", fake_encode)

    async with session_maker() as session:
        response = await auth_service.login(
            form_data=SimpleNamespace(
                username=user.name,
                password=user.password,
            ),
            db=session,
        )
        assert response == {
            "access_token": "fake-token",
            "token_type": "bearer",
        }

    async with session_maker() as verify_session:
        refreshed = await verify_session.get(User, user.id)
        assert refreshed.last_login is not None
        assert captured["payload"]["uid"] == user.id


@pytest.mark.asyncio
async def test_login_direct_rejects_unknown_user(session_maker):
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await auth_service.login(
                form_data=SimpleNamespace(
                    username="missing",
                    password="nope",
                ),
                db=session,
            )
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_callback_direct_creates_user(monkeypatch, session_maker):
    state = "csrf-token"
    fake_request = SimpleNamespace(session={"csrf_token": state})
    monkeypatch.setattr(
        "app.api.services.auth.oauth_callback",
        AsyncMock(
            return_value={
                "provider": "nycu",
                "sub": "direct-sub",
                "email": "direct@example.com",
                "name": "Direct User",
            }
        ),
    )
    monkeypatch.setattr(
        "app.api.services.auth.jwt.encode",
        lambda payload, key, algorithm: "direct-token",
    )

    async with session_maker() as session:
        response = await auth_service.auth_callback_endpoint(
            request=fake_request,
            code="code-1",
            state=state,
            db=session,
        )
        assert response.status_code in {302, 307}
        location = response.headers["location"]
        assert "direct-token" not in location
        code = parse_qs(urlparse(location).query)["code"][0]
        assert fake_request.session["oauth_code"] == code

    async with session_maker() as session:
        created = await session.execute(
            select(User).where(User.email == "direct@example.com")
        )
        user = created.scalar_one_or_none()
        assert user is not None
        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
async def test_logout_direct_without_header(monkeypatch, session_maker):
    user = User(
        name="logout-direct",
        email="logout-direct@example.com",
        is_admin=False,
        is_local=True,
    )
    async with session_maker() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)

    fake_request = SimpleNamespace(headers={})
    calls = []
    monkeypatch.setattr(
        "app.api.services.auth.blacklist_token",
        AsyncMock(side_effect=calls.append),
    )

    async with session_maker() as session:
        result = await auth_service.logout(
            request=fake_request,
            current_user=UserRoles(user_id=user.id, is_admin=False),
            db=session,
        )
        assert result == {"message": "Successfully logged out"}

    async with session_maker() as session:
        refreshed = await session.get(User, user.id)
        assert refreshed.last_logout is not None
        await session.delete(refreshed)
        await session.commit()

    assert calls == []


async def _oauth_callback_with(client, monkeypatch, info, **extra_params):
    login_response = await client.get("/auth/oauth/login", follow_redirects=False)
    state = parse_qs(urlparse(login_response.headers["location"]).query)["state"][0]
    monkeypatch.setattr(
        "app.api.services.auth.oauth_callback", AsyncMock(return_value=info)
    )
    response = await client.get(
        "/auth/oauth/callback",
        params={"code": "dummy", "state": state, **extra_params},
        follow_redirects=False,
    )
    assert response.status_code in {302, 307}
    return parse_qs(urlparse(response.headers["location"]).query)


@pytest.mark.asyncio
async def test_oauth_callback_rejects_suspended_user(
    client, monkeypatch, session_maker
):
    suffix = uuid.uuid4().hex[:8]
    async with session_maker() as session:
        user = User(
            name=f"suspended-{suffix}",
            email=f"suspended-{suffix}@example.com",
            oauth_provider="nycu",
            oauth_sub=f"suspended-{suffix}",
            is_admin=True,
            deleted_at=datetime.now(UTC),
        )
        session.add(user)
        await session.commit()
        user_id = user.id

    try:
        query = await _oauth_callback_with(
            client,
            monkeypatch,
            {
                "provider": "nycu",
                "sub": f"suspended-{suffix}",
                "email": f"suspended-{suffix}@example.com",
                "name": f"suspended-{suffix}",
            },
        )
        assert query == {"error": ["suspended"]}

        async with session_maker() as session:
            still_suspended = await session.get(User, user_id)
            assert still_suspended.deleted_at is not None
    finally:
        async with session_maker() as session:
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()


@pytest.mark.asyncio
async def test_oauth_callback_name_conflict_redirects_with_error(
    client, monkeypatch, make_user
):
    existing = await make_user(name=f"taken-{uuid.uuid4().hex[:8]}")

    query = await _oauth_callback_with(
        client,
        monkeypatch,
        {
            "provider": "nycu",
            "sub": f"new-sub-{uuid.uuid4().hex[:8]}",
            "email": f"{uuid.uuid4().hex[:8]}@example.com",
            "name": existing.name,
        },
    )
    assert query == {"error": ["conflict"]}


@pytest.mark.asyncio
async def test_oauth_callback_denied_by_provider(client, monkeypatch):
    query = await _oauth_callback_with(
        client, monkeypatch, {}, error="access_denied"
    )
    assert query == {"error": ["denied"]}


@pytest.mark.asyncio
async def test_oauth_callback_bad_state_redirects_with_error(client):
    response = await client.get(
        "/auth/oauth/callback",
        params={"code": "dummy", "state": "forged"},
        follow_redirects=False,
    )
    assert response.status_code in {302, 307}
    query = parse_qs(urlparse(response.headers["location"]).query)
    assert query == {"error": ["state"]}


@pytest.mark.asyncio
async def test_oauth_exchange_rejects_unknown_code(client):
    response = await client.post("/auth/oauth/exchange", json={"code": "nope"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_oauth_exchange_rejects_non_ascii_code(client, monkeypatch):
    query = await _oauth_callback_with(
        client,
        monkeypatch,
        {
            "provider": "nycu",
            "sub": f"ascii-{uuid.uuid4().hex[:8]}",
            "email": f"{uuid.uuid4().hex[:8]}@example.com",
            "name": f"ascii-{uuid.uuid4().hex[:8]}",
        },
    )
    assert "code" in query

    response = await client.post("/auth/oauth/exchange", json={"code": "代碼"})
    assert response.status_code == 400
