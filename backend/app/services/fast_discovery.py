import subprocess
import socket
import re
import json
import os
from typing import Any, Dict, List, Optional
import platform
import asyncio


class FastDiscoveryService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.oui_database = self._load_oui_database()
        self.network_status = {"connected": True, "last_check": None, "error": None}
        
    def _load_oui_database(self) -> Dict[str, str]:
        """Load OUI database from local file"""
        try:
            oui_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'oui_database.json')
            if os.path.exists(oui_file):
                with open(oui_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load OUI database: {e}")
        
        # Fallback minimal database
        return {
            "00:50:56": "VMware",
            "08:00:27": "VirtualBox", 
            "52:54:00": "QEMU",
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
    
    def _scan_network_async(self) -> List[Dict[str, str]]:
        """Scan the network to find devices not in ARP table (threaded)"""
        import concurrent.futures
        import threading
        
        devices = []
        try:
            # Get the current network interface IP to determine subnet
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Find the main network interface IP
                    for line in result.stdout.split('\n'):
                        if 'inet ' in line and not line.strip().startswith('inet 127.0.0.1'):
                            # Extract IP and netmask
                            parts = line.strip().split()
                            ip = None
                            netmask = None
                            for i, part in enumerate(parts):
                                if part == 'inet':
                                    ip = parts[i + 1]
                                elif part == 'netmask':
                                    netmask = parts[i + 1]
                            
                            if ip and netmask:
                                # Convert netmask to CIDR notation
                                if netmask.startswith('0x'):
                                    # Hex netmask
                                    netmask_int = int(netmask, 16)
                                    cidr = bin(netmask_int).count('1')
                                else:
                                    # Decimal netmask
                                    cidr = sum(bin(int(x)).count('1') for x in netmask.split('.'))
                                
                                # Calculate network range
                                ip_parts = ip.split('.')
                                if len(ip_parts) == 4:
                                    network = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/{cidr}"
                                    print(f"Scanning network: {network}")
                                    
                                    # Scan the network (limited to /24 for speed) using threads
                                    if cidr >= 24:
                                        base_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
                                        
                                        # Use ThreadPoolExecutor for concurrent pings
                                        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                                            # Submit ping tasks
                                            future_to_ip = {
                                                executor.submit(self._ping_host, f"{base_ip}.{i}"): f"{base_ip}.{i}"
                                                for i in range(1, 255)  # Skip .0 and .255
                                            }
                                            
                                            # Collect results with timeout
                                            for future in concurrent.futures.as_completed(future_to_ip, timeout=10):
                                                ip = future_to_ip[future]
                                                try:
                                                    if future.result():
                                                        devices.append({
                                                            'ip': ip,
                                                            'mac': 'Unknown',  # We don't have MAC from ping
                                                            'hostname': ip,
                                                            'type': 'scan'
                                                        })
                                                except Exception as e:
                                                    print(f"Error pinging {ip}: {e}")
                                    break
        except Exception as e:
            print(f"Error scanning network: {e}")
        
        return devices

    def _ping_host(self, ip: str) -> bool:
        """Ping a host to check if it's alive"""
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['ping', '-c', '1', '-W', '1000', ip], 
                                      capture_output=True, text=True, timeout=2)
            else:  # Linux
                result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                      capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    def _get_arp_table(self) -> List[Dict[str, str]]:
        """Get ARP table to find devices on the network"""
        devices = []
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Parse ARP output: "? (192.168.1.1) at 28:80:88:34:f1:79 on en0 ifscope [ethernet]"
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if not line or '(incomplete)' in line or 'broadcast' in line.lower() or 'mcast' in line.lower():
                            continue
                            
                        # Match pattern: "? (192.168.1.1) at 28:80:88:34:f1:79 on en0 ifscope [ethernet]"
                        match = re.search(r'\(([0-9.]+)\) at ([0-9a-fA-F:]+)', line)
                        if match:
                            ip = match.group(1)
                            mac = match.group(2)
                            
                            # Skip broadcast and multicast addresses
                            if ip.startswith('224.') or ip.startswith('239.') or ip == '255.255.255.255':
                                continue
                                
                            # Extract hostname (everything before the first parenthesis)
                            hostname_match = re.search(r'^([^(]+)', line)
                            hostname = hostname_match.group(1).strip() if hostname_match else ip
                            
                            # Clean up hostname
                            if hostname == '?' or hostname == '':
                                hostname = ip
                            
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
                        line = line.strip()
                        if not line or '(incomplete)' in line or 'broadcast' in line.lower() or 'mcast' in line.lower():
                            continue
                            
                        match = re.search(r'\(([0-9.]+)\) at ([0-9a-fA-F:]+)', line)
                        if match:
                            ip = match.group(1)
                            mac = match.group(2)
                            
                            # Skip broadcast and multicast addresses
                            if ip.startswith('224.') or ip.startswith('239.') or ip == '255.255.255.255':
                                continue
                                
                            hostname_match = re.search(r'^([^(]+)', line)
                            hostname = hostname_match.group(1).strip() if hostname_match else ip
                            
                            if hostname == '?' or hostname == '':
                                hostname = ip
                            
                            devices.append({
                                'ip': ip,
                                'mac': mac,
                                'hostname': hostname,
                                'type': 'arp'
                            })
        except Exception as e:
            print(f"Error getting ARP table: {e}")
        return devices

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

    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check if the network is connected by testing multiple methods"""
        import time
        
        connectivity_tests = []
        
        # Test 1: Check if we can resolve external DNS (most reliable test)
        try:
            socket.gethostbyname('google.com')
            connectivity_tests.append(("DNS Resolution", True, None))
        except Exception as e:
            connectivity_tests.append(("DNS Resolution", False, str(e)))
        
        # Test 1b: Try to resolve another external domain
        try:
            socket.gethostbyname('cloudflare.com')
            connectivity_tests.append(("DNS Resolution 2", True, None))
        except Exception as e:
            connectivity_tests.append(("DNS Resolution 2", False, str(e)))
        
        # Test 2: Check if we can reach external internet (critical test)
        try:
            # Try to connect to a reliable external service
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # Very short timeout for faster detection
            result = sock.connect_ex(('8.8.8.8', 53))  # Google DNS
            sock.close()
            if result == 0:
                connectivity_tests.append(("Internet Access", True, "Can reach 8.8.8.8"))
            else:
                connectivity_tests.append(("Internet Access", False, "Cannot reach 8.8.8.8"))
        except Exception as e:
            connectivity_tests.append(("Internet Access", False, str(e)))
        
        # Test 3: Check if we can reach another external service
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('1.1.1.1', 53))  # Cloudflare DNS
            sock.close()
            if result == 0:
                connectivity_tests.append(("External Service", True, "Can reach 1.1.1.1"))
            else:
                connectivity_tests.append(("External Service", False, "Cannot reach 1.1.1.1"))
        except Exception as e:
            connectivity_tests.append(("External Service", False, str(e)))
        
        # Test 3b: Try to reach a web server (HTTP)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('httpbin.org', 80))  # HTTP service
            sock.close()
            if result == 0:
                connectivity_tests.append(("HTTP Service", True, "Can reach httpbin.org"))
            else:
                connectivity_tests.append(("HTTP Service", False, "Cannot reach httpbin.org"))
        except Exception as e:
            connectivity_tests.append(("HTTP Service", False, str(e)))
        
        # Test 4: Check if we have active network interfaces (but don't rely on this alone)
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    # Look for active interfaces with IP addresses
                    has_active_interface = False
                    for line in result.stdout.split('\n'):
                        if 'inet ' in line and not line.strip().startswith('inet 127.0.0.1'):  # Exclude localhost
                            has_active_interface = True
                            break
                    if has_active_interface:
                        connectivity_tests.append(("Network Interfaces", True, "Active interfaces found"))
                    else:
                        connectivity_tests.append(("Network Interfaces", False, "No active interfaces"))
                else:
                    connectivity_tests.append(("Network Interfaces", False, "ifconfig failed"))
            else:  # Linux
                result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    has_active_interface = False
                    for line in result.stdout.split('\n'):
                        if 'inet ' in line and not '127.0.0.1' in line:  # Exclude localhost
                            has_active_interface = True
                            break
                    if has_active_interface:
                        connectivity_tests.append(("Network Interfaces", True, "Active interfaces found"))
                    else:
                        connectivity_tests.append(("Network Interfaces", False, "No active interfaces"))
                else:
                    connectivity_tests.append(("Network Interfaces", False, "ip addr failed"))
        except Exception as e:
            connectivity_tests.append(("Network Interfaces", False, str(e)))
        
        # Determine overall connectivity - require external connectivity
        successful_tests = sum(1 for test in connectivity_tests if test[1])
        total_tests = len(connectivity_tests)
        
        # Require at least 3 out of 6 tests to pass, with external connectivity being critical
        external_tests = [test for test in connectivity_tests if test[0] in ["DNS Resolution", "DNS Resolution 2", "Internet Access", "External Service", "HTTP Service"]]
        external_successful = sum(1 for test in external_tests if test[1])
        
        # Must have at least 2 external connectivity tests pass
        is_connected = external_successful >= 2 and successful_tests >= 3
        
        self.network_status = {
            "connected": is_connected,
            "last_check": time.time(),
            "error": None if is_connected else f"External connectivity failed: {external_successful}/{len(external_tests)} external tests passed",
            "tests": connectivity_tests
        }
        
        return self.network_status

    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status"""
        return self.network_status

    async def discover_devices(self) -> List[Dict[str, Any]]:
        """Fast device discovery using ARP table only"""
        all_devices = []
        
        print("Starting fast device discovery (ARP table only)...")
        
        # Check network connectivity first
        print("Checking network connectivity...")
        network_status = self._check_network_connectivity()
        
        if not network_status["connected"]:
            print(f"⚠️  Network connectivity issue detected: {network_status['error']}")
            # Return empty list but include network status
            return []
        
        print("✅ Network connectivity confirmed")
        
        # Get ARP table (fastest, most reliable for local network)
        print("Checking ARP table...")
        arp_devices = self._get_arp_table()
        
        # Optionally scan network for additional devices (threaded, non-blocking)
        scanned_devices = []
        try:
            print("Scanning network for additional devices (threaded)...")
            scanned_devices = self._scan_network_async()
        except Exception as e:
            print(f"Network scanning failed (non-critical): {e}")
        
        # Combine ARP and scanned devices, removing duplicates
        all_devices = arp_devices.copy()
        arp_ips = {device['ip'] for device in arp_devices}
        
        for device in scanned_devices:
            if device['ip'] not in arp_ips:
                all_devices.append(device)
                print(f"Found additional device via scan: {device['ip']}")
        
        print(f"Found {len(arp_devices)} devices via ARP, {len(scanned_devices)} via scan, {len(all_devices)} total")
        
        # Process devices and create final device list
        final_devices = []
        for device in all_devices:
            vendor = self._get_vendor_from_mac(device['mac'])
            device_info = self._get_device_info(device['ip'])
            
            discovery_method = 'arp' if device['ip'] in arp_ips else 'scan'
            
            final_devices.append({
                'id': device['ip'],
                'hostname': device['hostname'],
                'mgmtIp': device['ip'],
                'vendor': vendor if vendor != "Unknown" else device_info['vendor'],
                'model': device_info['model'],
                'status': 'up',
                'type': device_info['type'],
                'mac': device['mac'],
                'discovery_method': discovery_method
            })
        
        return final_devices
