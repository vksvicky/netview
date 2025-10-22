from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..services.oui_database import oui_db

router = APIRouter()


@router.get("/stats")
def get_oui_stats() -> Dict[str, Any]:
    """Get OUI database statistics"""
    try:
        stats = oui_db.get_database_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting OUI stats: {str(e)}")


@router.post("/update")
def update_oui_database() -> Dict[str, Any]:
    """Update OUI database from IEEE standards website"""
    try:
        result = oui_db.update_from_ieee()
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return {
            "status": "success",
            "message": "OUI database updated successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating OUI database: {str(e)}")


@router.get("/lookup/{mac_address}")
def lookup_vendor(mac_address: str) -> Dict[str, Any]:
    """Look up vendor name from MAC address"""
    try:
        vendor = oui_db.lookup_vendor(mac_address)
        return {
            "status": "success",
            "data": {
                "mac_address": mac_address,
                "vendor": vendor
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error looking up vendor: {str(e)}")


@router.get("/search")
def search_organization(query: str) -> Dict[str, Any]:
    """Search for organizations by name"""
    try:
        if not query or len(query) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters long")
        
        results = oui_db.search_organization(query)
        return {
            "status": "success",
            "data": {
                "query": query,
                "results": results,
                "count": len(results)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching organizations: {str(e)}")


@router.get("/debug/unknown-vendors")
def get_unknown_vendors() -> Dict[str, Any]:
    """Get all devices with unknown vendors for debugging"""
    try:
        from ..db import get_db
        from ..models import Device
        from sqlalchemy.orm import Session
        
        db = next(get_db())
        unknown_devices = db.query(Device).filter(Device.vendor == "Unknown").all()
        
        debug_data = []
        for device in unknown_devices:
            # Try to get MAC address from device data or interfaces
            mac_address = "Unknown"
            if hasattr(device, 'mac') and device.mac:
                mac_address = device.mac
            elif hasattr(device, 'interfaces') and device.interfaces:
                # Try to get MAC from first interface
                for interface in device.interfaces:
                    if hasattr(interface, 'mac') and interface.mac:
                        mac_address = interface.mac
                        break
            
            debug_data.append({
                "id": device.id,
                "hostname": device.hostname,
                "mgmtIp": device.mgmt_ip,
                "mac_address": mac_address,
                "model": device.model,
                "status": device.status,
                "lastSeen": device.last_seen.isoformat() if device.last_seen else None
            })
        
        # Get total devices from topology instead of database count
        # Count devices that are currently active (not just in database)
        active_devices = db.query(Device).filter(Device.status == 'up').count()
        total_devices = active_devices
        
        return {
            "status": "success",
            "data": {
                "unknown_devices": debug_data,
                "count": len(debug_data),
                "total_devices": total_devices
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting unknown vendors: {str(e)}")
