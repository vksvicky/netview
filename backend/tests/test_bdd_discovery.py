import pytest
from pytest_bdd import scenarios, given, when, then
from sqlalchemy.orm import Session
from app.db import initialize_database
from app.models import SessionLocal, Device
from app.services.discovery import DiscoveryService
from app.services.snmp import SnmpClient


scenarios("features/discovery.feature")


@pytest.fixture
def db() -> Session:
    initialize_database()
    session = SessionLocal()
    yield session
    session.close()


@given("an empty database")
def given_empty_db(db: Session):
    db.query(Device).delete()
    db.commit()


@when("discovery runs with mocked SNMP responses")
def when_discovery_runs(mocker, db: Session):
    import asyncio
    from app.services.fast_discovery import FastDiscoveryService
    
    mock_snmp = SnmpClient(config={})
    mock_fast_discovery = FastDiscoveryService(config={})
    
    # Mock the fast discovery to return test devices
    mocker.patch.object(
        mock_fast_discovery,
        "discover_devices",
        return_value=[
            {
                "id": "dev1",
                "hostname": "switch1",
                "mgmtIp": "10.0.0.1",
                "vendor": "Generic",
                "interfaces": [
                    {"ifIndex": 1, "name": "Gi0/1", "adminStatus": "up", "operStatus": "up"}
                ],
            }
        ],
    )
    
    svc = DiscoveryService(mock_snmp, mock_fast_discovery)
    asyncio.run(svc.run_discovery(db))


@then("the devices endpoint returns discovered devices")
def then_devices_present(db: Session):
    devices = db.query(Device).all()
    assert any(d.id == "dev1" for d in devices)


@then("the topology contains nodes")
def then_topology_has_nodes(db: Session):
    devices = db.query(Device).all()
    assert len(devices) > 0


