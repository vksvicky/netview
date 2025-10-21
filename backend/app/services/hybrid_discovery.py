import asyncio
import ipaddress
import subprocess
import socket
import re
import json
import urllib.request
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import platform


class HybridDiscoveryService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get('timeout', 1)
        self.scan_networks = config.get('scan_networks', ['192.168.1.0/24'])
        self.oui_database = self._load_oui_database()
        
    def _load_oui_database(self) -> Dict[str, str]:
        """Load OUI (Organizationally Unique Identifier) database for MAC vendor lookup"""
        oui_db = {}
        
        # Try multiple methods to load OUI database
        try:
            # Method 1: Try to load from local file first
            oui_db = self._load_oui_from_file()
            if oui_db:
                print(f"Loaded {len(oui_db)} OUI entries from local file")
                return oui_db
        except Exception as e:
            print(f"Failed to load OUI from file: {e}")
        
        try:
            # Method 2: Try to load from online API
            oui_db = self._load_oui_from_api()
            if oui_db:
                print(f"Loaded {len(oui_db)} OUI entries from API")
                return oui_db
        except Exception as e:
            print(f"Failed to load OUI from API: {e}")
        
        # Method 3: Fallback to minimal hardcoded database for common devices
        print("Using fallback OUI database")
        return self._get_fallback_oui_database()
    
    def _load_oui_from_file(self) -> Dict[str, str]:
        """Load OUI database from local file"""
        import os
        oui_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'oui_database.json')
        
        if os.path.exists(oui_file):
            with open(oui_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_oui_from_api(self) -> Dict[str, str]:
        """Load OUI database from online API"""
        try:
            # Use macvendors.com API (free tier)
            # Note: This is a simple implementation, in production you'd want proper rate limiting
            url = "https://api.macvendors.com/"
            
            # For now, return empty dict to avoid API calls during discovery
            # In production, you could implement a caching mechanism
            return {}
        except Exception as e:
            print(f"API OUI loading failed: {e}")
            return {}
    
    def _get_fallback_oui_database(self) -> Dict[str, str]:
        """Fallback OUI database for common devices"""
        return {
            # Virtualization
            "00:50:56": "VMware",
            "08:00:27": "VirtualBox", 
            "52:54:00": "QEMU",
            "00:0c:29": "VMware",
            "00:1c:42": "Parallels",
            "00:15:5d": "Microsoft",
            "00:16:3e": "Xen",
            
            # Major manufacturers
            "00:1b:21": "Intel",
            "00:1f:5b": "Apple",
            "00:23:12": "Apple",
            "00:25:00": "Apple",
            "00:26:bb": "Apple",
            "00:26:4a": "Apple",
            "00:26:b0": "Apple",
            "00:26:08": "Apple",
            "00:25:4b": "Apple",
            "00:25:bc": "Apple",
            "00:24:36": "Apple",
            "00:23:df": "Apple",
            "00:23:6c": "Apple",
            "00:22:41": "Apple",
            "00:21:e9": "Apple",
            "00:21:4a": "Apple",
            "00:20:af": "Apple",
            "00:1f:f3": "Apple",
            "00:1e:52": "Apple",
            "00:1d:4f": "Apple",
            "00:1b:63": "Apple",
            "00:1a:70": "Apple",
            "00:19:e3": "Apple",
            "00:18:65": "Apple",
            "00:17:f2": "Apple",
            "00:16:cb": "Apple",
            "00:15:99": "Apple",
            "00:14:51": "Apple",
            "00:13:83": "Apple",
            "00:12:fb": "Apple",
            "00:11:24": "Apple",
            "00:0f:b5": "Apple",
            "00:0e:35": "Apple",
            "00:0d:93": "Apple",
            "00:0c:41": "Apple",
            "00:0b:6b": "Apple",
            "00:0a:95": "Apple",
            "00:09:f3": "Apple",
            "00:08:74": "Apple",
            "00:07:e9": "Apple",
            "00:06:1b": "Apple",
            "00:05:02": "Apple",
            "00:03:93": "Apple",
            "00:02:2d": "Apple",
            "00:00:0a": "Apple",
            
            # Network equipment
            "00:04:96": "Cisco",
            "00:05:31": "Cisco",
            "00:05:32": "Cisco",
            "00:05:33": "Cisco",
            "00:05:5e": "Cisco",
            "00:05:73": "Cisco",
            "00:05:74": "Cisco",
            "00:05:75": "Cisco",
            "00:05:76": "Cisco",
            "00:05:77": "Cisco",
            "00:05:78": "Cisco",
            "00:05:79": "Cisco",
            "00:05:7a": "Cisco",
            "00:05:7b": "Cisco",
            "00:05:7c": "Cisco",
            "00:05:7d": "Cisco",
            "00:05:7e": "Cisco",
            "00:05:7f": "Cisco",
            "00:05:80": "Cisco",
            "00:05:81": "Cisco",
            "00:05:82": "Cisco",
            "00:05:83": "Cisco",
            "00:05:84": "Cisco",
            "00:05:85": "Cisco",
            "00:05:86": "Cisco",
            "00:05:87": "Cisco",
            "00:05:88": "Cisco",
            "00:05:89": "Cisco",
            "00:05:8a": "Cisco",
            "00:05:8b": "Cisco",
            "00:05:8c": "Cisco",
            "00:05:8d": "Cisco",
            "00:05:8e": "Cisco",
            "00:05:8f": "Cisco",
            "00:05:90": "Cisco",
            "00:05:91": "Cisco",
            "00:05:92": "Cisco",
            "00:05:93": "Cisco",
            "00:05:94": "Cisco",
            "00:05:95": "Cisco",
            "00:05:96": "Cisco",
            "00:05:97": "Cisco",
            "00:05:98": "Cisco",
            "00:05:99": "Cisco",
            "00:05:9a": "Cisco",
            "00:05:9b": "Cisco",
            "00:05:9c": "Cisco",
            "00:05:9d": "Cisco",
            "00:05:9e": "Cisco",
            "00:05:9f": "Cisco",
            "00:05:a0": "Cisco",
            "00:05:a1": "Cisco",
            "00:05:a2": "Cisco",
            "00:05:a3": "Cisco",
            "00:05:a4": "Cisco",
            "00:05:a5": "Cisco",
            "00:05:a6": "Cisco",
            "00:05:a7": "Cisco",
            "00:05:a8": "Cisco",
            "00:05:a9": "Cisco",
            "00:05:aa": "Cisco",
            "00:05:ab": "Cisco",
            "00:05:ac": "Cisco",
            "00:05:ad": "Cisco",
            "00:05:ae": "Cisco",
            "00:05:af": "Cisco",
            "00:05:b0": "Cisco",
            "00:05:b1": "Cisco",
            "00:05:b2": "Cisco",
            "00:05:b3": "Cisco",
            "00:05:b4": "Cisco",
            "00:05:b5": "Cisco",
            "00:05:b6": "Cisco",
            "00:05:b7": "Cisco",
            "00:05:b8": "Cisco",
            "00:05:b9": "Cisco",
            "00:05:ba": "Cisco",
            "00:05:bb": "Cisco",
            "00:05:bc": "Cisco",
            "00:05:bd": "Cisco",
            "00:05:be": "Cisco",
            "00:05:bf": "Cisco",
            "00:05:c0": "Cisco",
            "00:05:c1": "Cisco",
            "00:05:c2": "Cisco",
            "00:05:c3": "Cisco",
            "00:05:c4": "Cisco",
            "00:05:c5": "Cisco",
            "00:05:c6": "Cisco",
            "00:05:c7": "Cisco",
            "00:05:c8": "Cisco",
            "00:05:c9": "Cisco",
            "00:05:ca": "Cisco",
            "00:05:cb": "Cisco",
            "00:05:cc": "Cisco",
            "00:05:cd": "Cisco",
            "00:05:ce": "Cisco",
            "00:05:cf": "Cisco",
            "00:05:d0": "Cisco",
            "00:05:d1": "Cisco",
            "00:05:d2": "Cisco",
            "00:05:d3": "Cisco",
            "00:05:d4": "Cisco",
            "00:05:d5": "Cisco",
            "00:05:d6": "Cisco",
            "00:05:d7": "Cisco",
            "00:05:d8": "Cisco",
            "00:05:d9": "Cisco",
            "00:05:da": "Cisco",
            "00:05:db": "Cisco",
            "00:05:dc": "Cisco",
            "00:05:dd": "Cisco",
            "00:05:de": "Cisco",
            "00:05:df": "Cisco",
            "00:05:e0": "Cisco",
            "00:05:e1": "Cisco",
            "00:05:e2": "Cisco",
            "00:05:e3": "Cisco",
            "00:05:e4": "Cisco",
            "00:05:e5": "Cisco",
            "00:05:e6": "Cisco",
            "00:05:e7": "Cisco",
            "00:05:e8": "Cisco",
            "00:05:e9": "Cisco",
            "00:05:ea": "Cisco",
            "00:05:eb": "Cisco",
            "00:05:ec": "Cisco",
            "00:05:ed": "Cisco",
            "00:05:ee": "Cisco",
            "00:05:ef": "Cisco",
            "00:05:f0": "Cisco",
            "00:05:f1": "Cisco",
            "00:05:f2": "Cisco",
            "00:05:f3": "Cisco",
            "00:05:f4": "Cisco",
            "00:05:f5": "Cisco",
            "00:05:f6": "Cisco",
            "00:05:f7": "Cisco",
            "00:05:f8": "Cisco",
            "00:05:f9": "Cisco",
            "00:05:fa": "Cisco",
            "00:05:fb": "Cisco",
            "00:05:fc": "Cisco",
            "00:05:fd": "Cisco",
            "00:05:fe": "Cisco",
            "00:05:ff": "Cisco",
            
            # Other common manufacturers
            "00:50:56": "VMware",
            "00:0c:29": "VMware",
            "00:1c:42": "Parallels",
            "00:15:5d": "Microsoft",
            "00:16:3e": "Xen",
            "00:1b:21": "Intel",
            "00:1f:5b": "Apple",
            "00:23:12": "Apple",
            "00:25:00": "Apple",
            "00:26:bb": "Apple",
            "00:26:4a": "Apple",
            "00:26:b0": "Apple",
            "00:26:08": "Apple",
            "00:25:4b": "Apple",
            "00:25:bc": "Apple",
            "00:24:36": "Apple",
            "00:23:df": "Apple",
            "00:23:6c": "Apple",
            "00:22:41": "Apple",
            "00:21:e9": "Apple",
            "00:21:4a": "Apple",
            "00:20:af": "Apple",
            "00:1f:f3": "Apple",
            "00:1e:52": "Apple",
            "00:1d:4f": "Apple",
            "00:1b:63": "Apple",
            "00:1a:70": "Apple",
            "00:19:e3": "Apple",
            "00:18:65": "Apple",
            "00:17:f2": "Apple",
            "00:16:cb": "Apple",
            "00:15:99": "Apple",
            "00:14:51": "Apple",
            "00:13:83": "Apple",
            "00:12:fb": "Apple",
            "00:11:24": "Apple",
            "00:0f:b5": "Apple",
            "00:0e:35": "Apple",
            "00:0d:93": "Apple",
            "00:0c:41": "Apple",
            "00:0b:6b": "Apple",
            "00:0a:95": "Apple",
            "00:09:f3": "Apple",
            "00:08:74": "Apple",
            "00:07:e9": "Apple",
            "00:06:1b": "Apple",
            "00:05:02": "Apple",
            "00:03:93": "Apple",
            "00:02:2d": "Apple",
            "00:00:0a": "Apple"
        }
    
    def _get_vendor_from_mac(self, mac: str) -> str:
        """Get vendor name from MAC address using OUI database"""
        if not mac or len(mac) < 8:
            return "Unknown"
        
        # Normalize MAC address format
        mac = mac.replace('-', ':').replace('.', ':').upper()
        oui = ':'.join(mac.split(':')[:3])
        
        return self.oui_database.get(oui, "Unknown")
    
    def _discover_upnp_devices(self) -> List[Dict[str, Any]]:
        """Discover UPNP devices on the network"""
        devices = []
        try:
            import socket
            import struct
            
            # Create UDP socket for UPNP discovery
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            
            # UPNP M-SEARCH message
            msg = (
                "M-SEARCH * HTTP/1.1\r\n"
                "HOST: 239.255.255.250:1900\r\n"
                "MAN: \"ssdp:discover\"\r\n"
                "ST: upnp:rootdevice\r\n"
                "MX: 3\r\n\r\n"
            )
            
            # Send M-SEARCH to UPNP multicast address
            sock.sendto(msg.encode(), ("239.255.255.250", 1900))
            
            # Listen for responses
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < 3:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = data.decode('utf-8', errors='ignore')
                    
                    # Parse UPNP response
                    if 'HTTP/1.1 200 OK' in response:
                        device_info = self._parse_upnp_response(response, addr[0])
                        if device_info:
                            devices.append(device_info)
                except socket.timeout:
                    break
                except Exception as e:
                    print(f"UPNP discovery error: {e}")
                    break
            
            sock.close()
            
        except Exception as e:
            print(f"UPNP discovery failed: {e}")
        
        return devices
    
    def _parse_upnp_response(self, response: str, ip: str) -> Optional[Dict[str, Any]]:
        """Parse UPNP response to extract device information"""
        try:
            lines = response.split('\n')
            device_info = {
                'ip': ip,
                'hostname': ip,
                'vendor': 'Unknown',
                'model': 'Unknown',
                'type': 'upnp_device',
                'status': 'up'
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('SERVER:'):
                    server_info = line.split(':', 1)[1].strip()
                    device_info['model'] = server_info
                    # Try to extract vendor from server string
                    if 'Apple' in server_info:
                        device_info['vendor'] = 'Apple'
                    elif 'Samsung' in server_info:
                        device_info['vendor'] = 'Samsung'
                    elif 'LG' in server_info:
                        device_info['vendor'] = 'LG'
                    elif 'Sony' in server_info:
                        device_info['vendor'] = 'Sony'
                    elif 'Microsoft' in server_info:
                        device_info['vendor'] = 'Microsoft'
                elif line.startswith('LOCATION:'):
                    location = line.split(':', 1)[1].strip()
                    device_info['upnp_location'] = location
            
            return device_info
        except Exception as e:
            print(f"Error parsing UPNP response: {e}")
            return None
        
    def _get_arp_table(self) -> List[Dict[str, str]]:
        """Get ARP table to find devices on the network"""
        devices = []
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Parse ARP output: "hostname (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on en0"
                    for line in result.stdout.split('\n'):
                        if '(' in line and ')' in line:
                            match = re.search(r'\(([0-9.]+)\) at ([0-9a-fA-F:]+)', line)
                            if match:
                                ip = match.group(1)
                                mac = match.group(2)
                                hostname_match = re.search(r'^([^(]+)', line)
                                hostname = hostname_match.group(1).strip() if hostname_match else ip
                                devices.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'hostname': hostname,
                                    'type': 'arp'
                                })
            elif platform.system() == "Linux":
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '(' in line and ')' in line:
                            match = re.search(r'\(([0-9.]+)\) at ([0-9a-fA-F:]+)', line)
                            if match:
                                ip = match.group(1)
                                mac = match.group(2)
                                hostname_match = re.search(r'^([^(]+)', line)
                                hostname = hostname_match.group(1).strip() if hostname_match else ip
                                devices.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'hostname': hostname,
                                    'type': 'arp'
                                })
        except Exception as e:
            print(f"Error getting ARP table: {e}")
        return devices

    def _ping_host(self, ip: str) -> bool:
        """Ping a host to check if it's alive"""
        try:
            if platform.system() == "Darwin" or platform.system() == "Linux":
                result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                      capture_output=True, timeout=3)
                return result.returncode == 0
            else:  # Windows
                result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip], 
                                      capture_output=True, timeout=3)
                return result.returncode == 0
        except:
            return False

    def _get_device_info(self, ip: str) -> Dict[str, str]:
        """Get device information using multiple methods"""
        device_info = {
            'ip': ip,
            'hostname': ip,
            'vendor': 'Unknown',
            'model': 'Unknown',
            'type': 'unknown',
            'status': 'up'
        }
        
        # Try to get hostname via reverse DNS
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            device_info['hostname'] = hostname
        except:
            pass
        
        # Try to determine device type based on hostname patterns
        hostname_lower = device_info['hostname'].lower()
        if any(keyword in hostname_lower for keyword in ['router', 'gateway', 'ap', 'access-point']):
            device_info['type'] = 'router'
            device_info['vendor'] = 'Router'
        elif any(keyword in hostname_lower for keyword in ['switch', 'sw']):
            device_info['type'] = 'switch'
            device_info['vendor'] = 'Switch'
        elif any(keyword in hostname_lower for keyword in ['printer', 'print']):
            device_info['type'] = 'printer'
            device_info['vendor'] = 'Printer'
        elif any(keyword in hostname_lower for keyword in ['nas', 'storage', 'server']):
            device_info['type'] = 'server'
            device_info['vendor'] = 'Server'
        elif any(keyword in hostname_lower for keyword in ['iphone', 'ipad', 'android', 'phone']):
            device_info['type'] = 'mobile'
            device_info['vendor'] = 'Mobile'
        elif any(keyword in hostname_lower for keyword in ['laptop', 'desktop', 'pc', 'mac']):
            device_info['type'] = 'computer'
            device_info['vendor'] = 'Computer'
        else:
            device_info['type'] = 'device'
            device_info['vendor'] = 'Unknown'
        
        return device_info

    def _scan_network_range(self, network: str) -> List[Dict[str, Any]]:
        """Scan a network range for active devices"""
        devices = []
        try:
            net = ipaddress.ip_network(network, strict=False)
            # Limit to first 10 IPs to avoid long scans
            ips_to_scan = list(net.hosts())[:10]
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                # Ping all IPs in parallel
                futures = {executor.submit(self._ping_host, str(ip)): str(ip) for ip in ips_to_scan}
                
                for future in futures:
                    ip = futures[future]
                    if future.result():  # If ping successful
                        device_info = self._get_device_info(ip)
                        devices.append(device_info)
        except Exception as e:
            print(f"Error scanning network {network}: {e}")
        
        return devices

    async def discover_devices(self) -> List[Dict[str, Any]]:
        """Hybrid device discovery using multiple methods"""
        all_devices = []
        device_ips = set()  # To avoid duplicates
        
        print("Starting advanced hybrid device discovery...")
        
        # Method 1: ARP table (fastest, most reliable for local network)
        print("1. Checking ARP table...")
        arp_devices = self._get_arp_table()
        for device in arp_devices:
            if device['ip'] not in device_ips:
                device_ips.add(device['ip'])
                vendor = self._get_vendor_from_mac(device['mac'])
                device_info = self._get_device_info(device['ip'])
                
                all_devices.append({
                    'id': device['ip'],
                    'hostname': device['hostname'],
                    'mgmtIp': device['ip'],
                    'vendor': vendor if vendor != "Unknown" else device_info['vendor'],
                    'model': device_info['model'],
                    'status': 'up',
                    'type': device_info['type'],
                    'mac': device['mac'],
                    'discovery_method': 'arp'
                })
        
        print(f"Found {len(arp_devices)} devices via ARP table")
        
        # Method 2: UPNP discovery (for smart devices) - async to avoid blocking
        print("2. Discovering UPNP devices...")
        try:
            upnp_devices = self._discover_upnp_devices()
            for device in upnp_devices:
                if device['ip'] not in device_ips:
                    device_ips.add(device['ip'])
                    all_devices.append({
                        'id': device['ip'],
                        'hostname': device['hostname'],
                        'mgmtIp': device['ip'],
                        'vendor': device['vendor'],
                        'model': device['model'],
                        'status': device['status'],
                        'type': device['type'],
                        'discovery_method': 'upnp'
                    })
            print(f"Found {len(upnp_devices)} devices via UPNP")
        except Exception as e:
            print(f"UPNP discovery failed: {e}")
        
        # Skip network scanning for now to make it faster
        # Method 3: Quick network scanning for additional devices (limited)
        # print("3. Quick network scan for additional devices...")
        # # Only scan the first network range and limit to 10 IPs for speed
        # if self.scan_networks:
        #     network = self.scan_networks[0]
        #     print(f"Quick scan of {network}...")
        #     scanned_devices = self._scan_network_range(network)
        #     for device in scanned_devices:
        #         if device['ip'] not in device_ips:
        #             device_ips.add(device['ip'])
        #             all_devices.append({
        #                 'id': device['ip'],
        #                 'hostname': device['hostname'],
        #                 'mgmtIp': device['ip'],
        #                 'vendor': device['vendor'],
        #                 'model': device['model'],
        #                 'status': device['status'],
        #                 'type': device['type'],
        #                 'discovery_method': 'ping'
        #             })
        
        print(f"Total devices discovered: {len(all_devices)}")
        return all_devices
