from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from ..models import Device, Notification, NotificationRule, DeviceHistory


class NotificationService:
    """Service for managing network notifications and alerts"""
    
    def __init__(self):
        self.notification_types = {
            'new_device': {
                'title_template': 'New Device Detected',
                'message_template': 'A new device "{hostname}" ({ip}) from {vendor} has joined the network',
                'severity': 'info'
            },
            'device_offline': {
                'title_template': 'Device Went Offline',
                'message_template': 'Device "{hostname}" ({ip}) has gone offline',
                'severity': 'warning'
            },
            'device_online': {
                'title_template': 'Device Came Online',
                'message_template': 'Device "{hostname}" ({ip}) has come back online',
                'severity': 'info'
            },
            'ip_change': {
                'title_template': 'Device IP Changed',
                'message_template': 'Device "{hostname}" IP changed from {old_ip} to {new_ip}',
                'severity': 'warning'
            },
            'topology_change': {
                'title_template': 'Network Topology Changed',
                'message_template': 'Network topology has changed: {description}',
                'severity': 'info'
            },
            'security_alert': {
                'title_template': 'Security Alert',
                'message_template': 'Security alert: {description}',
                'severity': 'critical'
            },
            'unknown_device': {
                'title_template': 'Unknown Device Detected',
                'message_template': 'Unknown device "{hostname}" ({ip}) detected - requires identification',
                'severity': 'warning'
            }
        }
    
    def create_notification(
        self,
        db: Session,
        notification_type: str,
        device_id: Optional[str] = None,
        title: Optional[str] = None,
        message: Optional[str] = None,
        severity: Optional[str] = None,
        notification_data: Optional[Dict] = None
    ) -> Notification:
        """Create a new notification"""
        
        # Get template if not provided
        if notification_type in self.notification_types:
            template = self.notification_types[notification_type]
            if not title:
                title = template['title_template']
            if not severity:
                severity = template['severity']
        
        # Get device info if device_id provided
        device_info = {}
        if device_id:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                device_info = {
                    'hostname': device.hostname,
                    'ip': device.mgmt_ip,
                    'vendor': device.vendor,
                    'model': device.model
                }
        
        # Format message with device info
        if not message and notification_type in self.notification_types:
            template = self.notification_types[notification_type]
            # Merge device_info and notification_data, with notification_data taking precedence
            format_data = {**device_info, **(notification_data or {})}
            message = template['message_template'].format(**format_data)
        
        # Create notification
        notification = Notification(
            notification_type=notification_type,
            title=title or f"{notification_type.replace('_', ' ').title()}",
            message=message or f"Notification: {notification_type}",
            device_id=device_id,
            severity=severity or 'info',
            notification_data=notification_data or {}
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification
    
    def get_notifications(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0,
        notification_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_read: Optional[bool] = None,
        days_back: int = 7
    ) -> List[Notification]:
        """Get notifications with filtering options"""
        
        query = db.query(Notification)
        
        # Apply filters
        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)
        if severity:
            query = query.filter(Notification.severity == severity)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        
        # Time filter
        cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_back)
        query = query.filter(Notification.created_at >= cutoff_date)
        
        # Order and paginate
        query = query.order_by(desc(Notification.created_at))
        query = query.offset(offset).limit(limit)
        
        return query.all()
    
    def get_unread_count(self, db: Session) -> int:
        """Get count of unread notifications"""
        return db.query(Notification).filter(Notification.is_read == False).count()
    
    def mark_as_read(self, db: Session, notification_id: int) -> bool:
        """Mark a notification as read"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = True
            db.commit()
            return True
        return False
    
    def mark_all_as_read(self, db: Session) -> int:
        """Mark all notifications as read"""
        count = db.query(Notification).filter(Notification.is_read == False).update(
            {Notification.is_read: True}
        )
        db.commit()
        return count
    
    def acknowledge_notification(
        self,
        db: Session,
        notification_id: int,
        acknowledged_by: str = "system"
    ) -> bool:
        """Acknowledge a notification"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_acknowledged = True
            notification.acknowledged_at = datetime.now(UTC).replace(tzinfo=None)
            notification.acknowledged_by = acknowledged_by
            db.commit()
            return True
        return False
    
    def delete_old_notifications(self, db: Session, days_old: int = 30) -> int:
        """Delete notifications older than specified days"""
        cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_old)
        count = db.query(Notification).filter(Notification.created_at < cutoff_date).delete()
        db.commit()
        return count
    
    def get_notification_stats(self, db: Session, days_back: int = 7) -> Dict:
        """Get notification statistics"""
        cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_back)
        
        # Total notifications
        total = db.query(Notification).filter(Notification.created_at >= cutoff_date).count()
        
        # By type
        by_type = db.query(
            Notification.notification_type,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.created_at >= cutoff_date
        ).group_by(Notification.notification_type).all()
        
        # By severity
        by_severity = db.query(
            Notification.severity,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.created_at >= cutoff_date
        ).group_by(Notification.severity).all()
        
        # Unread count
        unread = db.query(Notification).filter(
            Notification.created_at >= cutoff_date,
            Notification.is_read == False
        ).count()
        
        return {
            'total_notifications': total,
            'unread_notifications': unread,
            'by_type': {ntype: count for ntype, count in by_type},
            'by_severity': {severity: count for severity, count in by_severity},
            'period_days': days_back
        }
    
    def process_device_event(self, db: Session, device_id: str, event_type: str, event_data: Dict) -> Optional[Notification]:
        """Process device events and create notifications based on rules"""
        
        # Check if we should create a notification for this event type
        if event_type in ['online', 'offline', 'ip_change']:
            notification_type = f"device_{event_type}"
            
            # Get device info
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return None
            
            # Create notification
            notification_data = {
                'hostname': device.hostname,
                'ip': device.mgmt_ip,
                'vendor': device.vendor,
                'old_ip': event_data.get('previous_ip'),
                'new_ip': event_data.get('new_ip')
            }
            
            return self.create_notification(
                db=db,
                notification_type=notification_type,
                device_id=device_id,
                notification_data=notification_data
            )
        
        return None
    
    def process_new_device(self, db: Session, device_id: str, device_data: Dict) -> Notification:
        """Process new device detection and create notification"""
        
        # Determine if device is unknown
        vendor = device_data.get('vendor', 'Unknown')
        is_unknown = vendor == 'Unknown' or not device_data.get('hostname')
        
        notification_type = 'unknown_device' if is_unknown else 'new_device'
        
        notification_data = {
            'hostname': device_data.get('hostname', 'Unknown'),
            'ip': device_data.get('mgmt_ip', 'Unknown'),
            'vendor': vendor,
            'model': device_data.get('model', 'Unknown')
        }
        
        return self.create_notification(
            db=db,
            notification_type=notification_type,
            device_id=device_id,
            notification_data=notification_data
        )


# Global instance
notification_service = NotificationService()
