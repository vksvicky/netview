import json
import os
import re
import requests
from typing import Dict, Optional
from pathlib import Path


class OuiDatabase:
    """OUI (Organizationally Unique Identifier) database manager"""
    
    def __init__(self, resources_dir: str = "resources"):
        self.resources_dir = Path(resources_dir)
        self.oui_file = self.resources_dir / "oui_database.json"
        self.oui_data: Dict[str, Dict[str, str]] = {}
        self._load_database()
    
    def _load_database(self) -> None:
        """Load OUI database from local file"""
        if self.oui_file.exists():
            try:
                with open(self.oui_file, 'r') as f:
                    self.oui_data = json.load(f)
                print(f"Loaded OUI database with {len(self.oui_data)} entries")
            except Exception as e:
                print(f"Error loading OUI database: {e}")
                self.oui_data = {}
        else:
            print("OUI database file not found, will create on first update")
            self.oui_data = {}
    
    def _save_database(self) -> None:
        """Save OUI database to local file"""
        try:
            self.resources_dir.mkdir(exist_ok=True)
            with open(self.oui_file, 'w') as f:
                json.dump(self.oui_data, f, indent=2)
            print(f"Saved OUI database with {len(self.oui_data)} entries")
        except Exception as e:
            print(f"Error saving OUI database: {e}")
    
    def _parse_oui_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse a single line from IEEE OUI database"""
        # Skip empty lines and comments
        if not line.strip() or line.startswith('#'):
            return None
        
        # Pattern to match OUI entries
        # Format: XX-XX-XX (hex)	Organization Name
        pattern = r'^([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})\s+\(hex\)\s+(.+)$'
        match = re.match(pattern, line.strip())
        
        if match:
            oui_hex = match.group(1).replace('-', '').upper()
            organization = match.group(2).strip()
            return {
                'oui': oui_hex,
                'organization': organization
            }
        
        return None
    
    def update_from_ieee(self) -> Dict[str, int]:
        """Update OUI database from IEEE standards website"""
        print("Updating OUI database from IEEE standards...")
        
        # IEEE OUI database URLs - try different formats and sources
        urls = [
            # IEEE official URLs (try different formats)
            "https://standards.ieee.org/wp-content/uploads/registries/oui.txt",
            "https://standards.ieee.org/wp-content/uploads/registries/oui36.txt", 
            "https://standards.ieee.org/wp-content/uploads/registries/oui28.txt",
            # Alternative IEEE URLs
            "https://standards-oui.ieee.org/oui/oui.txt",
            "https://standards-oui.ieee.org/oui36/oui36.txt",
            "https://standards-oui.ieee.org/oui28/oui28.txt",
            # Additional comprehensive sources
            "https://raw.githubusercontent.com/uxmansarwar/mac-address-vendor-database/master/data/raw/ma-l.csv",
            "https://raw.githubusercontent.com/uxmansarwar/mac-address-vendor-database/master/data/raw/ma-m.csv",
            "https://raw.githubusercontent.com/uxmansarwar/mac-address-vendor-database/master/data/raw/ma-s.csv",
            "https://raw.githubusercontent.com/uxmansarwar/mac-address-vendor-database/master/data/raw/iab.csv",
            "https://raw.githubusercontent.com/uxmansarwar/mac-address-vendor-database/master/data/raw/cid.csv",
            # Public alternatives
            "https://raw.githubusercontent.com/honzahommer/oui-database/main/oui.csv",
            "https://gitlab.com/wireshark/wireshark/-/raw/master/manuf"
        ]
        
        try:
            new_entries = 0
            updated_entries = 0
            
            # Parse CSV format
            import csv
            from io import StringIO
            
            for url in urls:
                print(f"Downloading from: {url}")
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Try CSV format first
                    if url.endswith('.csv'):
                        csv_content = StringIO(response.text)
                        reader = csv.DictReader(csv_content)
                        
                        for row in reader:
                            # Handle different CSV formats
                            oui_hex = None
                            organization = None
                            
                            # Format 1: IEEE standard format
                            if 'Assignment' in row and 'Organization Name' in row:
                                oui_hex = row['Assignment'].strip().replace('-', '').upper()
                                organization = row['Organization Name'].strip()
                            # Format 2: Alternative format
                            elif 'OUI' in row and 'Company' in row:
                                oui_hex = row['OUI'].strip().replace('-', '').upper()
                                organization = row['Company'].strip()
                            # Format 3: Another alternative
                            elif 'oui' in row and 'company' in row:
                                oui_hex = row['oui'].strip().replace('-', '').upper()
                                organization = row['company'].strip()
                            
                            if oui_hex and organization and len(oui_hex) >= 6:
                                # Normalize to 6 characters for MA-L (most common)
                                oui_key = oui_hex[:6]
                                
                                if oui_key in self.oui_data:
                                    if self.oui_data[oui_key]['organization'] != organization:
                                        updated_entries += 1
                                else:
                                    new_entries += 1
                                
                                self.oui_data[oui_key] = {
                                    'organization': organization,
                                    'source': 'ieee_standards',
                                    'full_oui': oui_hex
                                }
                    
                    # Try text format (IEEE standard format)
                    elif url.endswith('.txt') or 'manuf' in url:
                        for line in response.text.split('\n'):
                            entry = self._parse_oui_line(line)
                            if entry:
                                oui_hex = entry['oui']
                                organization = entry['organization']
                                
                                if oui_hex and organization and len(oui_hex) >= 6:
                                    oui_key = oui_hex[:6]
                                    
                                    if oui_key in self.oui_data:
                                        if self.oui_data[oui_key]['organization'] != organization:
                                            updated_entries += 1
                                    else:
                                        new_entries += 1
                                    
                                    self.oui_data[oui_key] = {
                                        'organization': organization,
                                        'source': 'ieee_standards',
                                        'full_oui': oui_hex
                                    }
                    
                    print(f"Successfully processed {url}")
                    
                except requests.RequestException as e:
                    print(f"Error downloading from {url}: {e}")
                    continue
            
            # Save the updated database
            self._save_database()
            
            result = {
                'new_entries': new_entries,
                'updated_entries': updated_entries,
                'total_entries': len(self.oui_data)
            }
            
            print(f"OUI database update completed: {result}")
            return result
            
        except requests.RequestException as e:
            print(f"Error fetching OUI data from IEEE: {e}")
            return {'error': str(e)}
        except Exception as e:
            print(f"Error updating OUI database: {e}")
            return {'error': str(e)}
    
    def lookup_vendor(self, mac_address: str) -> Optional[str]:
        """Look up vendor name from MAC address"""
        if not mac_address:
            return None
        
        # Clean MAC address (remove separators and convert to uppercase)
        mac_clean = re.sub(r'[^0-9A-Fa-f]', '', mac_address).upper()
        
        if len(mac_clean) < 6:
            return None
        
        # Get OUI (first 6 characters)
        oui = mac_clean[:6]
        
        if oui in self.oui_data:
            return self.oui_data[oui]['organization']
        
        return None
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        return {
            'total_entries': len(self.oui_data),
            'file_exists': self.oui_file.exists(),
            'file_size_bytes': self.oui_file.stat().st_size if self.oui_file.exists() else 0
        }
    
    def search_organization(self, query: str) -> Dict[str, str]:
        """Search for organizations by name (case-insensitive)"""
        query_lower = query.lower()
        results = {}
        
        for oui, data in self.oui_data.items():
            if query_lower in data['organization'].lower():
                results[oui] = data['organization']
        
        return results


# Global OUI database instance
oui_db = OuiDatabase()
