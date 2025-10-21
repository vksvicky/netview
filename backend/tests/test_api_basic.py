import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/metrics")
        assert resp.status_code == 200
        assert b"netview_http_requests_total" in resp.content


@pytest.mark.asyncio
async def test_topology_empty():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/topology")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nodes"] == []
        assert data["edges"] == []


