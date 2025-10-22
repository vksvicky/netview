import subprocess
import socket
import re
import json
import os
from typing import Any, Dict, List, Optional
import platform
import asyncio
import concurrent.futures
import threading
import requests
import time
from .oui_database import oui_db
from .user_settings import user_settings_service
from .router_discovery import RouterDiscoveryService
from .device_cache import device_cache
from sqlalchemy.orm import Session


class FastDiscoveryService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.network_status = {"connected": True, "last_check": None, "error": None}
        
    def _get_vendor_from_mac(self, mac: str) -> str:
        """Get vendor name from MAC address using OUI database"""
        if not mac or len(mac) < 8:
            return "Unknown"
        
        # Use the centralized OUI database service
        vendor = oui_db.lookup_vendor(mac)
        return vendor if vendor else "Unknown"
    
    def _get_mac_from_arp(self, ip: str) -> str:
        """Get MAC address for an IP from ARP table"""
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse output: "? (192.168.1.11) at 6a:6:44:26:70:e3 on en0 ifscope [ethernet]"
                    match = re.search(r'at\s+([0-9a-fA-F:]+)', result.stdout)
                    if match:
                        return match.group(1)
            elif platform.system() == "Linux":
                result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse Linux ARP output
                    match = re.search(r'([0-9a-fA-F:]{17})', result.stdout)
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"Error getting MAC for {ip}: {e}")
        return None
    
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
                                        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                                            # Submit ping tasks
                                            future_to_ip = {
                                                executor.submit(self._ping_host, f"{base_ip}.{i}"): f"{base_ip}.{i}"
                                                for i in range(1, 255)  # Skip .0 and .255
                                            }
                                            
                                            # Collect results with timeout
                                            for future in concurrent.futures.as_completed(future_to_ip, timeout=30):
                                                ip = future_to_ip[future]
                                                try:
                                                    if future.result():
                                                        # Try to get MAC address from ARP table
                                                        mac = self._get_mac_from_arp(ip)
                                                        devices.append({
                                                            'ip': ip,
                                                            'mac': mac if mac else 'Unknown',
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

    def _get_device_info_hybrid(self, ip: str, mac: str) -> Dict[str, str]:
        """Get device information using hybrid approach with multiple methods in parallel"""
        device_info = {
            'ip': ip,
            'hostname': ip,
            'vendor': 'Unknown',
            'model': 'Unknown',
            'type': 'unknown',
            'status': 'up'
        }
        
        # Try to get hostname via reverse DNS first (fast)
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            device_info['hostname'] = hostname
        except:
            pass
        
        # Use threading to try multiple discovery methods in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all discovery methods
            future_snmp = executor.submit(self._get_device_info_snmp, ip)
            future_http = executor.submit(self._get_device_info_http, ip)
            future_upnp = executor.submit(self._get_device_info_upnp, ip)
            future_services = executor.submit(self._get_device_info_services, ip)
            
            # Wait for the first successful result with timeout
            futures = [future_snmp, future_http, future_upnp, future_services]
            method_names = ['SNMP', 'HTTP', 'UPnP', 'Services']
            
            for future, method_name in zip(futures, method_names):
                try:
                    result = future.result(timeout=0.5)  # Reduced to 0.5 second timeout per method
                    if result and result.get('model') != 'Unknown':
                        print(f"✅ {method_name} discovery successful for {ip}: {result.get('model')}")
                        device_info.update(result)
                        # Cancel remaining futures
                        for f in futures:
                            if f != future and not f.done():
                                f.cancel()
                        break
                except (concurrent.futures.TimeoutError, Exception) as e:
                    # Don't print every failure to reduce noise
                    continue
        
        # Fallback to basic device type detection
        if device_info['model'] == 'Unknown':
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

    def _get_device_info_snmp(self, ip: str) -> Optional[Dict[str, str]]:
        """Get device info via SNMP"""
        try:
            # Try sysDescr first
            result = subprocess.run(['snmpget', '-v2c', '-c', 'public', ip, '1.3.6.1.2.1.1.1.0'], 
                                  capture_output=True, text=True, timeout=1)  # Reduced timeout
            if result.returncode == 0:
                sys_descr = result.stdout.strip()
                if '=' in sys_descr:
                    sys_descr = sys_descr.split('=', 1)[1].strip().strip('"')
                
                # Parse model from sysDescr
                model = self._parse_model_from_sysdescr(sys_descr)
                if model != 'Unknown':
                    return {'model': model, 'type': 'router' if 'router' in sys_descr.lower() else 'device'}
            
            # Try sysObjectID as fallback
            result = subprocess.run(['snmpget', '-v2c', '-c', 'public', ip, '1.3.6.1.2.1.1.2.0'], 
                                  capture_output=True, text=True, timeout=1)  # Reduced timeout
            if result.returncode == 0:
                sys_oid = result.stdout.strip()
                model = self._parse_model_from_oid(sys_oid)
                if model != 'Unknown':
                    return {'model': model, 'type': 'device'}
                    
        except Exception as e:
            print(f"SNMP discovery error for {ip}: {e}")
        
        return None

    def _get_device_info_http(self, ip: str) -> Optional[Dict[str, str]]:
        """Get device info via HTTP requests"""
        try:
            # Try common ports and paths
            urls_to_try = [
                f'http://{ip}/',
                f'http://{ip}:8080/',
                f'https://{ip}/',
                f'http://{ip}/status',
                f'http://{ip}/info',
                f'http://{ip}/device'
            ]
            
            for url in urls_to_try:
                try:
                    response = requests.get(url, timeout=0.5, verify=False)  # Reduced timeout
                    if response.status_code == 200:
                        # Parse title and content for model information
                        model = self._parse_model_from_html(response.text)
                        if model != 'Unknown':
                            return {'model': model, 'type': 'device'}
                except:
                    continue
                    
        except Exception as e:
            print(f"HTTP discovery error for {ip}: {e}")
        
        return None

    def _get_device_info_upnp(self, ip: str) -> Optional[Dict[str, str]]:
        """Get device info via UPnP/SSDP discovery"""
        try:
            # Send SSDP M-SEARCH request
            ssdp_request = (
                "M-SEARCH * HTTP/1.1\r\n"
                "HOST: 239.255.255.250:1900\r\n"
                "MAN: \"ssdp:discover\"\r\n"
                "ST: upnp:rootdevice\r\n"
                "MX: 3\r\n\r\n"
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
            
            try:
                data, addr = sock.recvfrom(1024)
                if addr[0] == ip:
                    response = data.decode()
                    model = self._parse_model_from_upnp(response)
                    if model != 'Unknown':
                        return {'model': model, 'type': 'device'}
            except socket.timeout:
                pass
            finally:
                sock.close()
                
        except Exception as e:
            print(f"UPnP discovery error for {ip}: {e}")
        
        return None

    def _get_device_info_services(self, ip: str) -> Optional[Dict[str, str]]:
        """Get device info via service banner detection"""
        try:
            # Common ports to check
            ports_to_check = [22, 23, 80, 443, 8080, 8443, 161, 162]
            
            for port in ports_to_check:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        # Port is open, try to get banner
                        banner = self._get_service_banner(ip, port)
                        if banner:
                            model = self._parse_model_from_banner(banner, port)
                            if model != 'Unknown':
                                sock.close()
                                return {'model': model, 'type': 'device'}
                    sock.close()
                except:
                    continue
                    
        except Exception as e:
            print(f"Service discovery error for {ip}: {e}")
        
        return None

    def _parse_model_from_sysdescr(self, sys_descr: str) -> str:
        """Parse model from SNMP sysDescr"""
        if not sys_descr:
            return 'Unknown'
        
        # Common patterns in sysDescr
        patterns = [
            r'(\w+)\s+Router',  # "Orbi Router"
            r'(\w+)\s+Switch',  # "Cisco Switch"
            r'(\w+)\s+AP',      # "Unifi AP"
            r'Model:\s*(\w+)',  # "Model: B0210"
            r'(\w+)\s+\d+',     # "Netgear R7000"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sys_descr, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'Unknown'

    def _parse_model_from_oid(self, sys_oid: str) -> str:
        """Parse model from SNMP sysObjectID"""
        # This would need a comprehensive OID to model mapping
        # For now, return Unknown
        return 'Unknown'

    def _parse_model_from_html(self, html_content: str) -> str:
        """Parse model from HTML content"""
        if not html_content:
            return 'Unknown'
        
        # Look for title tags
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1)
            # Extract model from title
            model_match = re.search(r'(\w+)\s+(Router|Switch|AP|Device)', title, re.IGNORECASE)
            if model_match:
                return model_match.group(1)
        
        # Look for model in meta tags or content
        model_patterns = [
            r'Model[:\s]+(\w+)',
            r'Device[:\s]+(\w+)',
            r'Product[:\s]+(\w+)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'Unknown'

    def _parse_model_from_upnp(self, upnp_response: str) -> str:
        """Parse model from UPnP response"""
        if not upnp_response:
            return 'Unknown'
        
        # Look for model in UPnP headers
        model_match = re.search(r'MODEL[:\s]+([^\r\n]+)', upnp_response, re.IGNORECASE)
        if model_match:
            return model_match.group(1).strip()
        
        return 'Unknown'

    def _get_service_banner(self, ip: str, port: int) -> Optional[str]:
        """Get service banner from open port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            
            # Try to receive some data
            sock.settimeout(0.5)
            try:
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                return banner
            except:
                return None
            finally:
                sock.close()
        except:
            return None

    def _parse_model_from_banner(self, banner: str, port: int) -> str:
        """Parse model from service banner"""
        if not banner:
            return 'Unknown'
        
        # SSH banners often contain device info
        if port == 22:
            if 'OpenSSH' in banner:
                return 'Linux Device'
            elif 'Cisco' in banner:
                return 'Cisco Device'
        
        # HTTP banners
        if port in [80, 443, 8080, 8443]:
            server_match = re.search(r'Server[:\s]+([^\r\n]+)', banner, re.IGNORECASE)
            if server_match:
                return server_match.group(1).strip()
        
        return 'Unknown'

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

    async def discover_devices(self, db: Session = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fast device discovery with caching (like Orbi interface)"""
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_devices = device_cache.get_cached_devices()
            if cached_devices:
                print(f"✅ Using cached devices: {len(cached_devices)} devices")
                return cached_devices
        
        print("Starting fresh device discovery...")
        all_devices = []
        
        # Use simple ARP table discovery (fastest approach like Orbi interface)
        print("Using simple ARP table discovery for speed...")
        all_devices = self._get_simple_arp_devices(db)
        
        # Update cache with new devices
        if all_devices:
            device_cache.update_cache(all_devices)
            print(f"✅ Updated device cache with {len(all_devices)} devices")
        
        return all_devices
    
    def _get_simple_arp_devices(self, db: Session = None) -> List[Dict[str, Any]]:
        """Simple ARP table discovery - fast like Orbi interface"""
        devices = []
        
        try:
            # Get ARP table (fastest method)
            arp_devices = self._get_arp_table()
            
            # Process devices quickly
            for device in arp_devices:
                vendor = self._get_vendor_from_mac(device['mac'])
                
                # Get device name (hostname or generate from vendor)
                device_name = self._get_device_name(device['hostname'], vendor, device['ip'])
                
                # Determine connection type and IP version
                connection_type = self._get_connection_type(device['mac'], vendor)
                ip_version = self._get_ip_version(device['ip'])
                
                device_data = {
                    'id': device['ip'],
                    'hostname': device_name,  # Use device name instead of IP
                    'mgmtIp': device['ip'],
                    'vendor': vendor,
                    'model': 'Unknown',  # Keep simple for speed
                    'status': 'up',
                    'type': 'device',
                    'mac': device['mac'],
                    'discovery_method': 'arp_simple',
                    'connection_type': connection_type,
                    'ip_version': ip_version,
                    'device_name': device_name
                }
                
                # Apply user mappings if available
                if db:
                    device_data = user_settings_service.apply_user_mappings_to_device(db, device_data)
                
                devices.append(device_data)
            
            print(f"✅ Simple ARP discovery found {len(devices)} devices")
            
        except Exception as e:
            print(f"❌ Simple ARP discovery error: {e}")
        
        return devices
    
    def _get_device_name(self, hostname: str, vendor: str, ip: str) -> str:
        """Generate a meaningful device name"""
        # If we have a good hostname, use it
        if hostname and hostname != ip and not hostname.startswith('192.168.'):
            return hostname
        
        # Generate name based on vendor and IP
        if vendor and vendor != "Unknown":
            # Clean vendor name
            vendor_clean = vendor.split()[0]  # Take first word
            if vendor_clean.lower() in ['apple', 'samsung', 'google', 'microsoft']:
                return f"{vendor_clean} Device"
            elif vendor_clean.lower() in ['netgear', 'cisco', 'linksys']:
                return f"{vendor_clean} Router"
            else:
                return f"{vendor_clean} Device"
        
        # Fallback to IP-based name
        return f"Device-{ip.split('.')[-1]}"
    
    def _get_connection_type(self, mac: str, vendor: str) -> str:
        """Determine connection type (wired/wireless, frequency)"""
        if not mac or mac == "Unknown":
            return "Unknown"
        
        # Check for known wireless vendors
        wireless_vendors = [
            'apple', 'samsung', 'google', 'microsoft', 'amazon', 'sony',
            'lg', 'huawei', 'xiaomi', 'oneplus', 'motorola', 'nokia'
        ]
        
        if vendor and any(wv in vendor.lower() for wv in wireless_vendors):
            # Most modern devices support 5GHz, but we can't determine exact frequency from ARP
            return "Wireless (2.4GHz/5GHz)"
        
        # Check for router/access point vendors
        router_vendors = ['netgear', 'cisco', 'linksys', 'tp-link', 'd-link', 'asus']
        if vendor and any(rv in vendor.lower() for rv in router_vendors):
            return "Wired (Ethernet)"
        
        # Check for IoT/smart device vendors
        iot_vendors = ['espressif', 'dyson', 'philips', 'nest', 'ring', 'arlo']
        if vendor and any(iv in vendor.lower() for iv in iot_vendors):
            return "Wireless (2.4GHz)"
        
        # Default assumption
        return "Wireless (2.4GHz/5GHz)"
    
    def _get_ip_version(self, ip: str) -> str:
        """Determine IP version"""
        if not ip:
            return "Unknown"
        
        # Check for IPv6
        if ':' in ip:
            return "IPv6"
        
        # Check for IPv4
        if '.' in ip:
            return "IPv4"
        
        return "Unknown"
    
    def _discover_via_router(self) -> List[Dict[str, Any]]:
        """Discover devices via router's device table (like Orbi interface)"""
        try:
            router_service = RouterDiscoveryService()
            devices = router_service.get_router_device_table()
            
            # Process devices and add vendor/model information
            processed_devices = []
            for device in devices:
                # Get vendor from MAC address
                vendor = self._get_vendor_from_mac(device['mac'])
                
                # Apply user mappings if database session is available
                if hasattr(self, '_db') and self._db:
                    device = user_settings_service.apply_user_mappings_to_device(self._db, device)
                
                processed_devices.append({
                    'id': device['ip'],
                    'hostname': device['hostname'],
                    'mgmtIp': device['ip'],
                    'vendor': vendor if vendor != "Unknown" else device.get('vendor', 'Unknown'),
                    'model': device.get('model', 'Unknown'),
                    'status': device['status'],
                    'type': device['type'],
                    'mac': device['mac'],
                    'discovery_method': device.get('source', 'router')
                })
            
            return processed_devices
            
        except Exception as e:
            print(f"Router discovery error: {e}")
            return []
    
    async def _discover_via_arp_fallback(self, db: Session = None) -> List[Dict[str, Any]]:
        """Fallback to ARP table discovery"""
        all_devices = []
        
        print("Starting ARP table fallback discovery...")
        
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
            
            # Use hybrid approach to get detailed device information
            device_info = self._get_device_info_hybrid(device['ip'], device['mac'])
            
            discovery_method = 'arp' if device['ip'] in arp_ips else 'scan'
            
            device_data = {
                'id': device['ip'],
                'hostname': device_info['hostname'],
                'mgmtIp': device['ip'],
                'vendor': vendor if vendor != "Unknown" else device_info['vendor'],
                'model': device_info['model'],
                'status': device_info['status'],
                'type': device_info['type'],
                'mac': device['mac'],
                'discovery_method': discovery_method
            }
            
            # Apply user-defined mappings if database session is available
            if db:
                device_data = user_settings_service.apply_user_mappings_to_device(db, device_data)
            
            final_devices.append(device_data)
        
        return final_devices
