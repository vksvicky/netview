import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from pytest_bdd import given, when, then, scenario

from app.models import SessionLocal, Device, DeviceHistory
from app.services.device_history import device_history_service


@pytest.fixture(autouse=True)
def clean_database():
    """Clean the database before each test"""
    from app.models import init_db
    init_db()  # Initialize database tables
    session = SessionLocal()
    session.query(DeviceHistory).delete()
    session.query(Device).delete()
    session.commit()
    session.close()


def get_session() -> Session:
    """Get a database session"""
    return SessionLocal()


def get_device_history_service():
    """Get the device history service instance"""
    return device_history_service


# Given steps
@given('an empty database')
def step_empty_database():
    """Ensure the database is empty"""
    session = get_session()
    session.query(DeviceHistory).delete()
    session.query(Device).delete()
    session.commit()
    session.close()


@given('a device "{device_id}" exists in the database')
def step_device_exists(device_id):
    """Create a device in the database"""
    session = get_session()
    device = Device(
        id=device_id,
        hostname=f"Device {device_id}",
        mgmt_ip="192.168.1.100",
        vendor="Test Vendor",
        model="Test Model",
        status="up",
        last_seen=datetime.now(UTC).replace(tzinfo=None)
    )
    session.add(device)
    session.commit()
    session.close()


@given('a device "{device_id}" exists with IP "{ip_address}"')
def step_device_exists_with_ip(device_id, ip_address):
    """Create a device with specific IP"""
    session = get_session()
    device = Device(
        id=device_id,
        hostname=f"Device {device_id}",
        mgmt_ip=ip_address,
        vendor="Test Vendor",
        model="Test Model",
        status="up",
        last_seen=datetime.now(UTC).replace(tzinfo=None)
    )
    session.add(device)
    session.commit()
    session.close()


@given('a device "{device_id}" exists with status "{status}"')
def step_device_exists_with_status(device_id, status):
    """Create a device with specific status"""
    session = get_session()
    device = Device(
        id=device_id,
        hostname=f"Device {device_id}",
        mgmt_ip="192.168.1.100",
        vendor="Test Vendor",
        model="Test Model",
        status=status,
        last_seen=datetime.now(UTC).replace(tzinfo=None)
    )
    session.add(device)
    session.commit()
    session.close()


@given('a device "{device_id}" has an active session started {hours:d} hours ago')
def step_device_has_active_session(device_id, hours):
    """Create a device with an active session"""
    session = get_session()
    
    # Create the device
    device = Device(
        id=device_id,
        hostname=f"Device {device_id}",
        mgmt_ip="192.168.1.100",
        vendor="Test Vendor",
        model="Test Model",
        status="up",
        last_seen=datetime.now(UTC).replace(tzinfo=None)
    )
    session.add(device)
    session.commit()
    
    # Simulate active session in the service
    history_service = get_device_history_service()
    history_service.device_sessions[device_id] = {
        "session_start": datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours),
        "ip": "192.168.1.100",
        "status": "up"
    }
    
    session.close()


@given('device history contains events for "{device_id}"')
def step_device_history_contains_events(device_id):
    """Create device history events"""
    session = get_session()
    
    # Create some sample events
    events = [
        DeviceHistory(
            device_id=device_id,
            event_type="online",
            new_status="up",
            new_ip="192.168.1.100",
            event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
        ),
        DeviceHistory(
            device_id=device_id,
            event_type="offline",
            previous_status="up",
            previous_ip="192.168.1.100",
            duration_seconds=3600,
            event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        )
    ]
    
    for event in events:
        session.add(event)
    session.commit()
    session.close()


@given('device history contains multiple sessions for "{device_id}"')
def step_device_history_multiple_sessions(device_id):
    """Create multiple session events"""
    session = get_session()
    
    # Create multiple online/offline cycles
    events = []
    for i in range(3):
        events.extend([
            DeviceHistory(
                device_id=device_id,
                event_type="online",
                new_status="up",
                new_ip="192.168.1.100",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=6-i*2)
            ),
            DeviceHistory(
                device_id=device_id,
                event_type="offline",
                previous_status="up",
                previous_ip="192.168.1.100",
                duration_seconds=3600,  # 1 hour sessions
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=5-i*2)
            )
        ])
    
    for event in events:
        session.add(event)
    session.commit()
    session.close()


