#!/usr/bin/env python3
"""
Script to download and parse the official IEEE OUI database
This creates a JSON file with MAC address prefixes mapped to vendor names
"""

import json
import urllib.request
import re
import os
from pathlib import Path

def download_oui_database():
    """Download the official IEEE OUI database"""
    urls = [
        "https://standards-oui.ieee.org/oui/oui.txt",
        "https://raw.githubusercontent.com/honzahommer/mac-address-oui-lookup/main/oui.txt",
        "https://gitlab.com/wireshark/wireshark/-/raw/master/manuf"
    ]
    
    for url in urls:
        print(f"Trying to download OUI database from: {url}")
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8')
            print(f"Downloaded {len(data)} bytes from {url}")
            return data
        except Exception as e:
            print(f"Failed to download from {url}: {e}")
            continue
    
    print("All download attempts failed")
    return None

def parse_oui_database(oui_text):
    """Parse the OUI database text and extract MAC prefixes and vendor names"""
    oui_db = {}
    
    # Pattern to match OUI entries
    # Format: XX-XX-XX   (hex)		VENDOR NAME
    pattern = r'^([0-9A-F]{2}-[0-9A-F]{2}-[0-9A-F]{2})\s+\(hex\)\s+(.+)$'
    
    lines = oui_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('Generated'):
            continue
            
        match = re.match(pattern, line)
        if match:
            mac_prefix = match.group(1).replace('-', ':')
            vendor_name = match.group(2).strip()
            
            # Clean up vendor name
            vendor_name = re.sub(r'\s+', ' ', vendor_name)
            vendor_name = vendor_name.replace('(hex)', '').strip()
            
            if vendor_name and len(vendor_name) > 1:
                oui_db[mac_prefix] = vendor_name
    
    return oui_db

def save_oui_database(oui_db, output_file):
    """Save the OUI database to a JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(oui_db, f, indent=2, sort_keys=True)
        print(f"Saved {len(oui_db)} OUI entries to {output_file}")
        return True
    except Exception as e:
        print(f"Failed to save OUI database: {e}")
        return False

def main():
    """Main function to download and process OUI database"""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_file = data_dir / "oui_database.json"
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Download OUI database
    oui_text = download_oui_database()
    if not oui_text:
        print("Failed to download OUI database")
        return
    
    # Parse OUI database
    print("Parsing OUI database...")
    oui_db = parse_oui_database(oui_text)
    
    if not oui_db:
        print("Failed to parse OUI database")
        return
    
    # Save to JSON file
    if save_oui_database(oui_db, output_file):
        print(f"Successfully created OUI database with {len(oui_db)} entries")
        print(f"File saved to: {output_file}")
    else:
        print("Failed to save OUI database")

if __name__ == "__main__":
    main()
