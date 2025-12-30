import re
import json
import logging
import time
from typing import Optional, Tuple, List, Dict
from app.core.db import get_connection

logger = logging.getLogger(__name__)

# Mapping of device_type to Lucide icon names
TYPE_TO_ICON = {
    "Smartphone": "smartphone",
    "Tablet": "tablet",
    "Laptop": "laptop",
    "Desktop": "monitor",
    "Server": "server",
    "Router/Gateway": "router",
    "Network Bridge": "network",
    "Switch": "layers",
    "Access Point": "rss",
    "TV/Entertainment": "tv",
    "IoT Device": "cpu",
    "Smart Bulb": "lightbulb",
    "Smart Plug/Switch": "plug",
    "Microcontroller": "microchip",
    "Security Camera": "camera",
    "Sensor": "waves",
    "Audio/Speaker": "speaker",
    "Streaming Device": "play",
    "Printer": "printer",
    "NAS/Storage": "hard-drive",
    "Game Console": "gamepad-2",
    "Media Server": "play-circle",
    "Home Automation": "home",
    "Server Admin": "settings",
    "Generic": "help-circle",
    "unknown": "help-circle"
}

# Cache for classification rules
_RULES_CACHE = []
_LAST_CACHE_UPDATE = 0
CACHE_TTL = 60 # Refresh rules every minute

def get_rules() -> List[Dict]:
    """Fetches classification rules from DB with caching."""
    global _RULES_CACHE, _LAST_CACHE_UPDATE
    now = time.time()
    
    if _RULES_CACHE and (now - _LAST_CACHE_UPDATE < CACHE_TTL):
        return _RULES_CACHE
    
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT pattern_hostname, pattern_vendor, ports, device_type, icon FROM classification_rules ORDER BY priority ASC, name ASC"
        ).fetchall()
        _RULES_CACHE = [
            {
                "hostname": r[0],
                "vendor": r[1],
                "ports": json.loads(r[2] or "[]"),
                "type": r[3],
                "icon": r[4]
            } for r in rows
        ]
        _LAST_CACHE_UPDATE = now
        return _RULES_CACHE
    except Exception as e:
        logger.error(f"Error fetching classification rules: {e}")
        return []
    finally:
        conn.close()

# Local OUI mapping for common vendors (kept for performance/OUI lookup only)
COMMON_OUIS = {
    "00:0c:29": "VMware, Inc.",
    "00:50:56": "VMware, Inc.",
    "08:00:27": "Oracle Corporation (VirtualBox)",
    "00:1c:c3": "Huawei Technologies",
    "00:25:9c": "Cisco Systems",
    "3c:5a:b4": "Google, Inc.",
    "d8:3b:bf": "Apple, Inc.",
    "f0:18:98": "Apple, Inc.",
    "00:03:93": "Apple, Inc.",
    "00:05:02": "Apple, Inc.",
    "00:15:5d": "Microsoft Corporation (Hyper-V)",
    "b8:27:eb": "Raspberry Pi Foundation",
    "dc:a6:32": "Raspberry Pi Foundation",
    "e4:5f:01": "Raspberry Pi Foundation",
    "00:14:d1": "TP-Link Technologies",
    "bc:d1:d3": "TP-Link Technologies",
    "c0:4a:00": "TP-Link Technologies",
    "8c:ae:4c": "ASUSTek Computer Inc.",
    "fc:db:b3": "Amazon Technologies (Echo/Kindle)",
}

def get_vendor_locally(mac: str) -> Optional[str]:
    if not mac or len(mac) < 8:
        return None
    prefix = mac.lower()[:8]
    return COMMON_OUIS.get(prefix)

def classify_device(
    hostname: Optional[str], 
    vendor: Optional[str], 
    ports: list[int] = []
) -> Tuple[str, str]:
    """
    Returns (device_type, icon_name) based on database-driven rules.
    """
    hostname = (hostname or "").lower()
    vendor = (vendor or "").lower()
    
    rules = get_rules()
    
    for rule in rules:
        matched = False
        
        # 1. Check Hostname Pattern
        if rule["hostname"]:
            if re.search(rule["hostname"], hostname, re.IGNORECASE):
                matched = True
        
        # 2. Check Vendor Pattern
        if not matched and rule["vendor"]:
            if re.search(rule["vendor"], vendor, re.IGNORECASE):
                matched = True
                
        # 3. Check Ports
        if not matched and rule["ports"]:
            if any(p in ports for p in rule["ports"]):
                matched = True
                
        if matched:
            return rule["type"], rule["icon"]

    # 10. Fallback: Service-based Classification (Generic but better than 'unknown')
    if any(p in ports for p in [22, 23, 21, 25, 53, 5900]):
         return "Server", TYPE_TO_ICON["Server"]
    if any(p in ports for p in [1883, 8883, 5683, 6053]):
         return "IoT Device", TYPE_TO_ICON["IoT Device"]
    if any(p in ports for p in [139, 445, 548]):
         return "NAS/Storage", TYPE_TO_ICON["NAS/Storage"]
    if any(p in ports for p in [80, 443, 8080, 8443, 8123, 8006, 9000, 9443, 32400, 8096]):
         return "Generic", TYPE_TO_ICON["Generic"]

    # If any port is open, it's at least a 'Generic' device, not 'unknown'
    if ports:
        # Sort ports so we show the lowest/most likely primary service
        p = sorted(ports)[0]
        return f"Service ({p})", TYPE_TO_ICON["Generic"]
        
    return "unknown", TYPE_TO_ICON["unknown"]
