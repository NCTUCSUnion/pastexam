import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

from app.api.services.meme import get_random_meme

from app.models.models import Meme


@pytest.mark.asyncio
async def test_get_random_meme_returns_meme(client, session_maker):
    created_id = None
    async with session_maker() as session:
        existing = await session.execute(select(Meme))
        meme = existing.scalars().first()
        if meme is None:
            meme = Meme(content="Seed", language="en")
            session.add(meme)
            await session.commit()
            await session.refresh(meme)
            created_id = meme.id

    try:
        response = await client.get("/meme")
        assert response.status_code == 200

        payload = response.json()
        assert payload["content"]
        assert payload["language"]
    finally:
        if created_id is not None:
            async with session_maker() as session:
                await session.execute(
                    delete(Meme).where(Meme.id == created_id)
                )
                await session.commit()


@pytest.mark.asyncio
async def test_get_random_meme_returns_404_when_empty(client, session_maker):
    async with session_maker() as session:
        existing = await session.execute(select(Meme))
        memes = existing.scalars().all()
        snapshot = [
            {"content": meme.content, "language": meme.language}
            for meme in memes
        ]
        await session.execute(delete(Meme))
        await session.commit()

    try:
        response = await client.get("/meme")
        assert response.status_code == 404
        assert response.json()["detail"] == "No memes available"
    finally:
        if snapshot:
            async with session_maker() as session:
                session.add_all(
                    Meme(content=item["content"], language=item["language"])
                    for item in snapshot
                )
                await session.commit()


@pytest.mark.asyncio
async def test_get_random_meme_direct_returns_entry(session_maker):
    async with session_maker() as session:
        await session.execute(delete(Meme))
        await session.commit()

        meme = Meme(content="Hi", language="en")
        session.add(meme)
        await session.commit()
        await session.refresh(meme)

        result = await get_random_meme(db=session)
        assert result.id == meme.id

        await session.execute(delete(Meme).where(Meme.id == meme.id))
        await session.commit()


@pytest.mark.asyncio
async def test_get_random_meme_direct_raises_when_empty(session_maker):
    async with session_maker() as session:
        await session.execute(delete(Meme))
        await session.commit()

        with pytest.raises(HTTPException):
            await get_random_meme(db=session)
