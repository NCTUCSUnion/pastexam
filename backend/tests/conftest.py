import asyncio
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from unittest.mock import AsyncMock

from app.core.config import settings
from app.main import app
from app.models.models import Archive, User
from app.utils.auth import get_password_hash

DATABASE_URL = (
    "postgresql+asyncpg://"
    f"{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    """Provide a single event loop for all async tests."""
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest_asyncio.fixture(autouse=True)
async def override_db_session(monkeypatch):
    """Swap engine per run to dodge asyncpg loop clashes."""
    engine = create_async_engine(
        DATABASE_URL,
        poolclass=NullPool,
        future=True,
    )
    session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    monkeypatch.setattr("app.db.session.engine", engine)
    monkeypatch.setattr("app.db.session.AsyncSessionLocal", session_maker)

    yield

    await engine.dispose()


@pytest.fixture()
def session_maker():
    from app.db.session import AsyncSessionLocal

    return AsyncSessionLocal


@pytest_asyncio.fixture
async def make_user(session_maker):
    """Factory fixture to create and cleanup test users."""
    created_ids: list[int] = []

    async def _make_user(**overrides):
        password = overrides.pop("password", "StrongPass123!")
        base = {
            "name": f"user-{uuid.uuid4().hex[:8]}",
            "email": f"user-{uuid.uuid4().hex[:8]}@example.com",
            "password_hash": get_password_hash(password),
            "is_local": True,
            "is_admin": False,
            "gemini_api_key": None,
        }

        if "password_hash" in overrides:
            base["password_hash"] = overrides.pop("password_hash")

        base.update(overrides)

        async with session_maker() as session:
            user = User(**base)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        created_ids.append(user.id)

        class _TestUser:
            __slots__ = ("_model", "password")

            def __init__(self, model: User, password_plain: str):
                self._model = model
                self.password = password_plain

            def __getattr__(self, item):
                return getattr(self._model, item)

            @property
            def model(self) -> User:
                return self._model

        return _TestUser(user, password)

    yield _make_user

    if created_ids:
        async with session_maker() as session:
            await session.execute(
                delete(Archive).where(Archive.uploader_id.in_(created_ids))
            )
            await session.execute(delete(User).where(User.id.in_(created_ids)))
            await session.commit()


@pytest_asyncio.fixture()
async def client(monkeypatch) -> AsyncIterator[AsyncClient]:
    """Return an AsyncClient backed by the FastAPI app."""
    monkeypatch.setattr("app.main.init_db", AsyncMock())
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as async_client:
        yield async_client
