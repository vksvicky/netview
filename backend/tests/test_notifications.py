import pytest
from datetime import datetime, timedelta, UTC
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import SessionLocal, Device, Notification
from app.services.notification_service import notification_service


@pytest.fixture(autouse=True)
def clean_database():
    """Clean the database before each test"""
    from app.models import init_db
    init_db()  # Initialize database tables
    session = SessionLocal()
    session.query(Notification).delete()
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
def sample_notifications():
    """Create sample notifications for testing"""
    session = SessionLocal()
    notifications = []
    
    # Create different types of notifications
    for i in range(5):
        notification = Notification(
            notification_type="new_device",
            title=f"Test Notification {i+1}",
            message=f"This is test notification {i+1}",
            device_id="test-device-1",
            severity="info" if i < 3 else "warning",
            is_read=i < 2,  # First 2 are read
            created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=i)
        )
        session.add(notification)
        notifications.append(notification)
    
    session.commit()
    for notification in notifications:
        session.refresh(notification)
    
    yield notifications
    session.close()


class TestNotificationService:
    """Test the NotificationService class"""
    
    def test_create_notification(self):
        """Test creating a notification"""
        session = SessionLocal()
        
        notification = notification_service.create_notification(
            db=session,
            notification_type="new_device",
            device_id="test-device-1",
            title="Test Notification",
            message="This is a test notification",
            severity="info"
        )
        
        assert notification.id is not None
        assert notification.notification_type == "new_device"
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.severity == "info"
        assert notification.device_id == "test-device-1"
        assert notification.is_read == False
        assert notification.is_acknowledged == False
        
        session.close()
    
    def test_create_notification_with_template(self):
        """Test creating a notification using template"""
        session = SessionLocal()
        
        # Create a device first
        device = Device(
            id="test-device-2",
            hostname="Template Device",
            mgmt_ip="192.168.1.101",
            vendor="Template Vendor",
            model="Template Model",
            status="up",
            last_seen=datetime.now(UTC).replace(tzinfo=None)
        )
        session.add(device)
        session.commit()
        
        notification = notification_service.create_notification(
            db=session,
            notification_type="new_device",
            device_id="test-device-2"
        )
        
        assert notification.title == "New Device Detected"
        assert "Template Device" in notification.message
        assert "192.168.1.101" in notification.message
        assert "Template Vendor" in notification.message
        
        session.close()
    
    def test_get_notifications_with_filters(self, sample_notifications):
        """Test getting notifications with various filters"""
        session = SessionLocal()
        
        # Test basic retrieval
        notifications = notification_service.get_notifications(session, limit=10)
        assert len(notifications) == 5
        
        # Test severity filter
        info_notifications = notification_service.get_notifications(
            session, severity="info"
        )
        assert len(info_notifications) == 3
        
        # Test read status filter
        unread_notifications = notification_service.get_notifications(
            session, is_read=False
        )
        assert len(unread_notifications) == 3
        
        # Test notification type filter
        new_device_notifications = notification_service.get_notifications(
            session, notification_type="new_device"
        )
        assert len(new_device_notifications) == 5
        
        session.close()
    
    def test_get_unread_count(self, sample_notifications):
        """Test getting unread notification count"""
        session = SessionLocal()
        
        count = notification_service.get_unread_count(session)
        assert count == 3  # 3 unread notifications
        
        session.close()
    
    def test_mark_as_read(self, sample_notifications):
        """Test marking a notification as read"""
        session = SessionLocal()
        
        notification_id = sample_notifications[0].id
        success = notification_service.mark_as_read(session, notification_id)
        
        assert success == True
        
        # Verify the notification is marked as read
        notification = session.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        assert notification.is_read == True
        
        session.close()
    
    def test_mark_all_as_read(self, sample_notifications):
        """Test marking all notifications as read"""
        session = SessionLocal()
        
        count = notification_service.mark_all_as_read(session)
        assert count == 3  # 3 notifications were marked as read
        
        # Verify all notifications are marked as read
        unread_count = notification_service.get_unread_count(session)
        assert unread_count == 0
        
        session.close()
    
    def test_acknowledge_notification(self, sample_notifications):
        """Test acknowledging a notification"""
        session = SessionLocal()
        
        notification_id = sample_notifications[0].id
        success = notification_service.acknowledge_notification(
            session, notification_id, "test_user"
        )
        
        assert success == True
        
        # Verify the notification is acknowledged
        notification = session.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        assert notification.is_acknowledged == True
        assert notification.acknowledged_by == "test_user"
        assert notification.acknowledged_at is not None
        
        session.close()
    
    def test_delete_old_notifications(self):
        """Test deleting old notifications"""
        session = SessionLocal()
        
        # Create old notifications
        old_notification = Notification(
            notification_type="old_event",
            title="Old Notification",
            message="This is an old notification",
            created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=35)
        )
        session.add(old_notification)
        
        # Create recent notification
        recent_notification = Notification(
            notification_type="recent_event",
            title="Recent Notification",
            message="This is a recent notification",
            created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=5)
        )
        session.add(recent_notification)
        session.commit()
        
        # Delete notifications older than 30 days
        count = notification_service.delete_old_notifications(session, days_old=30)
        assert count == 1
        
        # Verify only recent notification remains
        remaining = session.query(Notification).all()
        assert len(remaining) == 1
        assert remaining[0].notification_type == "recent_event"
        
        session.close()
    
    def test_get_notification_stats(self, sample_notifications):
        """Test getting notification statistics"""
        session = SessionLocal()
        
        stats = notification_service.get_notification_stats(session, days_back=7)
        
        assert stats['total_notifications'] == 5
        assert stats['unread_notifications'] == 3
        assert stats['by_type']['new_device'] == 5
        assert stats['by_severity']['info'] == 3
        assert stats['by_severity']['warning'] == 2
        assert stats['period_days'] == 7
        
        session.close()
    
    def test_process_device_event(self, sample_device):
        """Test processing device events"""
        session = SessionLocal()
        
        # Test online event
        notification = notification_service.process_device_event(
            session, 
            sample_device.id, 
            "online",
            {"new_status": "up", "new_ip": "192.168.1.100"}
        )
        
        assert notification is not None
        assert notification.notification_type == "device_online"
        assert notification.device_id == sample_device.id
        
        # Test offline event
        notification = notification_service.process_device_event(
            session, 
            sample_device.id, 
            "offline",
            {"previous_status": "up", "previous_ip": "192.168.1.100"}
        )
        
        assert notification is not None
        assert notification.notification_type == "device_offline"
        
        # Test IP change event
        notification = notification_service.process_device_event(
            session, 
            sample_device.id, 
            "ip_change",
            {"previous_ip": "192.168.1.100", "new_ip": "192.168.1.101"}
        )
        
        assert notification is not None
        assert notification.notification_type == "device_ip_change"
        
        session.close()
    
    def test_process_new_device(self):
        """Test processing new device detection"""
        session = SessionLocal()
        
        device_data = {
            "hostname": "New Device",
            "mgmt_ip": "192.168.1.102",
            "vendor": "New Vendor",
            "model": "New Model"
        }
        
        notification = notification_service.process_new_device(
            session, "new-device-1", device_data
        )
        
        assert notification.notification_type == "new_device"
        assert notification.device_id == "new-device-1"
        assert "New Device" in notification.message
        assert "192.168.1.102" in notification.message
        assert "New Vendor" in notification.message
        
        session.close()
    
    def test_process_unknown_device(self):
        """Test processing unknown device detection"""
        session = SessionLocal()
        
        device_data = {
            "hostname": None,  # Unknown hostname
            "mgmt_ip": "192.168.1.103",
            "vendor": "Unknown",  # Unknown vendor
            "model": "Unknown"
        }
        
        notification = notification_service.process_new_device(
            session, "unknown-device-1", device_data
        )
        
        assert notification.notification_type == "unknown_device"
        assert notification.device_id == "unknown-device-1"
        assert "Unknown" in notification.message
        assert notification.severity == "warning"
        
        session.close()


