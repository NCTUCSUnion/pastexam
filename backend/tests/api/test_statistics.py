import pytest


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
