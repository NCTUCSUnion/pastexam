import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from unittest.mock import AsyncMock

from app.core.config import settings
from app.main import app

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
    """Use a dedicated engine/sessionmaker for tests to avoid pool reuse issues."""
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool, future=True)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    monkeypatch.setattr("app.db.session.engine", engine)
    monkeypatch.setattr("app.db.session.AsyncSessionLocal", session_maker)

    yield

    await engine.dispose()


@pytest_asyncio.fixture()
async def client(monkeypatch) -> AsyncIterator[AsyncClient]:
    """Return an AsyncClient backed by the FastAPI app."""
    monkeypatch.setattr("app.main.init_db", AsyncMock())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
