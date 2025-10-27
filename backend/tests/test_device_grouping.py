import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models import Device, init_db
from app.db import get_db
import json

client = TestClient(app)

@pytest.fixture
def clean_database():
    """Clean database before each test"""
    from app.models import init_db
    from app.db import SessionLocal
    init_db()
    
    # Clear all devices
    db = SessionLocal()
    try:
        db.query(Device).delete()
        db.commit()
    finally:
        db.close()
    
    yield
    
    # Clean up after test
    db = SessionLocal()
    try:
        db.query(Device).delete()
        db.commit()
    finally:
        db.close()

class TestDeviceGroupingAPI:
    """Test device grouping API endpoints"""

    def test_get_grouped_devices_by_vendor(self, clean_database):
        """Test grouping devices by vendor"""
        # Create test devices
        devices_data = [
            {"id": "dev1", "hostname": "router1", "mgmt_ip": "192.168.1.1", "vendor": "Cisco", "model": "ISR4331", "status": "up"},
            {"id": "dev2", "hostname": "switch1", "mgmt_ip": "192.168.1.2", "vendor": "Cisco", "model": "Catalyst 2960", "status": "up"},
            {"id": "dev3", "hostname": "server1", "mgmt_ip": "192.168.1.3", "vendor": "HP", "model": "ProLiant", "status": "up"},
            {"id": "dev4", "hostname": "unknown1", "mgmt_ip": "192.168.1.4", "vendor": None, "model": None, "status": "down"}
        ]
        
        for device_data in devices_data:
            response = client.post("/devices", json=device_data)
            assert response.status_code == 200

        # Test grouping by vendor
        response = client.get("/devices/grouped?group_by=vendor")
        assert response.status_code == 200
        
        grouped_data = response.json()
        assert "Cisco" in grouped_data
        assert "HP" in grouped_data
        assert "Unknown" in grouped_data
        
        # Check device counts
        assert len(grouped_data["Cisco"]) == 2
        assert len(grouped_data["HP"]) == 1
        assert len(grouped_data["Unknown"]) == 1

    def test_get_grouped_devices_by_status(self, clean_database):
        """Test grouping devices by status"""
        # Create test devices
        devices_data = [
            {"id": "dev1", "hostname": "router1", "mgmt_ip": "192.168.1.1", "vendor": "Cisco", "model": "ISR4331", "status": "up"},
            {"id": "dev2", "hostname": "switch1", "mgmt_ip": "192.168.1.2", "vendor": "Cisco", "model": "Catalyst 2960", "status": "down"},
            {"id": "dev3", "hostname": "server1", "mgmt_ip": "192.168.1.3", "vendor": "HP", "model": "ProLiant", "status": "up"},
            {"id": "dev4", "hostname": "unknown1", "mgmt_ip": "192.168.1.4", "vendor": "Dell", "model": "PowerEdge", "status": "unknown"}
        ]
        
        for device_data in devices_data:
            response = client.post("/devices", json=device_data)
            assert response.status_code == 200

        # Test grouping by status
        response = client.get("/devices/grouped?group_by=status")
        assert response.status_code == 200
        
        grouped_data = response.json()
        assert "up" in grouped_data
        assert "down" in grouped_data
        assert "unknown" in grouped_data
        
        # Check device counts
        assert len(grouped_data["up"]) == 2
        assert len(grouped_data["down"]) == 1
        assert len(grouped_data["unknown"]) == 1

    def test_get_grouped_devices_by_connection_type(self, clean_database):
        """Test grouping devices by connection type"""
        # Create test devices with different connection types
        devices_data = [
            {"id": "dev1", "hostname": "router1", "mgmt_ip": "192.168.1.1", "vendor": "Cisco", "model": "ISR4331", "status": "up", "connection_type": "SNMP"},
            {"id": "dev2", "hostname": "switch1", "mgmt_ip": "192.168.1.2", "vendor": "Cisco", "model": "Catalyst 2960", "status": "up", "connection_type": "SNMP"},
            {"id": "dev3", "hostname": "server1", "mgmt_ip": "192.168.1.3", "vendor": "HP", "model": "ProLiant", "status": "up", "connection_type": "SSH"},
            {"id": "dev4", "hostname": "unknown1", "mgmt_ip": "192.168.1.4", "vendor": "Dell", "model": "PowerEdge", "status": "up", "connection_type": None}
        ]
        
        for device_data in devices_data:
            response = client.post("/devices", json=device_data)
            assert response.status_code == 200

        # Test grouping by connection type
        response = client.get("/devices/grouped?group_by=connection_type")
        assert response.status_code == 200
        
        grouped_data = response.json()
        assert "SNMP" in grouped_data
        assert "SSH" in grouped_data
        assert "Unknown" in grouped_data
        
        # Check device counts
        assert len(grouped_data["SNMP"]) == 2
        assert len(grouped_data["SSH"]) == 1
        assert len(grouped_data["Unknown"]) == 1

    def test_get_grouped_devices_by_device_type(self, clean_database):
        """Test grouping devices by device type"""
        # Create test devices with different roles
        devices_data = [
            {"id": "dev1", "hostname": "router1", "mgmt_ip": "192.168.1.1", "vendor": "Cisco", "model": "ISR4331", "status": "up", "roles": ["router"]},
            {"id": "dev2", "hostname": "switch1", "mgmt_ip": "192.168.1.2", "vendor": "Cisco", "model": "Catalyst 2960", "status": "up", "roles": ["switch"]},
            {"id": "dev3", "hostname": "server1", "mgmt_ip": "192.168.1.3", "vendor": "HP", "model": "ProLiant", "status": "up", "roles": ["server"]},
            {"id": "dev4", "hostname": "gateway1", "mgmt_ip": "192.168.1.4", "vendor": "Dell", "model": "PowerEdge", "status": "up", "roles": ["gateway"]},
            {"id": "dev5", "hostname": "cisco1", "mgmt_ip": "192.168.1.5", "vendor": "Cisco", "model": "ASA", "status": "up", "roles": []},
            {"id": "dev6", "hostname": "hp1", "mgmt_ip": "192.168.1.6", "vendor": "HP", "model": "Aruba", "status": "up", "roles": []},
            {"id": "dev7", "hostname": "dell1", "mgmt_ip": "192.168.1.7", "vendor": "Dell", "model": "PowerEdge", "status": "up", "roles": []},
            {"id": "dev8", "hostname": "other1", "mgmt_ip": "192.168.1.8", "vendor": "Other", "model": "Unknown", "status": "up", "roles": []}
        ]
        
        for device_data in devices_data:
            response = client.post("/devices", json=device_data)
            assert response.status_code == 200

        # Test grouping by device type
        response = client.get("/devices/grouped?group_by=device_type")
        assert response.status_code == 200
        
        grouped_data = response.json()
        
        # Check that device types are correctly categorized
        assert "Router/Gateway" in grouped_data
        assert "Switch" in grouped_data
        assert "Server" in grouped_data
        assert "Cisco Device" in grouped_data
        assert "HP Device" in grouped_data
        assert "Dell Device" in grouped_data
        assert "Other Device" in grouped_data
        
        # Check device counts
        assert len(grouped_data["Router/Gateway"]) == 2  # router + gateway
        assert len(grouped_data["Switch"]) == 1
        assert len(grouped_data["Server"]) == 1
        assert len(grouped_data["Cisco Device"]) == 1  # cisco device without specific role
        assert len(grouped_data["HP Device"]) == 1
        assert len(grouped_data["Dell Device"]) == 1
        assert len(grouped_data["Other Device"]) == 1

    def test_get_grouping_stats(self, clean_database):
        """Test getting grouping statistics"""
        # Create test devices
        devices_data = [
            {"id": "dev1", "hostname": "router1", "mgmt_ip": "192.168.1.1", "vendor": "Cisco", "model": "ISR4331", "status": "up", "connection_type": "SNMP", "roles": ["router"]},
            {"id": "dev2", "hostname": "switch1", "mgmt_ip": "192.168.1.2", "vendor": "Cisco", "model": "Catalyst 2960", "status": "down", "connection_type": "SNMP", "roles": ["switch"]},
            {"id": "dev3", "hostname": "server1", "mgmt_ip": "192.168.1.3", "vendor": "HP", "model": "ProLiant", "status": "up", "connection_type": "SSH", "roles": ["server"]},
            {"id": "dev4", "hostname": "unknown1", "mgmt_ip": "192.168.1.4", "vendor": None, "model": None, "status": "unknown", "connection_type": None, "roles": []}
        ]
        
        for device_data in devices_data:
            response = client.post("/devices", json=device_data)
            assert response.status_code == 200

        # Test getting grouping stats
        response = client.get("/devices/grouped/stats")
        assert response.status_code == 200
        
        stats = response.json()
        
        # Check that all grouping types are present
        assert "vendor" in stats
        assert "status" in stats
        assert "connection_type" in stats
        assert "device_type" in stats
        
        # Check vendor stats
        assert stats["vendor"]["Cisco"] == 2
        assert stats["vendor"]["HP"] == 1
        assert stats["vendor"]["Unknown"] == 1
        
        # Check status stats
        assert stats["status"]["up"] == 2
        assert stats["status"]["down"] == 1
        assert stats["status"]["unknown"] == 1
        
        # Check connection type stats
        assert stats["connection_type"]["SNMP"] == 2
        assert stats["connection_type"]["SSH"] == 1
        assert stats["connection_type"]["Unknown"] == 1
        
        # Check device type stats
        assert stats["device_type"]["Router/Gateway"] == 1
        assert stats["device_type"]["Switch"] == 1
        assert stats["device_type"]["Server"] == 1
        assert stats["device_type"]["Other Device"] == 1

    def test_grouped_devices_empty_database(self, clean_database):
        """Test grouped devices endpoint with empty database"""
        response = client.get("/devices/grouped")
        assert response.status_code == 200
        
        grouped_data = response.json()
        assert grouped_data == {}

    def test_grouping_stats_empty_database(self, clean_database):
        """Test grouping stats endpoint with empty database"""
        response = client.get("/devices/grouped/stats")
        assert response.status_code == 200
        
        stats = response.json()
        expected_stats = {
            "vendor": {},
            "status": {},
            "connection_type": {},
            "device_type": {}
        }
        assert stats == expected_stats

    def test_invalid_group_by_parameter(self, clean_database):
        """Test with invalid group_by parameter"""
        response = client.get("/devices/grouped?group_by=invalid")
        assert response.status_code == 200
        
        grouped_data = response.json()
        # Should return empty result when no devices exist
        assert grouped_data == {}

    def test_grouped_devices_sorting(self, clean_database):
        """Test that grouped devices are properly sorted"""
        # Create test devices with different names
        devices_data = [
            {"id": "dev1", "hostname": "z-device", "mgmt_ip": "192.168.1.1", "vendor": "Cisco", "model": "ISR4331", "status": "up"},
            {"id": "dev2", "hostname": "a-device", "mgmt_ip": "192.168.1.2", "vendor": "Cisco", "model": "Catalyst 2960", "status": "up"},
            {"id": "dev3", "hostname": "m-device", "mgmt_ip": "192.168.1.3", "vendor": "Cisco", "model": "ProLiant", "status": "up"}
        ]
        
        for device_data in devices_data:
            response = client.post("/devices", json=device_data)
            assert response.status_code == 200

        # Test grouping by vendor
        response = client.get("/devices/grouped?group_by=vendor")
        assert response.status_code == 200
        
        grouped_data = response.json()
        cisco_devices = grouped_data["Cisco"]
        
        # Check that devices are sorted by hostname
        assert len(cisco_devices) == 3
        assert cisco_devices[0]["hostname"] == "a-device"
        assert cisco_devices[1]["hostname"] == "m-device"
        assert cisco_devices[2]["hostname"] == "z-device"

    def test_grouped_devices_with_null_values(self, clean_database):
        """Test grouping with devices that have null values"""
        # Create test devices with null values
        devices_data = [
            {"id": "dev1", "hostname": None, "mgmt_ip": "192.168.1.1", "vendor": None, "model": None, "status": None, "connection_type": None},
            {"id": "dev2", "hostname": "device2", "mgmt_ip": "192.168.1.2", "vendor": "Cisco", "model": "ISR4331", "status": "up", "connection_type": "SNMP"}
        ]
        
        for device_data in devices_data:
            response = client.post("/devices", json=device_data)
            assert response.status_code == 200

        # Test grouping by vendor
        response = client.get("/devices/grouped?group_by=vendor")
        assert response.status_code == 200
        
        grouped_data = response.json()
        assert "Unknown" in grouped_data
        assert "Cisco" in grouped_data
        assert len(grouped_data["Unknown"]) == 1
        assert len(grouped_data["Cisco"]) == 1
        
        # Check that null hostname is handled properly (converted to "Unknown")
        unknown_device = grouped_data["Unknown"][0]
        assert unknown_device["hostname"] == "Unknown"
        assert unknown_device["mgmtIp"] == "192.168.1.1"
