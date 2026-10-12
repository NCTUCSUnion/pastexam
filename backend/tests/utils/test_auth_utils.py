import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.models.models import User
from app.utils import auth as auth_utils


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def setex(self, key: str, expire: int, value: str):
        self.store[key] = value

    async def get(self, key: str):
        return self.store.get(key)


@pytest.mark.asyncio
async def test_password_hash_roundtrip():
    password = "SuperSecret123!"
    hashed = auth_utils.get_password_hash(password)
    assert auth_utils.verify_password(password, hashed) is True
    assert auth_utils.verify_password("wrong", hashed) is False


@pytest.mark.asyncio
async def test_blacklist_and_check_token(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(auth_utils, "get_redis", lambda: fake_redis)

    token = "token-abc"
    await auth_utils.blacklist_token(token, expire_seconds=10)
    assert await auth_utils.is_token_blacklisted(token) is True
    assert await auth_utils.is_token_blacklisted("other") is False


@pytest.mark.asyncio
async def test_authenticate_user_validates_credentials(session_maker):
    password = "PlainPassword!"
    hashed = auth_utils.get_password_hash(password)
    suffix = uuid.uuid4().hex[:8]

    async with session_maker() as session:
        user = User(
            name=f"auth-user-{suffix}",
            email=f"auth-user-{suffix}@example.com",
            password_hash=hashed,
            is_local=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_name = user.name

    async with session_maker() as session:
        found = await auth_utils.authenticate_user(
            user_name,
            password,
            session,
        )
        assert found is not None
        missing = await auth_utils.authenticate_user(
            user_name,
            "wrong",
            session,
        )
        assert missing is None
        await session.delete(found)
        await session.commit()


@pytest.mark.asyncio
async def test_get_current_user_success(monkeypatch, session_maker):
    fake_redis = FakeRedis()
    monkeypatch.setattr(auth_utils, "get_redis", lambda: fake_redis)
    suffix = uuid.uuid4().hex[:8]

    async with session_maker() as session:
        user = User(
            name=f"token-user-{suffix}",
            email=f"token-user-{suffix}@example.com",
            password_hash=None,
            is_local=False,
            is_admin=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id

    token = auth_utils.jwt.encode(
        {
            "uid": user_id,
            "exp": int(
                (
                    datetime.now(UTC)
                    + timedelta(minutes=5)
                ).timestamp()
            ),
        },
        auth_utils.settings.SECRET_KEY,
        algorithm=auth_utils.settings.ALGORITHM,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    async with session_maker() as session:
        user_roles = await auth_utils.get_current_user(
            token=credentials,
            db=session,
        )
        assert user_roles.user_id == user_id
        assert user_roles.is_admin is True
        refreshed = await session.get(User, user_id)
        await session.delete(refreshed)
        await session.commit()


@pytest.mark.asyncio
async def test_get_current_user_blacklisted(monkeypatch, session_maker):
    fake_redis = FakeRedis()
    fake_redis.store["blacklist:blocked"] = "1"
    monkeypatch.setattr(auth_utils, "get_redis", lambda: fake_redis)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="blocked",
    )
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await auth_utils.get_current_user(
                token=credentials,
                db=session,
            )
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_user(monkeypatch, session_maker):
    fake_redis = FakeRedis()
    monkeypatch.setattr(auth_utils, "get_redis", lambda: fake_redis)

    token = auth_utils.jwt.encode(
        {
            "uid": 999999,
            "exp": int(
                (
                    datetime.now(UTC)
                    + timedelta(minutes=5)
                ).timestamp()
            ),
        },
        auth_utils.settings.SECRET_KEY,
        algorithm=auth_utils.settings.ALGORITHM,
    )
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await auth_utils.get_current_user(
                token=credentials,
                db=session,
            )
        assert exc.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_token",
    [
        # Expired
        lambda: auth_utils.jwt.encode(
            {"uid": 1, "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp())},
            auth_utils.settings.SECRET_KEY,
            algorithm=auth_utils.settings.ALGORITHM,
        ),
        # Signed with another key
        lambda: auth_utils.jwt.encode(
            {"uid": 1, "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())},
            "not-the-server-secret-key-0123456789",
            algorithm=auth_utils.settings.ALGORITHM,
        ),
        # Unsigned ("alg": "none")
        lambda: auth_utils.jwt.encode(
            {"uid": 1, "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())},
            None,
            algorithm="none",
        ),
    ],
    ids=["expired", "wrong-key", "alg-none"],
)
async def test_get_current_user_rejects_invalid_tokens(
    monkeypatch, session_maker, make_token
):
    monkeypatch.setattr(auth_utils, "get_redis", lambda: FakeRedis())
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=make_token())
    async with session_maker() as session:
        with pytest.raises(HTTPException) as exc:
            await auth_utils.get_current_user(token=credentials, db=session)
    assert exc.value.status_code == 401
