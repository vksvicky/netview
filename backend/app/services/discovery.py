from typing import Any, Dict, List
from sqlalchemy.orm import Session

from ..models import Device, Interface, Edge
from .snmp import SnmpClient
from .fast_discovery import FastDiscoveryService
from .topology_builder import build_topology


class DiscoveryService:
    def __init__(self, snmp_client: SnmpClient, fast_discovery: FastDiscoveryService):
        self.snmp_client = snmp_client
        self.fast_discovery = fast_discovery

    async def run_discovery(self, db: Session) -> Dict[str, List[dict]]:
        # Use fast discovery (ARP table only) for speed
        devices: List[Dict[str, Any]] = await self.fast_discovery.discover_devices()

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
            db.add(device)
            device_map[device_id] = device

        # Upsert interfaces if provided
        for d in devices:
            device_id = d.get("id") or d.get("mgmtIp")
            ifaces = d.get("interfaces", [])
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


