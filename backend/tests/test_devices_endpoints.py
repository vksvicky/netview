import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_devices_list_empty():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/devices")
        assert resp.status_code == 200
        assert resp.json() == []


