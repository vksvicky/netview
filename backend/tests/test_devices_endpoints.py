import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import SessionLocal, Device, Edge, Interface


@pytest.fixture(autouse=True)
def clean_database():
    """Clean the database before each test"""
    session = SessionLocal()
    session.query(Edge).delete()
    session.query(Interface).delete()
    session.query(Device).delete()
    session.commit()
    session.close()


def test_devices_list_empty():
    client = TestClient(app)
    resp = client.get("/devices")
    assert resp.status_code == 200
    assert resp.json() == []