@given('device history contains various event types for "{device_id}"')
def step_device_history_various_events(device_id):
    """Create various event types"""
    session = get_session()
    
    events = [
        DeviceHistory(
            device_id=device_id,
            event_type="online",
            new_status="up",
            new_ip="192.168.1.100",
            event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=3)
        ),
        DeviceHistory(
            device_id=device_id,
            event_type="offline",
            previous_status="up",
            previous_ip="192.168.1.100",
            duration_seconds=1800,
            event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
        ),
        DeviceHistory(
            device_id=device_id,
            event_type="ip_change",
            previous_ip="192.168.1.100",
            new_ip="192.168.1.101",
            event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        )
    ]
    
    for event in events:
        session.add(event)
    session.commit()
    session.close()


@given('device history contains recent events for multiple devices')
def step_device_history_multiple_devices():
    """Create events for multiple devices"""
    session = get_session()
    
    devices = ["device-1", "device-2", "device-3"]
    events = []
    
    for device_id in devices:
        events.extend([
            DeviceHistory(
                device_id=device_id,
                event_type="online",
                new_status="up",
                new_ip=f"192.168.1.{100 + int(device_id.split('-')[1])}",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
            ),
            DeviceHistory(
                device_id=device_id,
                event_type="offline",
                previous_status="up",
                previous_ip=f"192.168.1.{100 + int(device_id.split('-')[1])}",
                duration_seconds=1800,
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=30)
            )
        ])
    
    for event in events:
        session.add(event)
    session.commit()
    session.close()


@given('device history contains events for multiple devices')
def step_device_history_events_multiple_devices():
    """Create events for multiple devices over time"""
    session = get_session()
    
    devices = ["device-1", "device-2", "device-3"]
    events = []
    
    for device_id in devices:
        # Create events over the last 7 days
        for i in range(7):
            events.append(DeviceHistory(
                device_id=device_id,
                event_type="online",
                new_status="up",
                new_ip=f"192.168.1.{100 + int(device_id.split('-')[1])}",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=i)
            ))
    
    for event in events:
        session.add(event)
    session.commit()
    session.close()


# When steps
@when('discovery finds a new device "{device_id}" with IP "{ip_address}"')
def step_discovery_finds_new_device(device_id, ip_address):
    """Simulate discovery finding a new device"""
    session = get_session()
    
    discovered_devices = [{
        "id": device_id,
        "mgmtIp": ip_address,
        "vendor": "Test Vendor",
        "model": "Test Model",
        "hostname": f"Device {device_id}",
        "status": "up"
    }]
    
    existing_devices = []
    
    history_service = get_device_history_service()
    history_service.process_device_discovery(
        db=session,
        discovered_devices=discovered_devices,
        existing_devices=existing_devices
    )
    
    session.commit()
    session.close()


@when('discovery runs and does not find "{device_id}"')
def step_discovery_does_not_find_device(device_id):
    """Simulate discovery not finding a device"""
    session = get_session()
    
    # Get existing device
    existing_device = session.query(Device).filter(Device.id == device_id).first()
    existing_devices = [existing_device] if existing_device else []
    
    discovered_devices = []  # No devices found
    
    history_service = get_device_history_service()
    history_service.process_device_discovery(
        db=session,
        discovered_devices=discovered_devices,
        existing_devices=existing_devices
    )
    
    session.commit()
    session.close()


@when('discovery finds "{device_id}" with new IP "{new_ip}"')
def step_discovery_finds_device_new_ip(device_id, new_ip):
    """Simulate discovery finding device with new IP"""
    session = get_session()
    
    # Get existing device
    existing_device = session.query(Device).filter(Device.id == device_id).first()
    existing_devices = [existing_device] if existing_device else []
    
    discovered_devices = [{
        "id": device_id,
        "mgmtIp": new_ip,
        "vendor": existing_device.vendor,
        "model": existing_device.model,
        "hostname": existing_device.hostname,
        "status": existing_device.status
    }]
    
    history_service = get_device_history_service()
    history_service.process_device_discovery(
        db=session,
        discovered_devices=discovered_devices,
        existing_devices=existing_devices
    )
    
    session.commit()
    session.close()


