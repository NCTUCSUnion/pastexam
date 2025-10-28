import pytest
from sqlalchemy import delete, select
from urllib.parse import urlparse, parse_qs

from app.models.models import User


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
        data={"username": "unknown", "password": "wrong"},
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
    assert "token=" in redirect_url

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
async def test_oauth_callback_invalid_response_returns_400(
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
    assert callback_response.status_code == 400
    assert callback_response.json()["detail"] == "Invalid OAuth response"
