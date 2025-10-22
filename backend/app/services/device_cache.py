import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class DeviceCache:
    def __init__(self, cache_duration_minutes: int = 5):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.devices_cache: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.cache_file = "device_cache.json"
        
        # Load cache from file on initialization
        self._load_from_file()
        
    def is_cache_valid(self) -> bool:
        """Check if the cache is still valid"""
        if not self.last_update:
            return False
        return datetime.now() - self.last_update < self.cache_duration
    
    def get_cached_devices(self) -> List[Dict[str, Any]]:
        """Get devices from cache if valid"""
        if self.is_cache_valid():
            return list(self.devices_cache.values())
        return []
    
    def update_cache(self, devices: List[Dict[str, Any]]) -> None:
        """Update the device cache"""
        # Convert list to dict for faster lookups
        self.devices_cache = {device.get('id', device.get('mgmtIp', '')): device for device in devices}
        self.last_update = datetime.now()
        
        # Save to file for persistence
        self._save_to_file()
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific device from cache"""
        return self.devices_cache.get(device_id)
    
    def update_device(self, device: Dict[str, Any]) -> None:
        """Update a single device in cache"""
        device_id = device.get('id', device.get('mgmtIp', ''))
        if device_id:
            self.devices_cache[device_id] = device
            self.last_update = datetime.now()
            self._save_to_file()
    
    def remove_device(self, device_id: str) -> None:
        """Remove a device from cache"""
        if device_id in self.devices_cache:
            del self.devices_cache[device_id]
            self.last_update = datetime.now()
            self._save_to_file()
    
    def _save_to_file(self) -> None:
        """Save cache to file for persistence"""
        try:
            cache_data = {
                'devices': list(self.devices_cache.values()),
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save cache to file: {e}")
    
    def _load_from_file(self) -> None:
        """Load cache from file"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            devices = cache_data.get('devices', [])
            self.devices_cache = {device.get('id', device.get('mgmtIp', '')): device for device in devices}
            
            last_update_str = cache_data.get('last_update')
            if last_update_str:
                self.last_update = datetime.fromisoformat(last_update_str)
                
        except FileNotFoundError:
            # Cache file doesn't exist yet, that's fine
            pass
        except Exception as e:
            print(f"Failed to load cache from file: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'device_count': len(self.devices_cache),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'is_valid': self.is_cache_valid(),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60
        }


# Global cache instance
device_cache = DeviceCache()