@when('discovery finds "{device_id}" with status "{new_status}"')
def step_discovery_finds_device_new_status(device_id, new_status):
    """Simulate discovery finding device with new status"""
    session = get_session()
    
    # Get existing device
    existing_device = session.query(Device).filter(Device.id == device_id).first()
    existing_devices = [existing_device] if existing_device else []
    
    discovered_devices = [{
        "id": device_id,
        "mgmtIp": existing_device.mgmt_ip,
        "vendor": existing_device.vendor,
        "model": existing_device.model,
        "hostname": existing_device.hostname,
        "status": new_status
    }]
    
    history_service = get_device_history_service()
    history_service.process_device_discovery(
        db=session,
        discovered_devices=discovered_devices,
        existing_devices=existing_devices
    )
    
    session.commit()
    session.close()


@when('the device goes offline')
def step_device_goes_offline():
    """Simulate device going offline"""
    session = get_session()
    
    # Find a device with active session
    history_service = get_device_history_service()
    device_id = None
    for did in history_service.device_sessions:
        device_id = did
        break
    
    if device_id:
        existing_device = session.query(Device).filter(Device.id == device_id).first()
        existing_devices = [existing_device] if existing_device else []
        
        discovered_devices = []  # Device not found
        
        history_service.process_device_discovery(
            db=session,
            discovered_devices=discovered_devices,
            existing_devices=existing_devices
        )
    
    session.commit()
    session.close()


@when('I request device history for "{device_id}"')
def step_request_device_history(device_id):
    """Request device history via API"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get(f"/device-history/devices/{device_id}/history")
    
    # Store response for later assertions
    pytest.device_history_response = response


@when('I request session statistics for "{device_id}"')
def step_request_session_stats(device_id):
    """Request session statistics via API"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get(f"/device-history/devices/{device_id}/history/stats")
    
    # Store response for later assertions
    pytest.session_stats_response = response


@when('I request device history filtered by event_type "{event_type}"')
def step_request_filtered_history(device_id, event_type):
    """Request filtered device history"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get(f"/device-history/devices/{device_id}/history?event_type={event_type}")
    
    # Store response for later assertions
    pytest.filtered_history_response = response


@when('I request recent events for the last {hours:d} hours')
def step_request_recent_events(hours):
    """Request recent events"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get(f"/device-history/history/recent?hours_back={hours}")
    
    # Store response for later assertions
    pytest.recent_events_response = response


