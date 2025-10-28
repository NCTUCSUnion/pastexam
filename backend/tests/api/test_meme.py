import pytest
from sqlalchemy import delete, select

from app.models.models import Meme


@pytest.mark.asyncio
async def test_get_random_meme_returns_meme(client):
    response = await client.get("/meme")
    assert response.status_code == 200

    payload = response.json()
    assert payload["content"]
    assert payload["language"]


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
