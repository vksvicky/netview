import pytest
from datetime import datetime, timedelta, UTC
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
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


@pytest.fixture
def sample_device():
    """Create a sample device for testing"""
    session = SessionLocal()
    device = Device(
        id="test-device-1",
        hostname="Test Device",
        mgmt_ip="192.168.1.100",
        vendor="Test Vendor",
        model="Test Model",
        status="up",
        last_seen=datetime.now(UTC).replace(tzinfo=None)
    )
    session.add(device)
    session.commit()
    session.refresh(device)
    yield device
    session.close()


@pytest.fixture
def sample_devices():
    """Create multiple sample devices for testing"""
    session = SessionLocal()
    devices = []
    
    for i in range(3):
        device = Device(
            id=f"test-device-{i+1}",
            hostname=f"Test Device {i+1}",
            mgmt_ip=f"192.168.1.{100+i}",
            vendor=f"Vendor {i+1}",
            model=f"Model {i+1}",
            status="up",
            last_seen=datetime.now(UTC).replace(tzinfo=None)
        )
        session.add(device)
        devices.append(device)
    
    session.commit()
    for device in devices:
        session.refresh(device)
    yield devices
    session.close()


class TestDeviceHistoryService:
    """Test the DeviceHistoryService class"""
    
    @pytest.mark.asyncio
    async def test_track_device_event_online(self, sample_device):
        """Test tracking an online event"""
        session = SessionLocal()
        
        history = await device_history_service.track_device_event(
            db=session,
            device_id=sample_device.id,
            event_type="online",
            new_status="up",
            new_ip="192.168.1.100",
            event_metadata={"vendor": "Test Vendor"}
        )
        
        session.commit()
        
        assert history.device_id == sample_device.id
        assert history.event_type == "online"
        assert history.new_status == "up"
        assert history.new_ip == "192.168.1.100"
        assert history.event_metadata == {"vendor": "Test Vendor"}
        assert history.duration_seconds is None
        
        session.close()
    
    @pytest.mark.asyncio
    async def test_track_device_event_offline_with_duration(self, sample_device):
        """Test tracking an offline event with session duration"""
        session = SessionLocal()
        
        # Simulate an active session
        device_history_service.device_sessions[sample_device.id] = {
            "session_start": datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=30),
            "ip": "192.168.1.100",
            "status": "up"
        }
        
        history = await device_history_service.track_device_event(
            db=session,
            device_id=sample_device.id,
            event_type="offline",
            previous_status="up",
            previous_ip="192.168.1.100"
        )
        
        session.commit()
        
        assert history.device_id == sample_device.id
        assert history.event_type == "offline"
        assert history.previous_status == "up"
        assert history.previous_ip == "192.168.1.100"
        assert history.duration_seconds is not None
        assert history.duration_seconds >= 1800  # At least 30 minutes
        
        # Session should be removed
        assert sample_device.id not in device_history_service.device_sessions
        
        session.close()
    
    @pytest.mark.asyncio
    async def test_track_device_event_ip_change(self, sample_device):
        """Test tracking an IP change event"""
        session = SessionLocal()
        
        history = await device_history_service.track_device_event(
            db=session,
            device_id=sample_device.id,
            event_type="ip_change",
            previous_ip="192.168.1.100",
            new_ip="192.168.1.101"
        )
        
        session.commit()
        
        assert history.device_id == sample_device.id
        assert history.event_type == "ip_change"
        assert history.previous_ip == "192.168.1.100"
        assert history.new_ip == "192.168.1.101"
        
        session.close()
    
    @pytest.mark.asyncio
    async def test_process_device_discovery_new_device(self):
        """Test processing discovery with new devices"""
        session = SessionLocal()
        
        discovered_devices = [
            {
                "id": "new-device-1",
                "mgmtIp": "192.168.1.200",
                "vendor": "New Vendor",
                "model": "New Model",
                "hostname": "New Device",
                "status": "up"
            }
        ]
        
        existing_devices = []
        
        history_events = await device_history_service.process_device_discovery(
            db=session,
            discovered_devices=discovered_devices,
            existing_devices=existing_devices
        )
        
        session.commit()
        
        assert len(history_events) == 1
        assert history_events[0].event_type == "online"
        assert history_events[0].device_id == "new-device-1"
        assert history_events[0].new_ip == "192.168.1.200"
        
        session.close()
    
    @pytest.mark.asyncio
    async def test_process_device_discovery_existing_device_changes(self, sample_device):
        """Test processing discovery with existing device changes"""
        session = SessionLocal()
        
        discovered_devices = [
            {
                "id": sample_device.id,
                "mgmtIp": "192.168.1.101",  # IP changed
                "vendor": sample_device.vendor,
                "model": sample_device.model,
                "hostname": sample_device.hostname,
                "status": "down"  # Status changed
            }
        ]
        
        existing_devices = [sample_device]
        
        history_events = await device_history_service.process_device_discovery(
            db=session,
            discovered_devices=discovered_devices,
            existing_devices=existing_devices
        )
        
        session.commit()
        
        # Should have 2 events: IP change and status change
        assert len(history_events) == 2
        
        ip_change_event = next(e for e in history_events if e.event_type == "ip_change")
        status_change_event = next(e for e in history_events if e.event_type == "status_change")
        
        assert ip_change_event.device_id == sample_device.id
        assert ip_change_event.previous_ip == "192.168.1.100"
        assert ip_change_event.new_ip == "192.168.1.101"
        
        assert status_change_event.device_id == sample_device.id
        assert status_change_event.previous_status == "up"
        assert status_change_event.new_status == "down"
        
        session.close()
    
    @pytest.mark.asyncio
    async def test_process_device_discovery_device_offline(self, sample_device):
        """Test processing discovery when device goes offline"""
        session = SessionLocal()
        
        discovered_devices = []  # No devices discovered
        existing_devices = [sample_device]
        
        history_events = await device_history_service.process_device_discovery(
            db=session,
            discovered_devices=discovered_devices,
            existing_devices=existing_devices
        )
        
        session.commit()
        
        assert len(history_events) == 1
        assert history_events[0].event_type == "offline"
        assert history_events[0].device_id == sample_device.id
        assert history_events[0].previous_status == "up"
        
        session.close()
    
    def test_get_device_history(self, sample_device):
        """Test retrieving device history"""
        session = SessionLocal()
        
        # Create some history events
        events = []
        for i in range(5):
            event = DeviceHistory(
                device_id=sample_device.id,
                event_type="online" if i % 2 == 0 else "offline",
                new_status="up" if i % 2 == 0 else "down",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=i),
                duration_seconds=1800 if i % 2 == 1 else None
            )
            session.add(event)
            events.append(event)
        
        session.commit()
        
        # Test getting history
        history = device_history_service.get_device_history(
            db=session,
            device_id=sample_device.id,
            limit=10
        )
        
        assert len(history) == 5
        # Should be ordered by timestamp descending
        assert history[0].event_timestamp > history[1].event_timestamp
        
        session.close()
    
    def test_get_device_history_with_filters(self, sample_device):
        """Test retrieving device history with filters"""
        session = SessionLocal()
        
        # Create different types of events
        events = [
            DeviceHistory(
                device_id=sample_device.id,
                event_type="online",
                new_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="offline",
                previous_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="ip_change",
                previous_ip="192.168.1.100",
                new_ip="192.168.1.101",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=3)
            )
        ]
        
        for event in events:
            session.add(event)
        session.commit()
        
        # Test filtering by event type
        online_events = device_history_service.get_device_history(
            db=session,
            device_id=sample_device.id,
            event_type="online"
        )
        
        assert len(online_events) == 1
        assert online_events[0].event_type == "online"
        
        session.close()
    
    def test_get_device_session_stats(self, sample_device):
        """Test getting device session statistics"""
        session = SessionLocal()
        
        # Create session events
        events = [
            DeviceHistory(
                device_id=sample_device.id,
                event_type="online",
                new_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="offline",
                previous_status="up",
                duration_seconds=3600,  # 1 hour session
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=23)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="online",
                new_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=12)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="offline",
                previous_status="up",
                duration_seconds=7200,  # 2 hour session
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=10)
            )
        ]
        
        for event in events:
            session.add(event)
        session.commit()
        
        stats = device_history_service.get_device_session_stats(
            db=session,
            device_id=sample_device.id,
            days_back=30
        )
        
        assert stats["total_sessions"] == 2
        assert stats["total_online_time_seconds"] == 10800  # 3 hours total
        assert stats["avg_session_duration_seconds"] == 5400  # 1.5 hours average
        
        session.close()


