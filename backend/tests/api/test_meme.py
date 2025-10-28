import pytest


@pytest.mark.asyncio
async def test_get_random_meme_returns_meme(client):
    response = await client.get("/meme")
    assert response.status_code == 200

    payload = response.json()
    assert payload["content"]
    assert payload["language"]
