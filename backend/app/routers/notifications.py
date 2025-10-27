from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Notification
from ..services.notification_service import notification_service

router = APIRouter()


@router.get("/")
def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    notification_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    days_back: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get notifications with filtering options"""
    
    try:
        notifications = notification_service.get_notifications(
            db=db,
            limit=limit,
            offset=offset,
            notification_type=notification_type,
            severity=severity,
            is_read=is_read,
            days_back=days_back
        )
        
        return [
            {
                "id": n.id,
                "notification_type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "device_id": n.device_id,
                "severity": n.severity,
                "is_read": n.is_read,
                "is_acknowledged": n.is_acknowledged,
                "created_at": n.created_at.isoformat(),
                "acknowledged_at": n.acknowledged_at.isoformat() if n.acknowledged_at else None,
                "acknowledged_by": n.acknowledged_by,
                "notification_data": n.notification_data
            }
            for n in notifications
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving notifications: {str(e)}")


@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)) -> dict:
    """Get count of unread notifications"""
    
    try:
        count = notification_service.get_unread_count(db)
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting unread count: {str(e)}")


@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Mark a notification as read"""
    
    try:
        success = notification_service.mark_as_read(db, notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")


@router.put("/mark-all-read")
def mark_all_notifications_as_read(db: Session = Depends(get_db)) -> dict:
    """Mark all notifications as read"""
    
    try:
        count = notification_service.mark_all_as_read(db)
        return {"success": True, "count": count, "message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notifications as read: {str(e)}")


@router.put("/{notification_id}/acknowledge")
def acknowledge_notification(
    notification_id: int,
    acknowledged_by: str = Query("system"),
    db: Session = Depends(get_db)
) -> dict:
    """Acknowledge a notification"""
    
    try:
        success = notification_service.acknowledge_notification(db, notification_id, acknowledged_by)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "message": "Notification acknowledged"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error acknowledging notification: {str(e)}")


@router.get("/stats")
def get_notification_stats(
    days_back: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
) -> dict:
    """Get notification statistics"""
    
    try:
        stats = notification_service.get_notification_stats(db, days_back)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving notification stats: {str(e)}")


@router.delete("/cleanup")
def cleanup_old_notifications(
    days_old: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
) -> dict:
    """Delete notifications older than specified days"""
    
    try:
        count = notification_service.delete_old_notifications(db, days_old)
        return {"success": True, "count": count, "message": f"Deleted {count} old notifications"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up notifications: {str(e)}")


@router.post("/test")
def create_test_notification(
    notification_type: str = Query("info"),
    title: str = Query("Test Notification"),
    message: str = Query("This is a test notification"),
    severity: str = Query("info"),
    db: Session = Depends(get_db)
) -> dict:
    """Create a test notification (for development/testing)"""
    
    try:
        notification = notification_service.create_notification(
            db=db,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity
        )
        
        return {
            "success": True,
            "notification": {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "severity": notification.severity,
                "created_at": notification.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test notification: {str(e)}")
