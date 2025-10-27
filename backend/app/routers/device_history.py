from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

from ..db import get_db
from ..models import DeviceHistory
from ..services.device_history import device_history_service

router = APIRouter()


@router.get("/devices/{device_id}/history")
def get_device_history(
    device_id: str,
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get device connection/disconnection history"""
    
    try:
        history = device_history_service.get_device_history(
            db=db,
            device_id=device_id,
            limit=limit,
            event_type=event_type,
            days_back=days_back
        )
        
        return [
            {
                "id": h.id,
                "device_id": h.device_id,
                "event_type": h.event_type,
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "previous_ip": h.previous_ip,
                "new_ip": h.new_ip,
                "event_timestamp": h.event_timestamp.isoformat(),
                "duration_seconds": h.duration_seconds,
                "event_metadata": h.event_metadata
            }
            for h in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving device history: {str(e)}")


@router.get("/devices/{device_id}/history/stats")
def get_device_session_stats(
    device_id: str,
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> dict:
    """Get device session statistics"""
    
    try:
        stats = device_history_service.get_device_session_stats(
            db=db,
            device_id=device_id,
            days_back=days_back
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving device stats: {str(e)}")


@router.get("/history")
def get_all_device_history(
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = Query(None),
    days_back: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all device history across the network"""
    
    try:
        history = device_history_service.get_all_device_history(
            db=db,
            limit=limit,
            event_type=event_type,
            days_back=days_back
        )
        
        return [
            {
                "id": h.id,
                "device_id": h.device_id,
                "event_type": h.event_type,
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "previous_ip": h.previous_ip,
                "new_ip": h.new_ip,
                "event_timestamp": h.event_timestamp.isoformat(),
                "duration_seconds": h.duration_seconds,
                "event_metadata": h.event_metadata
            }
            for h in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving device history: {str(e)}")


@router.get("/history/recent")
def get_recent_events(
    hours_back: int = Query(24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get recent device events across the network"""
    
    try:
        # Convert hours to days for the service
        days_back = max(1, hours_back // 24)
        
        history = device_history_service.get_all_device_history(
            db=db,
            limit=50,
            days_back=days_back
        )
        
        # Filter to only show events within the specified hours
        cutoff_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=hours_back)
        recent_history = [h for h in history if h.event_timestamp >= cutoff_time]
        
        return [
            {
                "id": h.id,
                "device_id": h.device_id,
                "event_type": h.event_type,
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "previous_ip": h.previous_ip,
                "new_ip": h.new_ip,
                "event_timestamp": h.event_timestamp.isoformat(),
                "duration_seconds": h.duration_seconds,
                "event_metadata": h.event_metadata
            }
            for h in recent_history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recent events: {str(e)}")


@router.get("/history/summary")
def get_history_summary(
    days_back: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
) -> dict:
    """Get summary statistics of device history"""
    
    try:
        from datetime import timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_back)
        
        # Get event counts by type
        event_counts = db.query(
            DeviceHistory.event_type,
            func.count(DeviceHistory.id).label('count')
        ).filter(
            DeviceHistory.event_timestamp >= cutoff_date
        ).group_by(DeviceHistory.event_type).all()
        
        # Get unique devices with events
        unique_devices = db.query(func.count(func.distinct(DeviceHistory.device_id))).filter(
            DeviceHistory.event_timestamp >= cutoff_date
        ).scalar()
        
        # Get most active devices
        most_active = db.query(
            DeviceHistory.device_id,
            func.count(DeviceHistory.id).label('event_count')
        ).filter(
            DeviceHistory.event_timestamp >= cutoff_date
        ).group_by(DeviceHistory.device_id).order_by(
            func.count(DeviceHistory.id).desc()
        ).limit(10).all()
        
        return {
            "summary_period_days": days_back,
            "total_events": sum(count for _, count in event_counts),
            "unique_devices_with_events": unique_devices,
            "events_by_type": {event_type: count for event_type, count in event_counts},
            "most_active_devices": [
                {"device_id": device_id, "event_count": count}
                for device_id, count in most_active
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history summary: {str(e)}")
