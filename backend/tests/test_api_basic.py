import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import SessionLocal, Device, Edge, Interface
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clean_database():
    """Clean the database before each test"""
    session = SessionLocal()
    session.query(Edge).delete()
    session.query(Interface).delete()
    session.query(Device).delete()
    session.commit()
    session.close()


def test_metrics_endpoint():
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"netview_http_requests_total" in resp.content


@patch('app.routers.topology._add_missing_router')
def test_topology_empty(mock_add_router):
    """Test topology endpoint returns empty when no devices exist"""
    mock_add_router.return_value = None  # Don't add any router
    client = TestClient(app)
    resp = client.get("/topology")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nodes"] == []
    assert data["edges"] == []


