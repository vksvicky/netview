from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from ..models import UserSettings


class UserSettingsService:
    def __init__(self):
        pass
    
    def get_device_mapping(self, db: Session, identifier: str, device_type: str = "mac_mapping") -> Optional[Dict[str, str]]:
        """Get user-defined device mapping by MAC or IP"""
        setting = db.query(UserSettings).filter(
            UserSettings.id == identifier,
            UserSettings.device_type == device_type
        ).first()
        
        if setting:
            return {
                "vendor": setting.vendor,
                "model": setting.model,
                "hostname": setting.hostname,
                "notes": setting.notes
            }
        return None
    
    def set_device_mapping(self, db: Session, identifier: str, device_type: str, 
                          vendor: str, model: str, hostname: str = None, notes: str = None) -> UserSettings:
        """Set user-defined device mapping"""
        setting = db.query(UserSettings).filter(
            UserSettings.id == identifier,
            UserSettings.device_type == device_type
        ).first()
        
        if not setting:
            setting = UserSettings(
                id=identifier,
                device_type=device_type
            )
        
        setting.vendor = vendor
        setting.model = model
        setting.hostname = hostname
        setting.notes = notes
        
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting
    
    def get_all_mappings(self, db: Session) -> List[Dict[str, Any]]:
        """Get all user-defined device mappings"""
        settings = db.query(UserSettings).all()
        return [
            {
                "id": s.id,
                "device_type": s.device_type,
                "vendor": s.vendor,
                "model": s.model,
                "hostname": s.hostname,
                "notes": s.notes,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in settings
        ]
    
    def delete_mapping(self, db: Session, identifier: str, device_type: str) -> bool:
        """Delete user-defined device mapping"""
        setting = db.query(UserSettings).filter(
            UserSettings.id == identifier,
            UserSettings.device_type == device_type
        ).first()
        
        if setting:
            db.delete(setting)
            db.commit()
            return True
        return False
    
    def apply_user_mappings_to_device(self, db: Session, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply user-defined mappings to device data"""
        # Try MAC mapping first
        if device_data.get("mac") and device_data["mac"] != "Unknown":
            mac_mapping = self.get_device_mapping(db, device_data["mac"], "mac_mapping")
            if mac_mapping:
                device_data["vendor"] = mac_mapping["vendor"]
                device_data["model"] = mac_mapping["model"]
                if mac_mapping.get("hostname"):
                    device_data["hostname"] = mac_mapping["hostname"]
                return device_data
        
        # Try IP mapping as fallback
        if device_data.get("mgmtIp"):
            ip_mapping = self.get_device_mapping(db, device_data["mgmtIp"], "ip_mapping")
            if ip_mapping:
                device_data["vendor"] = ip_mapping["vendor"]
                device_data["model"] = ip_mapping["model"]
                if ip_mapping.get("hostname"):
                    device_data["hostname"] = ip_mapping["hostname"]
                return device_data
        
        return device_data


# Global instance
user_settings_service = UserSettingsService()