class TestDeviceHistoryAPI:
    """Test the Device History API endpoints"""
    
    def test_get_device_history_endpoint_empty(self):
        """Test getting device history when none exists"""
        client = TestClient(app)
        resp = client.get("/device-history/devices/nonexistent/history")
        assert resp.status_code == 200
        assert resp.json() == []
    
    def test_get_device_history_endpoint_with_data(self, sample_device):
        """Test getting device history with existing data"""
        session = SessionLocal()
        
        # Create history events
        events = [
            DeviceHistory(
                device_id=sample_device.id,
                event_type="online",
                new_status="up",
                new_ip="192.168.1.100",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="offline",
                previous_status="up",
                previous_ip="192.168.1.100",
                duration_seconds=1800,
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
            )
        ]
        
        for event in events:
            session.add(event)
        session.commit()
        session.close()
        
        client = TestClient(app)
        resp = client.get(f"/device-history/devices/{sample_device.id}/history")
        
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        
        # Check first event (most recent)
        assert data[0]["event_type"] == "online"
        assert data[0]["device_id"] == sample_device.id
        assert data[0]["new_status"] == "up"
        assert data[0]["new_ip"] == "192.168.1.100"
        
        # Check second event
        assert data[1]["event_type"] == "offline"
        assert data[1]["duration_seconds"] == 1800
    
    def test_get_device_history_with_parameters(self, sample_device):
        """Test getting device history with query parameters"""
        session = SessionLocal()
        
        # Create events with different types
        events = [
            DeviceHistory(
                device_id=sample_device.id,
                event_type="online",
                new_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="offline",
                previous_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="ip_change",
                previous_ip="192.168.1.100",
                new_ip="192.168.1.101",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=3)
            )
        ]
        
        for event in events:
            session.add(event)
        session.commit()
        session.close()
        
        client = TestClient(app)
        
        # Test filtering by event type
        resp = client.get(f"/device-history/devices/{sample_device.id}/history?event_type=online")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["event_type"] == "online"
        
        # Test limiting results
        resp = client.get(f"/device-history/devices/{sample_device.id}/history?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
    
    def test_get_device_session_stats_endpoint(self, sample_device):
        """Test getting device session statistics"""
        session = SessionLocal()
        
        # Create session events
        events = [
            DeviceHistory(
                device_id=sample_device.id,
                event_type="online",
                new_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
            ),
            DeviceHistory(
                device_id=sample_device.id,
                event_type="offline",
                previous_status="up",
                duration_seconds=3600,
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=23)
            )
        ]
        
        for event in events:
            session.add(event)
        session.commit()
        session.close()
        
        client = TestClient(app)
        resp = client.get(f"/device-history/devices/{sample_device.id}/history/stats")
        
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sessions" in data
        assert "total_online_time_seconds" in data
        assert "avg_session_duration_seconds" in data
        assert data["total_sessions"] == 1
        assert data["total_online_time_seconds"] == 3600
    
    def test_get_all_device_history_endpoint(self, sample_devices):
        """Test getting all device history"""
        session = SessionLocal()
        
        # Create history events for multiple devices
        for i, device in enumerate(sample_devices):
            event = DeviceHistory(
                device_id=device.id,
                event_type="online",
                new_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=i)
            )
            session.add(event)
        
        session.commit()
        session.close()
        
        client = TestClient(app)
        resp = client.get("/device-history/history")
        
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        
        # Should be ordered by timestamp descending
        assert data[0]["event_timestamp"] > data[1]["event_timestamp"]
    
    def test_get_recent_events_endpoint(self, sample_devices):
        """Test getting recent events"""
        session = SessionLocal()
        
        # Create recent events
        recent_event = DeviceHistory(
            device_id=sample_devices[0].id,
            event_type="online",
            new_status="up",
            event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        )
        
        # Create old event (should be filtered out)
        old_event = DeviceHistory(
            device_id=sample_devices[1].id,
            event_type="offline",
            previous_status="up",
            event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=25)
        )
        
        session.add(recent_event)
        session.add(old_event)
        session.commit()
        session.close()
        
        client = TestClient(app)
        resp = client.get("/device-history/history/recent?hours_back=24")
        
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["event_type"] == "online"
    
    def test_get_history_summary_endpoint(self, sample_devices):
        """Test getting history summary"""
        session = SessionLocal()
        
        # Create various events
        events = [
            DeviceHistory(
                device_id=sample_devices[0].id,
                event_type="online",
                new_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
            ),
            DeviceHistory(
                device_id=sample_devices[1].id,
                event_type="offline",
                previous_status="up",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
            ),
            DeviceHistory(
                device_id=sample_devices[0].id,
                event_type="ip_change",
                previous_ip="192.168.1.100",
                new_ip="192.168.1.101",
                event_timestamp=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=3)
            )
        ]
        
        for event in events:
            session.add(event)
        session.commit()
        session.close()
        
        client = TestClient(app)
        resp = client.get("/device-history/history/summary?days_back=7")
        
        assert resp.status_code == 200
        data = resp.json()
        assert "total_events" in data
        assert "unique_devices_with_events" in data
        assert "events_by_type" in data
        assert "most_active_devices" in data
        
        assert data["total_events"] == 3
        assert data["unique_devices_with_events"] == 2
        assert data["events_by_type"]["online"] == 1
        assert data["events_by_type"]["offline"] == 1
        assert data["events_by_type"]["ip_change"] == 1


class TestDeviceHistoryIntegration:
    """Integration tests for device history with discovery service"""
    
    @pytest.mark.asyncio
    async def test_discovery_service_tracks_history(self):
        """Test that discovery service automatically tracks device history"""
        session = SessionLocal()
        
        # Mock discovered devices
        discovered_devices = [
            {
                "id": "integration-test-device",
                "mgmtIp": "192.168.1.200",
                "vendor": "Integration Vendor",
                "model": "Integration Model",
                "hostname": "Integration Device",
                "status": "up"
            }
        ]
        
        existing_devices = []
        
        # Process discovery
        history_events = await device_history_service.process_device_discovery(
            db=session,
            discovered_devices=discovered_devices,
            existing_devices=existing_devices
        )
        
        session.commit()
        
        # Verify history was created
        assert len(history_events) == 1
        assert history_events[0].event_type == "online"
        assert history_events[0].device_id == "integration-test-device"
        
        # Verify it's in the database
        db_history = session.query(DeviceHistory).filter(
            DeviceHistory.device_id == "integration-test-device"
        ).first()
        
        assert db_history is not None
        assert db_history.event_type == "online"
        
        session.close()
