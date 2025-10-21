from typing import Dict, List


def build_topology(devices: List[dict], forwarding_tables: List[dict], neighbors: List[dict]) -> Dict[str, List[dict]]:
    """Build network topology from discovered devices and LLDP neighbors"""
    edges = []
    
    # Create device lookup by IP
    device_map = {device['mgmtIp']: device for device in devices}
    
    # Process LLDP neighbors to create edges
    for neighbor in neighbors:
        local_device_ip = neighbor.get('localDevice')
        local_port = neighbor.get('localPort')
        neighbor_chassis = neighbor.get('chassisId', '')
        neighbor_port = neighbor.get('portId', '')
        neighbor_sysname = neighbor.get('sysName', '')
        
        if not local_device_ip or not local_port:
            continue
            
        # Try to find the neighbor device by various methods
        neighbor_device_ip = None
        
        # Method 1: Look for device with matching sysName
        if neighbor_sysname:
            for device in devices:
                if device.get('hostname') == neighbor_sysname:
                    neighbor_device_ip = device['mgmtIp']
                    break
        
        # Method 2: Look for device with matching chassis ID (MAC address)
        if not neighbor_device_ip and neighbor_chassis:
            for device in devices:
                # Check if any interface MAC matches the chassis ID
                for interface in device.get('interfaces', []):
                    if interface.get('mac', '').upper() == neighbor_chassis.upper():
                        neighbor_device_ip = device['mgmtIp']
                        break
                if neighbor_device_ip:
                    break
        
        # Create edge if we found both devices
        if neighbor_device_ip and neighbor_device_ip != local_device_ip:
            edge_id = f"{local_device_ip}:{local_port}-{neighbor_device_ip}:{neighbor_port}"
            edge = {
                "id": edge_id,
                "from": local_device_ip,
                "to": neighbor_device_ip,
                "srcIfIndex": local_port,
                "dstIfIndex": neighbor_port,
                "linkType": "lldp",
                "vlanTags": [],
                "confidence": 90  # High confidence for LLDP
            }
            edges.append(edge)
    
    # Remove duplicate edges (bidirectional links)
    unique_edges = []
    seen_edges = set()
    
    for edge in edges:
        # Create a normalized key for bidirectional links
        key1 = f"{edge['from']}-{edge['to']}"
        key2 = f"{edge['to']}-{edge['from']}"
        
        if key1 not in seen_edges and key2 not in seen_edges:
            unique_edges.append(edge)
            seen_edges.add(key1)
            seen_edges.add(key2)
    
    return {"nodes": devices, "edges": unique_edges}


