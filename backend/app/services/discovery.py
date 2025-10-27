from typing import Any, Dict, List
from sqlalchemy.orm import Session

from ..models import Device, Interface, Edge
from .snmp import SnmpClient
from .fast_discovery import FastDiscoveryService
from .topology_builder import build_topology
from .user_settings import user_settings_service
from .device_history import device_history_service


class DiscoveryService:
    def __init__(self, snmp_client: SnmpClient, fast_discovery: FastDiscoveryService):
        self.snmp_client = snmp_client
        self.fast_discovery = fast_discovery

    async def run_discovery(self, db: Session, force_refresh: bool = False) -> Dict[str, List[dict]]:
        # Use fast discovery with caching for speed
        devices: List[Dict[str, Any]] = await self.fast_discovery.discover_devices(db, force_refresh)

        # If no devices found, don't clear existing ones (network might be temporarily down)
        if not devices:
            print("No devices found, keeping existing devices in database")
            # Return existing topology
            existing_devices = db.query(Device).all()
            return {
                "nodes": [
                    {
                        "id": d.id,
                        "label": d.hostname or d.id,
                        "title": d.mgmt_ip,
                        "group": d.vendor or "device",
                    }
                    for d in existing_devices
                ],
                "edges": []
            }

        # Get current device IPs to detect network changes
        current_ips = {d.get("mgmtIp") for d in devices if d.get("mgmtIp")}
        existing_devices = db.query(Device).all()
        existing_ips = {d.mgmt_ip for d in existing_devices}
        
        # Track device history changes before making any modifications
        if devices:  # Only track history if we have discovered devices
            history_events = device_history_service.process_device_discovery(
                db=db,
                discovered_devices=devices,
                existing_devices=existing_devices
            )
            
            # Create notifications for new devices
            try:
                from .notification_service import notification_service
                for device_data in devices:
                    device_id = device_data.get("id") or device_data.get("mgmtIp")
                    if device_id and device_id not in {d.id for d in existing_devices}:
                        # This is a new device
                        notification_service.process_new_device(db, device_id, device_data)
            except Exception:
                # Don't fail discovery if notification fails
                pass
            if history_events:
                print(f"📊 Tracked {len(history_events)} device history events")
                for event in history_events:
                    print(f"  - {event.event_type}: {event.device_id} ({event.new_status or event.previous_status})")
        
        # Check if we're on a different network (no overlap in IPs)
        if existing_ips and not current_ips.intersection(existing_ips):
            print(f"🔄 Network change detected! Old IPs: {existing_ips}, New IPs: {current_ips}")
            print("Clearing old devices and discovering new network...")
            # Clear old devices since we're on a different network
            db.query(Edge).delete()
            db.query(Interface).delete()
            db.query(Device).delete()
            db.commit()

        # Upsert devices
        device_map = {}
        for d in devices:
            device_id = d.get("id") or d.get("mgmtIp")
            if not device_id:
                continue
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                device = Device(id=device_id)
            device.hostname = d.get("hostname")
            device.mgmt_ip = d.get("mgmtIp")
            device.vendor = d.get("vendor")
            device.model = d.get("model")
            device.status = d.get("status", "up")
            device.connection_type = d.get("connection_type", "Unknown")
            device.ip_version = d.get("ip_version", "IPv4")
            device.device_name = d.get("device_name")
            db.add(device)
            device_map[device_id] = device

        # Upsert interfaces if provided, or create default interface with MAC
        for d in devices:
            device_id = d.get("id") or d.get("mgmtIp")
            ifaces = d.get("interfaces", [])
            
            # If no interfaces provided, create a default one with the MAC address
            if not ifaces and d.get("mac"):
                ifaces = [{
                    "ifIndex": 1,
                    "name": "default",
                    "mac": d.get("mac"),
                    "adminStatus": "up",
                    "operStatus": "up"
                }]
            
            for i in ifaces:
                iface_id = f"{device_id}:{i.get('ifIndex')}"
                iface = db.query(Interface).filter(Interface.id == iface_id).first()
                if not iface:
                    iface = Interface(id=iface_id, device_id=device_id, if_index=i.get("ifIndex"))
                iface.name = i.get("name")
                iface.speed = i.get("speed")
                iface.mac = i.get("mac")
                iface.admin_status = i.get("adminStatus")
                iface.oper_status = i.get("operStatus")
                db.add(iface)

        # Skip SNMP operations for now to avoid blocking
        # TODO: Implement async SNMP operations in separate threads
        print("🚀 Fast discovery mode: Skipping SNMP operations to avoid blocking")
        
        # Build topology from discovered data only (no SNMP neighbors)
        topo = build_topology(devices=devices, forwarding_tables=[], neighbors=[])

        # Replace edges table
        db.query(Edge).delete()
        for e in topo.get("edges", []):
            edge = Edge(
                id=e.get("id"),
                src_device_id=e.get("from"),
                src_if_index=e.get("srcIfIndex") or 0,
                dst_device_id=e.get("to"),
                dst_if_index=e.get("dstIfIndex") or 0,
                link_type=e.get("linkType") or "unknown",
                vlan_tags=e.get("vlanTags") or [],
                confidence=e.get("confidence") or 100,
            )
            db.add(edge)

        db.commit()
        return topo


