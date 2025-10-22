from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from ..db import get_db
from ..services.user_settings import user_settings_service


router = APIRouter()


class DeviceMappingRequest(BaseModel):
    identifier: str  # MAC address or IP address
    device_type: str  # "mac_mapping" or "ip_mapping"
    vendor: str
    model: str
    hostname: str = None
    notes: str = None


class DeviceMappingResponse(BaseModel):
    id: str
    device_type: str
    vendor: str
    model: str
    hostname: str = None
    notes: str = None
    created_at: str = None
    updated_at: str = None


@router.get("/mappings", response_model=List[DeviceMappingResponse])
def get_all_mappings(db: Session = Depends(get_db)):
    """Get all user-defined device mappings"""
    try:
        mappings = user_settings_service.get_all_mappings(db)
        return mappings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting mappings: {str(e)}")


@router.post("/mappings", response_model=DeviceMappingResponse)
def create_mapping(request: DeviceMappingRequest, db: Session = Depends(get_db)):
    """Create a new device mapping"""
    try:
        setting = user_settings_service.set_device_mapping(
            db=db,
            identifier=request.identifier,
            device_type=request.device_type,
            vendor=request.vendor,
            model=request.model,
            hostname=request.hostname,
            notes=request.notes
        )
        
        return {
            "id": setting.id,
            "device_type": setting.device_type,
            "vendor": setting.vendor,
            "model": setting.model,
            "hostname": setting.hostname,
            "notes": setting.notes,
            "created_at": setting.created_at.isoformat() if setting.created_at else None,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating mapping: {str(e)}")


@router.get("/mappings/{identifier}/{device_type}", response_model=DeviceMappingResponse)
def get_mapping(identifier: str, device_type: str, db: Session = Depends(get_db)):
    """Get a specific device mapping"""
    try:
        mapping = user_settings_service.get_device_mapping(db, identifier, device_type)
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        return {
            "id": identifier,
            "device_type": device_type,
            "vendor": mapping["vendor"],
            "model": mapping["model"],
            "hostname": mapping.get("hostname"),
            "notes": mapping.get("notes"),
            "created_at": None,  # Would need to fetch from DB for full details
            "updated_at": None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting mapping: {str(e)}")


@router.put("/mappings/{identifier}/{device_type}", response_model=DeviceMappingResponse)
def update_mapping(identifier: str, device_type: str, request: DeviceMappingRequest, db: Session = Depends(get_db)):
    """Update an existing device mapping"""
    try:
        setting = user_settings_service.set_device_mapping(
            db=db,
            identifier=identifier,
            device_type=device_type,
            vendor=request.vendor,
            model=request.model,
            hostname=request.hostname,
            notes=request.notes
        )
        
        return {
            "id": setting.id,
            "device_type": setting.device_type,
            "vendor": setting.vendor,
            "model": setting.model,
            "hostname": setting.hostname,
            "notes": setting.notes,
            "created_at": setting.created_at.isoformat() if setting.created_at else None,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating mapping: {str(e)}")


@router.delete("/mappings/{identifier}/{device_type}")
def delete_mapping(identifier: str, device_type: str, db: Session = Depends(get_db)):
    """Delete a device mapping"""
    try:
        success = user_settings_service.delete_mapping(db, identifier, device_type)
        if not success:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        return {"status": "success", "message": "Mapping deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting mapping: {str(e)}")


@router.post("/apply-to-devices")
def apply_mappings_to_devices(db: Session = Depends(get_db)):
    """Apply user mappings to all existing devices in the database"""
    try:
        from ..models import Device
        
        devices = db.query(Device).all()
        updated_count = 0
        
        for device in devices:
            # Get device data as dict
            device_data = {
                "mac": None,
                "mgmtIp": device.mgmt_ip,
                "vendor": device.vendor,
                "model": device.model,
                "hostname": device.hostname
            }
            
            # Get MAC from first interface
            if device.interfaces:
                for interface in device.interfaces:
                    if interface.mac:
                        device_data["mac"] = interface.mac
                        break
            
            # Apply user mappings
            updated_data = user_settings_service.apply_user_mappings_to_device(db, device_data)
            
            # Update device if mapping was applied
            if (updated_data["vendor"] != device.vendor or 
                updated_data["model"] != device.model or 
                updated_data["hostname"] != device.hostname):
                
                device.vendor = updated_data["vendor"]
                device.model = updated_data["model"]
                device.hostname = updated_data["hostname"]
                updated_count += 1
        
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Applied mappings to {updated_count} devices",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying mappings: {str(e)}")
