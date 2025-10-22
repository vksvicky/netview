import asyncio
import ipaddress
from typing import Any, Dict, List, Optional
import socket
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
import threading
from .oui_database import oui_db


class SnmpClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.community = config.get('community', 'public')
        self.timeout = config.get('timeout', 5)
        self.retries = config.get('retries', 1)
        # Try multiple SNMP communities
        self.communities = ['public', 'private', 'admin', 'snmp', 'read', 'write']
        # Thread pool for SNMP operations
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="snmp")
    
    def __del__(self):
        """Clean up thread pool when object is destroyed"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
    def _snmp_get(self, target: str, oid: str) -> Optional[str]:
        """Perform SNMP GET operation using snmpget command, trying multiple communities"""
        for community in self.communities:
            try:
                cmd = [
                    'snmpget', '-v2c', '-c', community,
                    '-t', str(self.timeout), '-r', str(self.retries),
                    target, oid
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 5)
                
                if result.returncode == 0:
                    # Parse output: "OID = TYPE: value"
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if '=' in line:
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                value = parts[1].strip()
                                # Remove type prefix (e.g., "STRING: " or "INTEGER: ")
                                if ':' in value:
                                    value = value.split(':', 1)[1].strip()
                                print(f"SNMP GET success for {target} with community '{community}'")
                                return value
                else:
                    # Only print error for the last community tried
                    if community == self.communities[-1]:
                        print(f"SNMP GET error for {target} with all communities: {result.stderr}")
            except subprocess.TimeoutExpired:
                # Only print timeout for the last community tried
                if community == self.communities[-1]:
                    print(f"SNMP GET timeout for {target} with all communities")
            except FileNotFoundError:
                print("snmpget command not found. Please install net-snmp tools.")
                return None
            except Exception as e:
                # Only print error for the last community tried
                if community == self.communities[-1]:
                    print(f"SNMP GET error for {target}: {e}")
        return None

    def _snmp_walk(self, target: str, oid: str) -> List[tuple]:
        """Perform SNMP WALK operation using snmpwalk command, trying multiple communities"""
        results = []
        for community in self.communities:
            try:
                cmd = [
                    'snmpwalk', '-v2c', '-c', community,
                    '-t', str(self.timeout), '-r', str(self.retries),
                    target, oid
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if '=' in line:
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                oid_part = parts[0].strip()
                                value_part = parts[1].strip()
                                # Remove type prefix (e.g., "STRING: " or "INTEGER: ")
                                if ':' in value_part:
                                    value_part = value_part.split(':', 1)[1].strip()
                                results.append((oid_part, value_part))
                    if results:  # If we got results, return them
                        print(f"SNMP WALK success for {target} with community '{community}'")
                        return results
                else:
                    # Only print error for the last community tried
                    if community == self.communities[-1]:
                        print(f"SNMP WALK error for {target} with all communities: {result.stderr}")
            except subprocess.TimeoutExpired:
                # Only print timeout for the last community tried
                if community == self.communities[-1]:
                    print(f"SNMP WALK timeout for {target} with all communities")
            except FileNotFoundError:
                print("snmpwalk command not found. Please install net-snmp tools.")
                return results
            except Exception as e:
                # Only print error for the last community tried
                if community == self.communities[-1]:
                    print(f"SNMP WALK error for {target}: {e}")
        return results

    def _get_system_info(self, target: str) -> Dict[str, str]:
        """Get system information from SNMP"""
        sys_descr = self._snmp_get(target, '1.3.6.1.2.1.1.1.0')  # sysDescr
        sys_name = self._snmp_get(target, '1.3.6.1.2.1.1.5.0')   # sysName
        sys_contact = self._snmp_get(target, '1.3.6.1.2.1.1.4.0') # sysContact
        sys_location = self._snmp_get(target, '1.3.6.1.2.1.1.6.0') # sysLocation
        
        # Try to get vendor from OUI database using MAC address
        vendor = "Unknown"
        try:
            # Get the first interface MAC address to determine vendor
            interfaces = self._get_interfaces(target)
            for interface in interfaces:
                if interface.get('mac') and interface['mac'] != '00:00:00:00:00:00':
                    vendor = oui_db.lookup_vendor(interface['mac'])
                    if vendor:
                        break
        except Exception as e:
            print(f"Error looking up vendor from OUI database: {e}")
        
        # Fallback to sysDescr parsing if OUI lookup failed
        if vendor == "Unknown" and sys_descr:
            if "cisco" in sys_descr.lower():
                vendor = "Cisco"
            elif "juniper" in sys_descr.lower():
                vendor = "Juniper"
            elif "hp" in sys_descr.lower() or "hewlett" in sys_descr.lower():
                vendor = "HP"
            elif "arista" in sys_descr.lower():
                vendor = "Arista"
        
        return {
            "sysDescr": sys_descr or "",
            "sysName": sys_name or target,
            "sysContact": sys_contact or "",
            "sysLocation": sys_location or "",
            "vendor": vendor
        }

    def _get_interfaces(self, target: str) -> List[Dict[str, Any]]:
        """Get interface information from IF-MIB"""
        interfaces = []
        
        # Walk ifTable
        if_table = self._snmp_walk(target, '1.3.6.1.2.1.2.2.1')
        
        # Group by interface index
        if_data = {}
        for oid, value in if_table:
            parts = oid.split('.')
            if_index = parts[-1]
            oid_type = '.'.join(parts[:-1])
            
            if if_index not in if_data:
                if_data[if_index] = {}
            
            # Map OIDs to interface properties
            if oid_type == '1.3.6.1.2.1.2.2.1.2':  # ifDescr
                if_data[if_index]['name'] = value
            elif oid_type == '1.3.6.1.2.1.2.2.1.3':  # ifType
                if_data[if_index]['type'] = value
            elif oid_type == '1.3.6.1.2.1.2.2.1.5':  # ifSpeed
                if_data[if_index]['speed'] = int(value) if value.isdigit() else 0
            elif oid_type == '1.3.6.1.2.1.2.2.1.7':  # ifAdminStatus
                if_data[if_index]['adminStatus'] = 'up' if value == '1' else 'down'
            elif oid_type == '1.3.6.1.2.1.2.2.1.8':  # ifOperStatus
                if_data[if_index]['operStatus'] = 'up' if value == '1' else 'down'
            elif oid_type == '1.3.6.1.2.1.2.2.1.6':  # ifPhysAddress
                if_data[if_index]['mac'] = value
        
        # Convert to list format
        for if_index, data in if_data.items():
            if data.get('name'):  # Only include interfaces with names
                interfaces.append({
                    "ifIndex": int(if_index),
                    "name": data.get('name', ''),
                    "type": data.get('type', ''),
                    "speed": data.get('speed', 0),
                    "adminStatus": data.get('adminStatus', 'unknown'),
                    "operStatus": data.get('operStatus', 'unknown'),
                    "mac": data.get('mac', '')
                })
        
        return interfaces

    def _get_lldp_neighbors(self, target: str) -> List[Dict[str, Any]]:
        """Get LLDP neighbor information"""
        neighbors = []
        
        # Walk lldpRemTable
        lldp_table = self._snmp_walk(target, '1.0.8802.1.1.2.1.4.1')
        
        # Group by neighbor index
        neighbor_data = {}
        for oid, value in lldp_table:
            parts = oid.split('.')
            if len(parts) < 2:
                continue
                
            neighbor_index = parts[-1]
            local_port = parts[-2]
            oid_type = '.'.join(parts[:-2])
            
            key = f"{local_port}.{neighbor_index}"
            if key not in neighbor_data:
                neighbor_data[key] = {'localPort': local_port, 'neighborIndex': neighbor_index}
            
            # Map OIDs to neighbor properties
            if oid_type == '1.0.8802.1.1.2.1.4.1.1.9':  # lldpRemChassisId
                neighbor_data[key]['chassisId'] = value
            elif oid_type == '1.0.8802.1.1.2.1.4.1.1.7':  # lldpRemPortId
                neighbor_data[key]['portId'] = value
            elif oid_type == '1.0.8802.1.1.2.1.4.1.1.8':  # lldpRemPortDesc
                neighbor_data[key]['portDesc'] = value
            elif oid_type == '1.0.8802.1.1.2.1.4.1.1.9':  # lldpRemSysName
                neighbor_data[key]['sysName'] = value
        
        # Convert to list format
        for key, data in neighbor_data.items():
            neighbors.append({
                "localPort": int(data['localPort']),
                "neighborIndex": int(data['neighborIndex']),
                "chassisId": data.get('chassisId', ''),
                "portId": data.get('portId', ''),
                "portDesc": data.get('portDesc', ''),
                "sysName": data.get('sysName', '')
            })
        
        return neighbors

    def _scan_network(self, network: str) -> List[str]:
        """Scan network for SNMP-enabled devices"""
        devices = []
        try:
            net = ipaddress.ip_network(network, strict=False)
            for ip in net.hosts():
                ip_str = str(ip)
                # Quick SNMP ping to check if device responds
                if self._snmp_get(ip_str, '1.3.6.1.2.1.1.1.0'):
                    devices.append(ip_str)
        except Exception as e:
            print(f"Network scan error: {e}")
        return devices

    def _add_demo_device(self) -> Dict[str, Any]:
        """Add a demo device for testing purposes"""
        return {
            "id": "demo-device",
            "hostname": "demo-switch-01",
            "mgmtIp": "192.168.1.100",
            "vendor": "Demo",
            "model": "Demo Switch v1.0",
            "status": "up",
            "interfaces": [
                {"ifIndex": 1, "name": "Gi0/1", "adminStatus": "up", "operStatus": "up", "speed": 1000},
                {"ifIndex": 2, "name": "Gi0/2", "adminStatus": "up", "operStatus": "up", "speed": 1000},
                {"ifIndex": 3, "name": "Gi0/3", "adminStatus": "down", "operStatus": "down", "speed": 1000},
            ]
        }

    async def discover_devices(self) -> List[Dict[str, Any]]:
        """Discover devices using SNMP"""
        devices = []
        
        # Get scan targets from config
        scan_networks = self.config.get('scan_networks', ['192.168.1.0/24', '10.0.0.0/24'])
        
        for network in scan_networks:
            print(f"Scanning network: {network}")
            found_ips = self._scan_network(network)
            
            for ip in found_ips:
                print(f"Found SNMP device: {ip}")
                system_info = self._get_system_info(ip)
                interfaces = self._get_interfaces(ip)
                
                device = {
                    "id": ip,
                    "hostname": system_info["sysName"],
                    "mgmtIp": ip,
                    "vendor": system_info["vendor"],
                    "model": system_info["sysDescr"][:50] if system_info["sysDescr"] else "Unknown",
                    "status": "up",
                    "interfaces": interfaces
                }
                devices.append(device)
        
        print(f"SNMP discovery completed: found {len(devices)} devices")
        if len(devices) == 0:
            print("No SNMP-enabled devices found. Make sure SNMP is enabled on your network devices.")
        return devices

    async def poll_interface_counters(self, device_id: str) -> List[Dict[str, Any]]:
        """Poll interface counters from IF-MIB"""
        counters = []
        
        # Walk ifInOctets, ifOutOctets, ifInErrors, ifOutErrors, ifInDiscards, ifOutDiscards
        counter_oids = {
            'inOctets': '1.3.6.1.2.1.2.2.1.10',    # ifInOctets
            'outOctets': '1.3.6.1.2.1.2.2.1.16',   # ifOutOctets
            'inErrors': '1.3.6.1.2.1.2.2.1.14',    # ifInErrors
            'outErrors': '1.3.6.1.2.1.2.2.1.20',   # ifOutErrors
            'inDiscards': '1.3.6.1.2.1.2.2.1.13',  # ifInDiscards
            'outDiscards': '1.3.6.1.2.1.2.2.1.19'  # ifOutDiscards
        }
        
        counter_data = {}
        for counter_name, oid in counter_oids.items():
            walk_results = self._snmp_walk(device_id, oid)
            for oid_str, value in walk_results:
                if_index = oid_str.split('.')[-1]
                if if_index not in counter_data:
                    counter_data[if_index] = {}
                counter_data[if_index][counter_name] = int(value) if value.isdigit() else 0
        
        # Convert to list format
        for if_index, data in counter_data.items():
            counters.append({
                "ifIndex": int(if_index),
                "inOctets": data.get('inOctets', 0),
                "outOctets": data.get('outOctets', 0),
                "inErrors": data.get('inErrors', 0),
                "outErrors": data.get('outErrors', 0),
                "inDiscards": data.get('inDiscards', 0),
                "outDiscards": data.get('outDiscards', 0)
            })
        
        return counters