@when('I request history summary for the last {days:d} days')
def step_request_history_summary(days):
    """Request history summary"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get(f"/device-history/history/summary?days_back={days}")
    
    # Store response for later assertions
    pytest.history_summary_response = response


# Then steps
@then('device history should contain an "{event_type}" event for "{device_id}"')
def step_device_history_contains_event(event_type, device_id):
    """Check that device history contains specific event"""
    session = get_session()
    
    event = session.query(DeviceHistory).filter(
        DeviceHistory.device_id == device_id,
        DeviceHistory.event_type == event_type
    ).first()
    
    assert event is not None, f"No {event_type} event found for {device_id}"
    session.close()


@then('the event should have new_ip "{ip_address}"')
def step_event_has_new_ip(ip_address):
    """Check event has specific new IP"""
    session = get_session()
    
    event = session.query(DeviceHistory).filter(
        DeviceHistory.new_ip == ip_address
    ).first()
    
    assert event is not None, f"No event found with new_ip {ip_address}"
    assert event.new_ip == ip_address
    session.close()


@then('the event should have new_status "{status}"')
def step_event_has_new_status(status):
    """Check event has specific new status"""
    session = get_session()
    
    event = session.query(DeviceHistory).filter(
        DeviceHistory.new_status == status
    ).first()
    
    assert event is not None, f"No event found with new_status {status}"
    assert event.new_status == status
    session.close()


@then('the event should have previous_status "{status}"')
def step_event_has_previous_status(status):
    """Check event has specific previous status"""
    session = get_session()
    
    event = session.query(DeviceHistory).filter(
        DeviceHistory.previous_status == status
    ).first()
    
    assert event is not None, f"No event found with previous_status {status}"
    assert event.previous_status == status
    session.close()


@then('the event should have previous_ip "{ip_address}"')
def step_event_has_previous_ip(ip_address):
    """Check event has specific previous IP"""
    session = get_session()
    
    event = session.query(DeviceHistory).filter(
        DeviceHistory.previous_ip == ip_address
    ).first()
    
    assert event is not None, f"No event found with previous_ip {ip_address}"
    assert event.previous_ip == ip_address
    session.close()


@then('the event should have duration_seconds approximately {seconds:d}')
def step_event_has_duration(seconds):
    """Check event has approximate duration"""
    session = get_session()
    
    # Allow for some tolerance in duration calculation
    tolerance = 60  # 1 minute tolerance
    event = session.query(DeviceHistory).filter(
        DeviceHistory.duration_seconds >= seconds - tolerance,
        DeviceHistory.duration_seconds <= seconds + tolerance
    ).first()
    
    assert event is not None, f"No event found with duration approximately {seconds} seconds"
    session.close()


@then('the API should return the device history events')
def step_api_returns_device_history():
    """Check API returns device history"""
    response = pytest.device_history_response
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@then('events should be ordered by timestamp descending')
def step_events_ordered_by_timestamp():
    """Check events are ordered by timestamp"""
    response = pytest.device_history_response
    data = response.json()
    
    if len(data) > 1:
        for i in range(len(data) - 1):
            current_time = datetime.fromisoformat(data[i]['event_timestamp'].replace('Z', '+00:00'))
            next_time = datetime.fromisoformat(data[i + 1]['event_timestamp'].replace('Z', '+00:00'))
            assert current_time >= next_time, "Events are not ordered by timestamp descending"


@then('the API should return total sessions count')
def step_api_returns_total_sessions():
    """Check API returns total sessions"""
    response = pytest.session_stats_response
    assert response.status_code == 200
    
    data = response.json()
    assert 'total_sessions' in data
    assert isinstance(data['total_sessions'], int)


@then('the API should return total online time')
def step_api_returns_total_online_time():
    """Check API returns total online time"""
    response = pytest.session_stats_response
    data = response.json()
    assert 'total_online_time_seconds' in data
    assert isinstance(data['total_online_time_seconds'], int)


@then('the API should return average session duration')
def step_api_returns_avg_session_duration():
    """Check API returns average session duration"""
    response = pytest.session_stats_response
    data = response.json()
    assert 'avg_session_duration_seconds' in data
    assert isinstance(data['avg_session_duration_seconds'], (int, float))


@then('the API should return only "{event_type}" events')
def step_api_returns_only_event_type(event_type):
    """Check API returns only specific event type"""
    response = pytest.filtered_history_response
    assert response.status_code == 200
    
    data = response.json()
    for event in data:
        assert event['event_type'] == event_type


@then('the API should return events from the last {hours:d} hours')
def step_api_returns_recent_events(hours):
    """Check API returns recent events"""
    response = pytest.recent_events_response
    assert response.status_code == 200
    
    data = response.json()
    cutoff_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours)
    
    for event in data:
        event_time = datetime.fromisoformat(event['event_timestamp'].replace('Z', '+00:00'))
        assert event_time >= cutoff_time, f"Event {event['id']} is older than {hours} hours"


@then('the API should return total events count')
def step_api_returns_total_events():
    """Check API returns total events count"""
    response = pytest.history_summary_response
    assert response.status_code == 200
    
    data = response.json()
    assert 'total_events' in data
    assert isinstance(data['total_events'], int)


@then('the API should return unique devices count')
def step_api_returns_unique_devices():
    """Check API returns unique devices count"""
    response = pytest.history_summary_response
    data = response.json()
    assert 'unique_devices_with_events' in data
    assert isinstance(data['unique_devices_with_events'], int)


@then('the API should return events by type breakdown')
def step_api_returns_events_by_type():
    """Check API returns events by type breakdown"""
    response = pytest.history_summary_response
    data = response.json()
    assert 'events_by_type' in data
    assert isinstance(data['events_by_type'], dict)


@then('the API should return most active devices list')
def step_api_returns_most_active_devices():
    """Check API returns most active devices list"""
    response = pytest.history_summary_response
    data = response.json()
    assert 'most_active_devices' in data
    assert isinstance(data['most_active_devices'], list)
