from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from app.services.auth import oauth_callback


class FakeAsyncClient:
    def __init__(
        self,
        *,
        token_status=200,
        profile_status=200,
        token_payload=None,
        profile_payload=None,
        token_exc=None,
        profile_exc=None,
    ):
        self.token_status = token_status
        self.profile_status = profile_status
        self.token_payload = token_payload or {"access_token": "token-123"}
        self.profile_payload = profile_payload or {
            "username": "student",
            "email": "student@example.com",
        }
        self.token_exc = token_exc
        self.profile_exc = profile_exc
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *_args, **_kwargs):
        self.calls.append(("post", _args, _kwargs))
        if self.token_exc:
            raise self.token_exc
        return SimpleNamespace(
            status_code=self.token_status,
            json=lambda: self.token_payload,
        )

    async def get(self, *_args, **_kwargs):
        self.calls.append(("get", _args, _kwargs))
        if self.profile_exc:
            raise self.profile_exc
        return SimpleNamespace(
            status_code=self.profile_status,
            json=lambda: self.profile_payload,
        )


@pytest.mark.asyncio
async def test_oauth_callback_valid(monkeypatch):
    fake_client = FakeAsyncClient()
    monkeypatch.setattr(httpx, "AsyncClient", lambda *_, **__: fake_client)

    result = await oauth_callback(
        code="abc",
        state="same",
        stored_state="same",
    )
    assert result["provider"] == "nycu"
    assert result["sub"] == "student"
    assert result["email"] == "student@example.com"


@pytest.mark.asyncio
async def test_oauth_callback_invalid_state():
    with pytest.raises(HTTPException) as exc:
        await oauth_callback(code="abc", state="one", stored_state="two")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_oauth_callback_token_request_error(monkeypatch):
    fake_request = httpx.Request("POST", "https://oauth/token")
    fake_client = FakeAsyncClient(
        token_exc=httpx.RequestError("boom", request=fake_request)
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda *_, **__: fake_client)

    with pytest.raises(HTTPException) as exc:
        await oauth_callback(code="abc", state="s", stored_state="s")
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_oauth_callback_token_failure_status(monkeypatch):
    fake_client = FakeAsyncClient(token_status=400)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *_, **__: fake_client)

    with pytest.raises(HTTPException) as exc:
        await oauth_callback(code="abc", state="s", stored_state="s")
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_oauth_callback_profile_request_error(monkeypatch):
    fake_request = httpx.Request("GET", "https://oauth/userinfo")
    fake_client = FakeAsyncClient(
        profile_exc=httpx.RequestError("oops", request=fake_request)
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda *_, **__: fake_client)

    with pytest.raises(HTTPException) as exc:
        await oauth_callback(code="abc", state="s", stored_state="s")
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_oauth_callback_profile_failure_status(monkeypatch):
    fake_client = FakeAsyncClient(profile_status=500)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *_, **__: fake_client)

    with pytest.raises(HTTPException) as exc:
        await oauth_callback(code="abc", state="s", stored_state="s")
    assert exc.value.status_code == 500
