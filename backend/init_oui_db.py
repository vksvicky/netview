#!/usr/bin/env python3
"""
Initialize OUI database on first run
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.oui_database import oui_db

def main():
    print("Initializing OUI database...")
    
    # Check if database already exists
    stats = oui_db.get_database_stats()
    if stats['total_entries'] > 0:
        print(f"OUI database already exists with {stats['total_entries']} entries")
        return
    
    # Update from IEEE standards
    print("Downloading OUI data from IEEE standards...")
    result = oui_db.update_from_ieee()
    
    if 'error' in result:
        print(f"Error updating OUI database: {result['error']}")
        sys.exit(1)
    
    print(f"OUI database initialized successfully!")
    print(f"New entries: {result['new_entries']}")
    print(f"Total entries: {result['total_entries']}")

if __name__ == "__main__":
    main()
