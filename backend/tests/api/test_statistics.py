import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_statistics_endpoint_has_basic_fields(client):
    response = await client.get("/statistics")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    for key in {
        "totalUsers",
        "totalDownloads",
        "onlineUsers",
        "totalArchives",
        "totalCourses",
        "activeToday",
    }:
        assert key in data


@pytest.mark.asyncio
async def test_statistics_endpoint_handles_errors(monkeypatch, client):
    async def failing_execute(self, *args, **kwargs):
        raise RuntimeError("db error")

    monkeypatch.setattr(AsyncSession, "execute", failing_execute, raising=False)

    response = await client.get("/statistics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["totalUsers"] == 0
