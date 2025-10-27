from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import get_db
from ..models import Device

router = APIRouter()


class DeviceCreate(BaseModel):
    id: str
    hostname: Optional[str] = None
    mgmt_ip: str
    vendor: Optional[str] = "Unknown"
    model: Optional[str] = "Unknown"
    status: Optional[str] = "up"
    connection_type: Optional[str] = None
    roles: Optional[List[str]] = None


@router.get("")
def list_devices(db: Session = Depends(get_db)) -> List[dict]:
    devices = db.query(Device).all()
    return [
        {
            "id": d.id,
            "hostname": d.hostname,
            "mgmtIp": d.mgmt_ip,
            "vendor": d.vendor,
            "model": d.model,
            "status": d.status,
            "lastSeen": d.last_seen.isoformat() if d.last_seen else None,
        }
        for d in devices
    ]


@router.post("")
def create_device(device: DeviceCreate, db: Session = Depends(get_db)) -> dict:
    # Check if device already exists
    existing = db.query(Device).filter(Device.id == device.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device with this ID already exists")
    
    # Create new device
    new_device = Device(
        id=device.id,
        hostname=device.hostname or "Unknown",
        mgmt_ip=device.mgmt_ip,
        vendor=device.vendor or "Unknown",
        model=device.model or "Unknown",
        status=device.status or "up",
        connection_type=device.connection_type,
        roles=device.roles or []
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    return {
        "id": new_device.id,
        "hostname": new_device.hostname,
        "mgmtIp": new_device.mgmt_ip,
        "vendor": new_device.vendor,
        "model": new_device.model,
        "status": new_device.status,
        "lastSeen": new_device.last_seen.isoformat() if new_device.last_seen else None,
    }


@router.delete("/{device_id}")
def delete_device(device_id: str, db: Session = Depends(get_db)) -> dict:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    return {"message": f"Device {device_id} deleted successfully"}


@router.get("/grouped")
def get_grouped_devices(
    group_by: str = Query("vendor", description="Group by: vendor, status, connection_type, device_type"),
    db: Session = Depends(get_db)
) -> Dict[str, List[dict]]:
    """Get devices grouped by specified criteria"""
    devices = db.query(Device).all()
    
    # Convert devices to dict format
    device_list = [
        {
            "id": d.id,
            "hostname": d.hostname,
            "mgmtIp": d.mgmt_ip,
            "vendor": d.vendor,
            "model": d.model,
            "status": d.status,
            "connectionType": d.connection_type,
            "lastSeen": d.last_seen.isoformat() if d.last_seen else None,
            "roles": d.roles or [],
            "deviceName": d.device_name
        }
        for d in devices
    ]
    
    # Group devices based on criteria
    grouped = {}
    for device in device_list:
        if group_by == "vendor":
            key = device["vendor"] or "Unknown"
        elif group_by == "status":
            key = device["status"] or "Unknown"
        elif group_by == "connection_type":
            key = device["connectionType"] or "Unknown"
        elif group_by == "device_type":
            # Determine device type based on roles and vendor
            roles = device["roles"] or []
            if "router" in roles or "gateway" in roles:
                key = "Router/Gateway"
            elif "switch" in roles:
                key = "Switch"
            elif "server" in roles:
                key = "Server"
            elif device["vendor"] and "cisco" in device["vendor"].lower():
                key = "Cisco Device"
            elif device["vendor"] and "hp" in device["vendor"].lower():
                key = "HP Device"
            elif device["vendor"] and "dell" in device["vendor"].lower():
                key = "Dell Device"
            else:
                key = "Other Device"
        else:
            key = "Unknown"
        
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(device)
    
    # Sort groups and devices within groups
    sorted_groups = {}
    for key in sorted(grouped.keys()):
        sorted_groups[key] = sorted(grouped[key], key=lambda x: x["hostname"] or x["mgmtIp"])
    
    return sorted_groups


@router.get("/grouped/stats")
def get_grouping_stats(db: Session = Depends(get_db)) -> Dict[str, Dict[str, int]]:
    """Get statistics for different grouping criteria"""
    devices = db.query(Device).all()
    
    stats = {
        "vendor": {},
        "status": {},
        "connection_type": {},
        "device_type": {}
    }
    
    for device in devices:
        # Vendor stats
        vendor = device.vendor or "Unknown"
        stats["vendor"][vendor] = stats["vendor"].get(vendor, 0) + 1
        
        # Status stats
        status = device.status or "Unknown"
        stats["status"][status] = stats["status"].get(status, 0) + 1
        
        # Connection type stats
        conn_type = device.connection_type or "Unknown"
        stats["connection_type"][conn_type] = stats["connection_type"].get(conn_type, 0) + 1
        
        # Device type stats
        roles = device.roles or []
        if "router" in roles or "gateway" in roles:
            device_type = "Router/Gateway"
        elif "switch" in roles:
            device_type = "Switch"
        elif "server" in roles:
            device_type = "Server"
        elif device.vendor and "cisco" in device.vendor.lower():
            device_type = "Cisco Device"
        elif device.vendor and "hp" in device.vendor.lower():
            device_type = "HP Device"
        elif device.vendor and "dell" in device.vendor.lower():
            device_type = "Dell Device"
        else:
            device_type = "Other Device"
        stats["device_type"][device_type] = stats["device_type"].get(device_type, 0) + 1
    
    return stats
    
@router.get("/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db)) -> dict:
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        return {}
    return {
        "id": d.id,
        "hostname": d.hostname,
        "mgmtIp": d.mgmt_ip,
        "vendor": d.vendor,
        "model": d.model,
        "status": d.status,
        "lastSeen": d.last_seen.isoformat() if d.last_seen else None,
    }
