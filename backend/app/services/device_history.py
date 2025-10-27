from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models import Device, DeviceHistory


class DeviceHistoryService:
    """Service for tracking device connection/disconnection history"""
    
    def __init__(self):
        self.device_sessions: Dict[str, Dict] = {}  # Track active sessions
    
    async def track_device_event(
        self, 
        db: Session, 
        device_id: str, 
        event_type: str,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        previous_ip: Optional[str] = None,
        new_ip: Optional[str] = None,
        event_metadata: Optional[Dict] = None
    ) -> DeviceHistory:
        """Track a device event and create history record"""
        
        # Calculate duration for offline events
        duration_seconds = None
        if event_type == "offline" and device_id in self.device_sessions:
            session_start = self.device_sessions[device_id].get("session_start")
            if session_start:
                duration_seconds = int((datetime.now(UTC).replace(tzinfo=None) - session_start).total_seconds())
                del self.device_sessions[device_id]
        
        # Create history record
        history = DeviceHistory(
            device_id=device_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            previous_ip=previous_ip,
            new_ip=new_ip,
            duration_seconds=duration_seconds,
            event_metadata=event_metadata or {}
        )
        
        db.add(history)
        
        # Create notification for significant events
        try:
            from .notification_service import notification_service
            event_data = {
                'previous_status': previous_status,
                'new_status': new_status,
                'previous_ip': previous_ip,
                'new_ip': new_ip
            }
            await notification_service.process_device_event(db, device_id, event_type, event_data)
        except Exception:
            # Don't fail history tracking if notification fails
            pass
        
        # Update session tracking for online events
        if event_type == "online":
            self.device_sessions[device_id] = {
                "session_start": datetime.now(UTC).replace(tzinfo=None),
                "ip": new_ip,
                "status": new_status
            }
        
        return history
    
    async def process_device_discovery(
        self, 
        db: Session, 
        discovered_devices: List[Dict], 
        existing_devices: List[Device]
    ) -> List[DeviceHistory]:
        """Process device discovery and track changes"""
        
        history_events = []
        existing_device_map = {d.id: d for d in existing_devices}
        discovered_device_map = {d.get("id") or d.get("mgmtIp"): d for d in discovered_devices}
        
        # Track devices that came online
        for device_id, device_data in discovered_device_map.items():
            if device_id not in existing_device_map:
                # New device discovered
                history = await self.track_device_event(
                    db=db,
                    device_id=device_id,
                    event_type="online",
                    new_status="up",
                    new_ip=device_data.get("mgmtIp"),
                    event_metadata={
                        "vendor": device_data.get("vendor"),
                        "model": device_data.get("model"),
                        "hostname": device_data.get("hostname"),
                        "connection_type": device_data.get("connection_type", "Unknown")
                    }
                )
                history_events.append(history)
            else:
                # Existing device - check for changes
                existing_device = existing_device_map[device_id]
                new_ip = device_data.get("mgmtIp")
                new_status = device_data.get("status", "up")
                
                # Check for IP changes
                if existing_device.mgmt_ip != new_ip:
                    history = await self.track_device_event(
                        db=db,
                        device_id=device_id,
                        event_type="ip_change",
                        previous_ip=existing_device.mgmt_ip,
                        new_ip=new_ip,
                        event_metadata={
                            "vendor": device_data.get("vendor"),
                            "model": device_data.get("model")
                        }
                    )
                    history_events.append(history)
                
                # Check for status changes
                if existing_device.status != new_status:
                    history = await self.track_device_event(
                        db=db,
                        device_id=device_id,
                        event_type="status_change",
                        previous_status=existing_device.status,
                        new_status=new_status,
                        event_metadata={
                            "vendor": device_data.get("vendor"),
                            "model": device_data.get("model")
                        }
                    )
                    history_events.append(history)
        
        # Track devices that went offline
        for device_id, existing_device in existing_device_map.items():
            if device_id not in discovered_device_map:
                # Device no longer discovered - mark as offline
                history = await self.track_device_event(
                    db=db,
                    device_id=device_id,
                    event_type="offline",
                    previous_status=existing_device.status,
                    previous_ip=existing_device.mgmt_ip,
                    event_metadata={
                        "vendor": existing_device.vendor,
                        "model": existing_device.model,
                        "hostname": existing_device.hostname
                    }
                )
                history_events.append(history)
        
        return history_events
    
    def get_device_history(
        self, 
        db: Session, 
        device_id: str, 
        limit: int = 50,
        event_type: Optional[str] = None,
        days_back: int = 30
    ) -> List[DeviceHistory]:
        """Get device history with optional filtering"""
        
        query = db.query(DeviceHistory).filter(
            DeviceHistory.device_id == device_id,
            DeviceHistory.event_timestamp >= datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_back)
        )
        
        if event_type:
            query = query.filter(DeviceHistory.event_type == event_type)
        
        return query.order_by(desc(DeviceHistory.event_timestamp)).limit(limit).all()
    
    def get_all_device_history(
        self, 
        db: Session, 
        limit: int = 100,
        event_type: Optional[str] = None,
        days_back: int = 7
    ) -> List[DeviceHistory]:
        """Get all device history with optional filtering"""
        
        query = db.query(DeviceHistory).filter(
            DeviceHistory.event_timestamp >= datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_back)
        )
        
        if event_type:
            query = query.filter(DeviceHistory.event_type == event_type)
        
        return query.order_by(desc(DeviceHistory.event_timestamp)).limit(limit).all()
    
    def get_device_session_stats(
        self, 
        db: Session, 
        device_id: str, 
        days_back: int = 30
    ) -> Dict:
        """Get device session statistics"""
        
        cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_back)
        
        # Get online/offline events
        events = db.query(DeviceHistory).filter(
            DeviceHistory.device_id == device_id,
            DeviceHistory.event_timestamp >= cutoff_date,
            DeviceHistory.event_type.in_(["online", "offline"])
        ).order_by(DeviceHistory.event_timestamp).all()
        
        total_sessions = 0
        total_online_time = 0
        avg_session_duration = 0
        
        for event in events:
            if event.event_type == "online":
                total_sessions += 1
            elif event.event_type == "offline" and event.duration_seconds:
                total_online_time += event.duration_seconds
        
        if total_sessions > 0:
            avg_session_duration = total_online_time / total_sessions
        
        return {
            "total_sessions": total_sessions,
            "total_online_time_seconds": total_online_time,
            "avg_session_duration_seconds": avg_session_duration,
            "days_tracked": days_back
        }


# Global instance
device_history_service = DeviceHistoryService()