class TestNotificationAPI:
    """Test the notification API endpoints"""
    
    def test_get_notifications_endpoint_empty(self):
        """Test getting notifications when none exist"""
        client = TestClient(app)
        response = client.get("/notifications")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_notifications_endpoint_with_data(self, sample_notifications):
        """Test getting notifications with data"""
        client = TestClient(app)
        response = client.get("/notifications")
        
        assert response.status_code == 200
        notifications = response.json()
        assert len(notifications) == 5
        
        # Check structure of first notification
        first_notification = notifications[0]
        assert "id" in first_notification
        assert "notification_type" in first_notification
        assert "title" in first_notification
        assert "message" in first_notification
        assert "severity" in first_notification
        assert "is_read" in first_notification
        assert "created_at" in first_notification
    
    def test_get_notifications_with_parameters(self, sample_notifications):
        """Test getting notifications with query parameters"""
        client = TestClient(app)
        
        # Test with limit
        response = client.get("/notifications?limit=3")
        assert response.status_code == 200
        assert len(response.json()) == 3
        
        # Test with severity filter
        response = client.get("/notifications?severity=info")
        assert response.status_code == 200
        notifications = response.json()
        assert all(n["severity"] == "info" for n in notifications)
        
        # Test with read status filter
        response = client.get("/notifications?is_read=false")
        assert response.status_code == 200
        notifications = response.json()
        assert all(n["is_read"] == False for n in notifications)
    
    def test_get_unread_count_endpoint(self, sample_notifications):
        """Test getting unread count endpoint"""
        client = TestClient(app)
        response = client.get("/notifications/unread-count")
        
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 3
    
    def test_mark_notification_as_read_endpoint(self, sample_notifications):
        """Test marking notification as read endpoint"""
        client = TestClient(app)
        
        notification_id = sample_notifications[0].id
        response = client.put(f"/notifications/{notification_id}/read")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["message"] == "Notification marked as read"
    
    def test_mark_notification_as_read_not_found(self):
        """Test marking non-existent notification as read"""
        client = TestClient(app)
        response = client.put("/notifications/99999/read")
        
        assert response.status_code == 404
        assert "Notification not found" in response.json()["detail"]
    
    def test_mark_all_notifications_as_read_endpoint(self, sample_notifications):
        """Test marking all notifications as read endpoint"""
        client = TestClient(app)
        response = client.put("/notifications/mark-all-read")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["count"] == 3
        assert "Marked 3 notifications as read" in data["message"]
    
    def test_acknowledge_notification_endpoint(self, sample_notifications):
        """Test acknowledging notification endpoint"""
        client = TestClient(app)
        
        notification_id = sample_notifications[0].id
        response = client.put(f"/notifications/{notification_id}/acknowledge?acknowledged_by=test_user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["message"] == "Notification acknowledged"
    
    def test_get_notification_stats_endpoint(self, sample_notifications):
        """Test getting notification stats endpoint"""
        client = TestClient(app)
        response = client.get("/notifications/stats")
        
        assert response.status_code == 200
        stats = response.json()
        
        assert stats["total_notifications"] == 5
        assert stats["unread_notifications"] == 3
        assert stats["by_type"]["new_device"] == 5
        assert stats["by_severity"]["info"] == 3
        assert stats["by_severity"]["warning"] == 2
        assert stats["period_days"] == 7
    
    def test_create_test_notification_endpoint(self):
        """Test creating test notification endpoint"""
        client = TestClient(app)
        response = client.post("/notifications/test?notification_type=info&title=Test&message=Test%20message&severity=info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "notification" in data
        assert data["notification"]["title"] == "Test"
        assert data["notification"]["message"] == "Test message"
        assert data["notification"]["severity"] == "info"
    
    def test_cleanup_old_notifications_endpoint(self):
        """Test cleanup old notifications endpoint"""
        client = TestClient(app)
        
        # First create some old notifications
        session = SessionLocal()
        old_notification = Notification(
            notification_type="old_event",
            title="Old Notification",
            message="This is an old notification",
            created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=35)
        )
        session.add(old_notification)
        session.commit()
        session.close()
        
        # Now test cleanup
        response = client.delete("/notifications/cleanup?days_old=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["count"] == 1
        assert "Deleted 1 old notifications" in data["message"]


class TestNotificationIntegration:
    """Test notification integration with other services"""
    
    def test_notification_creation_on_device_discovery(self):
        """Test that notifications are created during device discovery"""
        # This would require mocking the discovery service
        # For now, we'll test the integration points
        
        session = SessionLocal()
        
        # Simulate device discovery creating a notification
        notification = notification_service.process_new_device(
            session,
            "discovered-device-1",
            {
                "hostname": "Discovered Device",
                "mgmt_ip": "192.168.1.104",
                "vendor": "Discovery Vendor",
                "model": "Discovery Model"
            }
        )
        
        assert notification is not None
        assert notification.notification_type == "new_device"
        assert notification.device_id == "discovered-device-1"
        
        session.close()
    
    def test_notification_creation_on_device_status_change(self, sample_device):
        """Test that notifications are created on device status changes"""
        session = SessionLocal()
        
        # Simulate device going offline
        notification = notification_service.process_device_event(
            session,
            sample_device.id,
            "offline",
            {"previous_status": "up", "previous_ip": sample_device.mgmt_ip}
        )
        
        assert notification is not None
        assert notification.notification_type == "device_offline"
        assert notification.device_id == sample_device.id
        
        session.close()
