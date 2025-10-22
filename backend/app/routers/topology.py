from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Device, Interface, Edge
from ..services.discovery import DiscoveryService
from ..services.snmp import SnmpClient
from ..services.fast_discovery import FastDiscoveryService

router = APIRouter()


@router.get("")
@router.head("")
def get_topology(db: Session = Depends(get_db)) -> dict:
    # Skip router detection for now to avoid blocking UI
    # _add_missing_router(db)
    
    devices = db.query(Device).all()
    edges = db.query(Edge).all()

    # Identify router/gateway device
    router_device = None
    other_devices = []
    
    for d in devices:
        # Get MAC address from first interface
        mac_address = "Unknown"
        if d.interfaces:
            for interface in d.interfaces:
                if interface.mac:
                    mac_address = interface.mac
                    break
        
        device_info = {
            "id": d.id,
            "label": d.hostname or d.id,
            "title": d.mgmt_ip,
            "group": d.vendor or "device",
            "mac": mac_address,
            "model": d.model or "Unknown",
            "status": d.status or "up",
            "lastSeen": d.last_seen.isoformat() if d.last_seen else None,
            "connection_type": d.connection_type or 'Unknown',
            "ip_version": d.ip_version or 'IPv4',
            "device_name": d.device_name or d.hostname or d.id
        }
        
        # Check if this is likely a router/gateway
        if _is_router_device(d):
            router_device = device_info
        else:
            other_devices.append(device_info)
    
    # Put router first, then other devices
    node_items = []
    if router_device:
        node_items.append(router_device)
    node_items.extend(other_devices)
    
    edge_items = [
        {
            "id": e.id,
            "from": e.src_device_id,
            "to": e.dst_device_id,
        }
        for e in edges
    ]
    return {"nodes": node_items, "edges": edge_items}


def _is_router_device(device: Device) -> bool:
    """Identify if a device is likely a router/gateway"""
    import ipaddress
    
    # Check if IP is a common gateway IP (usually .1 in the subnet)
    try:
        ip = ipaddress.IPv4Address(device.mgmt_ip)
        # Check if it's a .1 address (common gateway pattern)
        if str(ip).endswith('.1'):
            return True
    except (ipaddress.AddressValueError, ValueError):
        pass
    
    # Check vendor names that are commonly routers
    router_vendors = [
        'cisco', 'netgear', 'linksys', 'tp-link', 'd-link', 'asus', 
        'belkin', 'buffalo', 'zyxel', 'ubiquiti', 'mikrotik',
        'aruba', 'ruckus', 'meraki', 'fortinet', 'sonicwall'
    ]
    
    if device.vendor and device.vendor.lower() in router_vendors:
        return True
    
    # Check hostname patterns
    if device.hostname:
        hostname_lower = device.hostname.lower()
        router_patterns = ['router', 'gateway', 'ap-', 'wifi', 'wireless']
        if any(pattern in hostname_lower for pattern in router_patterns):
            return True
    
    return False

def _add_missing_router(db: Session) -> Device:
    """Add the router device if it's not discovered but should exist"""
    import ipaddress
    
    print("🔍 Checking for missing router...")
    
    # Check if we already have a router device
    existing_router = db.query(Device).filter(
        Device.mgmt_ip.like('%.1')
    ).first()
    
    if existing_router:
        print(f"✅ Router already exists: {existing_router.mgmt_ip}")
        return existing_router
    
    # Try to add common router IPs that might not be in ARP table
    common_router_ips = ['192.168.1.1', '192.168.0.1', '10.0.0.1', '172.16.0.1']
    print(f"🔍 Testing router IPs: {common_router_ips}")
    
    for router_ip in common_router_ips:
        print(f"🔍 Testing router IP: {router_ip}")
        
        # Check if this IP is already in the database
        existing_device = db.query(Device).filter(Device.mgmt_ip == router_ip).first()
        if existing_device:
            print(f"⚠️  Router {router_ip} already exists in database")
            continue
            
        # Try to ping the router to see if it exists
        try:
            import subprocess
            import platform
            
            print(f"🏓 Pinging {router_ip}...")
            
            # Use correct ping command for different platforms
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['ping', '-c', '1', '-W', '2000', router_ip], 
                                      capture_output=True, text=True, timeout=5)
            else:  # Linux
                result = subprocess.run(['ping', '-c', '1', '-W', '2', router_ip], 
                                      capture_output=True, text=True, timeout=5)
            
            print(f"🏓 Ping result for {router_ip}: returncode={result.returncode}")
            
            if result.returncode == 0:
                # Router is reachable, add it to database
                router_device = Device(
                    id=router_ip,
                    hostname=f"router-{router_ip.split('.')[-1]}",
                    mgmt_ip=router_ip,
                    vendor="Router",
                    model="Unknown Router",
                    status="up"
                )
                db.add(router_device)
                db.commit()
                print(f"✅ Added missing router: {router_ip}")
                return router_device
            else:
                print(f"❌ Router {router_ip} not reachable")
        except Exception as e:
            print(f"❌ Could not ping router {router_ip}: {e}")
            continue
    
    return None

@router.get("/network-status")
def get_network_status() -> dict:
    """Get current network connectivity status"""
    from ..config import settings
    fast_discovery = FastDiscoveryService(config=settings.snmp_config)
    # Always run a fresh connectivity check
    fast_discovery._check_network_connectivity()
    return fast_discovery.get_network_status()

@router.post("/discover")
async def trigger_discovery(db: Session = Depends(get_db), force_refresh: bool = False) -> dict:
    import asyncio
    from ..config import settings
    
    # Return immediately with current topology
    current_topology = get_topology(db)
    
    # Start discovery in background (non-blocking)
    async def background_discovery():
        try:
            print("🚀 Starting background discovery...")
            fast_discovery = FastDiscoveryService(config=settings.snmp_config)
            from ..services.discovery import DiscoveryService
            from ..services.snmp import SnmpClient
            snmp_client = SnmpClient(config=settings.snmp_config)
            svc = DiscoveryService(snmp_client, fast_discovery)
            await svc.run_discovery(db, force_refresh)
            print("✅ Background discovery completed")
        except Exception as e:
            print(f"❌ Background discovery failed: {e}")
    
    # Start background task
    asyncio.create_task(background_discovery())
    
    return {
        "status": "discovery_started",
        "message": "Discovery started in background. UI will update automatically.",
        "current_topology": current_topology
    }


