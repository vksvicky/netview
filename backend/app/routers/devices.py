from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import get_db
from ..models import Device

router = APIRouter()


class DeviceCreate(BaseModel):
    id: str
    hostname: str
    mgmt_ip: str
    vendor: str = "Unknown"
    model: str = "Unknown"
    status: str = "up"


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
        hostname=device.hostname,
        mgmt_ip=device.mgmt_ip,
        vendor=device.vendor,
        model=device.model,
        status=device.status
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


