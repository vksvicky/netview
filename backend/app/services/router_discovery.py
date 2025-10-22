import requests
import re
import json
from typing import Dict, List, Any, Optional
import subprocess

# Optional BeautifulSoup import
try:
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False


class RouterDiscoveryService:
    def __init__(self, router_ip: str = "192.168.1.1"):
        self.router_ip = router_ip
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for local routers
        
    def get_router_device_table(self) -> List[Dict[str, Any]]:
        """Get device table directly from router - similar to Orbi interface"""
        devices = []
        
        # Try multiple methods to get device information from router
        methods = [
            self._get_devices_from_http,
            self._get_devices_from_snmp_arp,
            self._get_devices_from_snmp_bridge,
            self._fallback_arp_scan
        ]
        
        for method in methods:
            try:
                devices = method()
                if devices:
                    print(f"✅ Router discovery successful using {method.__name__}: {len(devices)} devices")
                    break
            except Exception as e:
                print(f"❌ {method.__name__} failed: {e}")
                continue
        
        return devices
    
    def _get_devices_from_http(self) -> List[Dict[str, Any]]:
        """Try to get device list from router's HTTP interface"""
        try:
            # Try common router endpoints
            endpoints = [
                '/start.htm',
                '/device_list.htm',
                '/attached_devices.htm',
                '/dhcp_clients.htm',
                '/client_list.htm',
                '/connected_devices.htm',
                '/network_map.htm'
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"http://{self.router_ip}{endpoint}"
                    response = self.session.get(url, timeout=2)
                    if response.status_code == 200:
                        devices = self._parse_router_html(response.text)
                        if devices:
                            return devices
                except:
                    continue
                    
        except Exception as e:
            print(f"HTTP discovery error: {e}")
        
        return []
    
    def _parse_router_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse device information from router HTML pages"""
        devices = []
        
        try:
            # Try to parse with BeautifulSoup if available
            if HAS_BEAUTIFULSOUP:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Look for device tables
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            device_info = self._extract_device_from_row(cells)
                            if device_info:
                                devices.append(device_info)
                
                if devices:
                    return devices
            
            # Fallback: regex parsing for common patterns
            # Look for IP addresses in the content
            ip_pattern = r'\b(192\.168\.\d+\.\d+)\b'
            mac_pattern = r'\b([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})\b'
            
            ips = re.findall(ip_pattern, html_content)
            macs = re.findall(mac_pattern, html_content)
            
            # Try to match IPs with MACs
            for i, ip in enumerate(ips):
                if i < len(macs):
                    devices.append({
                        'ip': ip,
                        'mac': macs[i],
                        'hostname': f'Device-{i+1}',
                        'vendor': 'Unknown',
                        'model': 'Unknown',
                        'type': 'device',
                        'status': 'up',
                        'source': 'router_http'
                    })
            
        except Exception as e:
            print(f"HTML parsing error: {e}")
        
        return devices
    
    def _extract_device_from_row(self, cells) -> Optional[Dict[str, Any]]:
        """Extract device information from HTML table row"""
        try:
            # Common patterns in router device tables
            text_content = ' '.join([cell.get_text().strip() for cell in cells])
            
            # Look for IP address
            ip_match = re.search(r'\b(192\.168\.\d+\.\d+)\b', text_content)
            if not ip_match:
                return None
            
            ip = ip_match.group(1)
            
            # Look for MAC address
            mac_match = re.search(r'\b([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})\b', text_content)
            mac = mac_match.group(1) if mac_match else 'Unknown'
            
            # Look for device name/hostname
            hostname = 'Unknown'
            for cell in cells:
                cell_text = cell.get_text().strip()
                if cell_text and not re.match(r'\b(192\.168\.\d+\.\d+)\b', cell_text) and not re.match(r'\b([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})\b', cell_text):
                    hostname = cell_text
                    break
            
            return {
                'ip': ip,
                'mac': mac,
                'hostname': hostname,
                'vendor': 'Unknown',
                'model': 'Unknown',
                'type': 'device',
                'status': 'up',
                'source': 'router_http'
            }
            
        except Exception as e:
            print(f"Row extraction error: {e}")
            return None
    
    def _get_devices_from_snmp_arp(self) -> List[Dict[str, Any]]:
        """Get devices from router's SNMP ARP table"""
        devices = []
        
        try:
            # SNMP ARP table: 1.3.6.1.2.1.4.22.1
            result = subprocess.run([
                'snmpwalk', '-v2c', '-c', 'public', self.router_ip, 
                '1.3.6.1.2.1.4.22.1'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                devices = self._parse_snmp_arp_output(result.stdout)
                
        except Exception as e:
            print(f"SNMP ARP error: {e}")
        
        return devices
    
    def _get_devices_from_snmp_bridge(self) -> List[Dict[str, Any]]:
        """Get devices from router's SNMP bridge table"""
        devices = []
        
        try:
            # SNMP Bridge table: 1.3.6.1.2.1.17.4.3.1
            result = subprocess.run([
                'snmpwalk', '-v2c', '-c', 'public', self.router_ip,
                '1.3.6.1.2.1.17.4.3.1'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                devices = self._parse_snmp_bridge_output(result.stdout)
                
        except Exception as e:
            print(f"SNMP Bridge error: {e}")
        
        return devices
    
    def _parse_snmp_arp_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse SNMP ARP table output"""
        devices = []
        
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if 'ipNetToMediaPhysAddress' in line:
                    # Extract IP and MAC from SNMP output
                    # Format: .1.3.6.1.2.1.4.22.1.2.1.192.168.1.2 = Hex-STRING: B0 B3 53 73 43 52
                    parts = line.split('=')
                    if len(parts) == 2:
                        oid_part = parts[0].strip()
                        value_part = parts[1].strip()
                        
                        # Extract IP from OID
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', oid_part)
                        if ip_match:
                            ip = ip_match.group(1)
                            
                            # Extract MAC from value
                            mac_match = re.search(r'([0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2})', value_part)
                            if mac_match:
                                mac = mac_match.group(1).replace(' ', ':')
                                
                                devices.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'hostname': f'Device-{len(devices)+1}',
                                    'vendor': 'Unknown',
                                    'model': 'Unknown',
                                    'type': 'device',
                                    'status': 'up',
                                    'source': 'router_snmp_arp'
                                })
        except Exception as e:
            print(f"SNMP ARP parsing error: {e}")
        
        return devices
    
    def _parse_snmp_bridge_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse SNMP Bridge table output"""
        devices = []
        
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if 'dot1dTpFdbAddress' in line:
                    # Extract MAC from bridge table
                    parts = line.split('=')
                    if len(parts) == 2:
                        value_part = parts[1].strip()
                        mac_match = re.search(r'([0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2}\s+[0-9a-fA-F]{2})', value_part)
                        if mac_match:
                            mac = mac_match.group(1).replace(' ', ':')
                            
                            devices.append({
                                'ip': 'Unknown',
                                'mac': mac,
                                'hostname': f'Device-{len(devices)+1}',
                                'vendor': 'Unknown',
                                'model': 'Unknown',
                                'type': 'device',
                                'status': 'up',
                                'source': 'router_snmp_bridge'
                            })
        except Exception as e:
            print(f"SNMP Bridge parsing error: {e}")
        
        return devices
    
    def _fallback_arp_scan(self) -> List[Dict[str, Any]]:
        """Fallback to local ARP table scan"""
        devices = []
        
        try:
            # Use local ARP table as fallback
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                devices = self._parse_arp_output(result.stdout)
        except Exception as e:
            print(f"ARP scan error: {e}")
        
        return devices
    
    def _parse_arp_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse ARP table output"""
        devices = []
        
        try:
            lines = output.strip().split('\n')
            for line in lines:
                # Parse ARP output format
                # macOS: "? (192.168.1.2) at b0:b3:53:73:43:52 on en0 ifscope [ethernet]"
                # Linux: "192.168.1.2 ether b0:b3:53:73:43:52 C en0"
                
                ip_match = re.search(r'\b(192\.168\.\d+\.\d+)\b', line)
                mac_match = re.search(r'\b([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})\b', line)
                
                if ip_match and mac_match:
                    devices.append({
                        'ip': ip_match.group(1),
                        'mac': mac_match.group(1),
                        'hostname': f'Device-{len(devices)+1}',
                        'vendor': 'Unknown',
                        'model': 'Unknown',
                        'type': 'device',
                        'status': 'up',
                        'source': 'arp_table'
                    })
        except Exception as e:
            print(f"ARP parsing error: {e}")
        
        return devices
