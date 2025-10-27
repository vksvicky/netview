import pytest
from behave import given, when, then
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models import Device, init_db
from app.db import get_db
import json

client = TestClient(app)

@given('an empty database with device grouping enabled')
def step_empty_database_with_grouping(context):
    """Initialize empty database"""
    init_db()
    context.devices = []

@given('the following devices exist')
def step_devices_exist(context):
    """Create devices from the table data"""
    init_db()
    context.devices = []
    
    for row in context.table:
        device_data = {
            "id": f"dev_{len(context.devices) + 1}",
            "hostname": row["hostname"],
            "mgmt_ip": row["mgmt_ip"],
            "vendor": row["vendor"] if row["vendor"] else None,
            "model": row["model"] if row["model"] else None,
            "status": row["status"] if row["status"] else None,
            "connection_type": row.get("connection_type") if row.get("connection_type") else None,
            "roles": [row["roles"]] if row.get("roles") else []
        }
        
        response = client.post("/devices", json=device_data)
        assert response.status_code == 200
        context.devices.append(device_data)

@given('no devices exist')
def step_no_devices_exist(context):
    """Ensure no devices exist"""
    init_db()
    context.devices = []

@when('I request devices grouped by vendor')
def step_request_grouped_by_vendor(context):
    """Request devices grouped by vendor"""
    response = client.get("/devices/grouped?group_by=vendor")
    assert response.status_code == 200
    context.grouped_response = response.json()

@when('I request devices grouped by status')
def step_request_grouped_by_status(context):
    """Request devices grouped by status"""
    response = client.get("/devices/grouped?group_by=status")
    assert response.status_code == 200
    context.grouped_response = response.json()

@when('I request devices grouped by connection type')
def step_request_grouped_by_connection_type(context):
    """Request devices grouped by connection type"""
    response = client.get("/devices/grouped?group_by=connection_type")
    assert response.status_code == 200
    context.grouped_response = response.json()

@when('I request devices grouped by device type')
def step_request_grouped_by_device_type(context):
    """Request devices grouped by device type"""
    response = client.get("/devices/grouped?group_by=device_type")
    assert response.status_code == 200
    context.grouped_response = response.json()

@when('I request grouping statistics')
def step_request_grouping_stats(context):
    """Request grouping statistics"""
    response = client.get("/devices/grouped/stats")
    assert response.status_code == 200
    context.stats_response = response.json()

@when('I request devices grouped by invalid criteria')
def step_request_grouped_by_invalid(context):
    """Request devices grouped by invalid criteria"""
    response = client.get("/devices/grouped?group_by=invalid")
    assert response.status_code == 200
    context.grouped_response = response.json()

@then('I should see the following groups')
def step_verify_groups(context):
    """Verify that the expected groups exist with correct counts"""
    for row in context.table:
        group_name = row["group_name"]
        expected_count = int(row["device_count"])
        
        assert group_name in context.grouped_response, f"Group '{group_name}' not found"
        actual_count = len(context.grouped_response[group_name])
        assert actual_count == expected_count, f"Expected {expected_count} devices in '{group_name}', got {actual_count}"

@then('each group should contain the correct devices')
def step_verify_group_devices(context):
    """Verify that groups contain the correct devices"""
    # This is a placeholder - in a real implementation, you would verify
    # that each group contains the devices that match the grouping criteria
    pass

@then('I should see vendor statistics')
def step_verify_vendor_stats(context):
    """Verify vendor statistics"""
    vendor_stats = context.stats_response["vendor"]
    for row in context.table:
        vendor = row["vendor"]
        expected_count = int(row["count"])
        assert vendor in vendor_stats, f"Vendor '{vendor}' not found in stats"
        assert vendor_stats[vendor] == expected_count, f"Expected {expected_count} devices for vendor '{vendor}', got {vendor_stats[vendor]}"

@then('I should see status statistics')
def step_verify_status_stats(context):
    """Verify status statistics"""
    status_stats = context.stats_response["status"]
    for row in context.table:
        status = row["status"]
        expected_count = int(row["count"])
        assert status in status_stats, f"Status '{status}' not found in stats"
        assert status_stats[status] == expected_count, f"Expected {expected_count} devices for status '{status}', got {status_stats[status]}"

@then('I should see connection type statistics')
def step_verify_connection_type_stats(context):
    """Verify connection type statistics"""
    conn_type_stats = context.stats_response["connection_type"]
    for row in context.table:
        conn_type = row["connection_type"]
        expected_count = int(row["count"])
        assert conn_type in conn_type_stats, f"Connection type '{conn_type}' not found in stats"
        assert conn_type_stats[conn_type] == expected_count, f"Expected {expected_count} devices for connection type '{conn_type}', got {conn_type_stats[conn_type]}"

@then('I should see device type statistics')
def step_verify_device_type_stats(context):
    """Verify device type statistics"""
    device_type_stats = context.stats_response["device_type"]
    for row in context.table:
        device_type = row["device_type"]
        expected_count = int(row["count"])
        assert device_type in device_type_stats, f"Device type '{device_type}' not found in stats"
        assert device_type_stats[device_type] == expected_count, f"Expected {expected_count} devices for device type '{device_type}', got {device_type_stats[device_type]}"

@then('I should receive an empty response')
def step_verify_empty_response(context):
    """Verify that the response is empty"""
    assert context.grouped_response == {}, f"Expected empty response, got {context.grouped_response}"

@then('I should receive empty statistics for all grouping types')
def step_verify_empty_stats(context):
    """Verify that all grouping statistics are empty"""
    expected_stats = {
        "vendor": {},
        "status": {},
        "connection_type": {},
        "device_type": {}
    }
    assert context.stats_response == expected_stats, f"Expected empty stats, got {context.stats_response}"

@then('the Cisco group should contain devices in alphabetical order')
def step_verify_alphabetical_order(context):
    """Verify that devices in a group are sorted alphabetically"""
    cisco_devices = context.grouped_response["Cisco"]
    hostnames = [device["hostname"] for device in cisco_devices]
    
    expected_hostnames = [row["hostname"] for row in context.table]
    assert hostnames == expected_hostnames, f"Expected {expected_hostnames}, got {hostnames}"

@then('all devices should be grouped under "Unknown"')
def step_verify_unknown_grouping(context):
    """Verify that all devices are grouped under Unknown for invalid criteria"""
    assert "Unknown" in context.grouped_response, "Expected 'Unknown' group for invalid criteria"
    total_devices = sum(len(devices) for devices in context.grouped_response.values())
    assert total_devices == len(context.devices), f"Expected {len(context.devices)} devices, got {total_devices}"
