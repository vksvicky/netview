import os
import json


class Settings:
    def __init__(self) -> None:
        self.basic_auth_enabled = os.getenv("NETVIEW_BASIC_AUTH_ENABLED", "false").lower() == "true"
        self.basic_auth_username = os.getenv("NETVIEW_BASIC_AUTH_USERNAME", "")
        self.basic_auth_password = os.getenv("NETVIEW_BASIC_AUTH_PASSWORD", "")
        # Polling intervals in seconds
        self.discovery_interval_sec = int(os.getenv("NETVIEW_DISCOVERY_INTERVAL_SEC", "300"))
        self.polling_interval_sec = int(os.getenv("NETVIEW_POLLING_INTERVAL_SEC", "60"))
        
        # SNMP configuration
        self.snmp_community = os.getenv("NETVIEW_SNMP_COMMUNITY", "public")
        self.snmp_timeout = int(os.getenv("NETVIEW_SNMP_TIMEOUT", "1"))
        self.snmp_retries = int(os.getenv("NETVIEW_SNMP_RETRIES", "1"))
        
        # Network scan configuration - use full network ranges for hybrid discovery
        scan_networks = os.getenv("NETVIEW_SCAN_NETWORKS", "192.168.1.0/24,192.168.0.0/24,10.0.0.0/24")
        self.scan_networks = [net.strip() for net in scan_networks.split(',')]
        
        # Get SNMP config for services
        self.snmp_config = {
            'community': self.snmp_community,
            'timeout': self.snmp_timeout,
            'retries': self.snmp_retries,
            'scan_networks': self.scan_networks
        }


settings = Settings()


