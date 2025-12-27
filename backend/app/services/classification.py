import re
from typing import Optional, Tuple
from app.core.db import get_connection

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
    "Generic": "help-circle",
    "unknown": "help-circle"
}

# Local OUI mapping for common vendors (First 3 bytes)
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
    "00:0a:27": "Apple, Inc.",
    "00:0d:93": "Apple, Inc.",
    "00:10:fa": "Apple, Inc.",
    "00:11:24": "Apple, Inc.",
    "00:14:51": "Apple, Inc.",
    "00:16:cb": "Apple, Inc.",
    "b8:27:eb": "Raspberry Pi Foundation",
    "dc:a6:32": "Raspberry Pi Foundation",
    "e4:5f:01": "Raspberry Pi Foundation",
    "00:15:5d": "Microsoft Corporation (Hyper-V)",
    "00:1a:2b": "Casio Computer Co., Ltd.",
    "00:1a:11": "Google, Inc.",
    "f4:f5:d8": "Google, Inc.",
    "00:50:ba": "D-Link Corporation",
    "00:0d:88": "D-Link Corporation",
    "00:1e:58": "D-Link Corporation",
    "00:21:91": "D-Link Corporation",
    "00:14:d1": "TP-Link Technologies",
    "00:19:e0": "TP-Link Technologies",
    "00:23:cd": "TP-Link Technologies",
    "00:27:19": "TP-Link Technologies",
    "bc:d1:d3": "TP-Link Technologies",
    "c0:25:a5": "TP-Link Technologies",
    "c0:4a:00": "TP-Link Technologies",
    "8c:ae:4c": "ASUSTek Computer Inc.",
    "ac:22:0b": "ASUSTek Computer Inc.",
    "ac:9e:17": "ASUSTek Computer Inc.",
    "b0:6e:bf": "ASUSTek Computer Inc.",
    "bc:ee:7b": "ASUSTek Computer Inc.",
    "00:16:3e": "Xensource, Inc (Xen)",
    "00:1e:67": "Intel Corporation",
    "00:21:6a": "Intel Corporation",
    "00:23:4d": "Intel Corporation",
    "00:24:d7": "Intel Corporation",
    "00:26:c7": "Intel Corporation",
    "b4:b5:b6": "Samsung Electronics",
    "b4:b6:76": "Samsung Electronics",
    "b8:c6:8e": "Samsung Electronics",
    "bc:72:b1": "Samsung Electronics",
    "cc:07:ab": "Samsung Electronics",
    "dc:e0:64": "Samsung Electronics",
    "00:0c:f1": "Intel Corporation",
    "00:1b:21": "Intel Corporation",
    "fc:db:b3": "Amazon Technologies (Echo/Kindle)",
    "00:bb:3a": "Amazon Technologies",
    "0c:47:c9": "Amazon Technologies",
    "30:d1:7e": "Amazon Technologies",
    "34:d2:70": "Amazon Technologies",
    "44:65:0d": "Amazon Technologies",
    "50:dc:e7": "Amazon Technologies",
}

def get_vendor_from_db(mac: str) -> Optional[str]:
    """Queries the local mac_vendors table."""
    if not mac or len(mac) < 8:
        return None
    prefix = mac.upper()[:8]
    conn = get_connection()
    try:
        row = conn.execute("SELECT vendor FROM mac_vendors WHERE oui = ?", [prefix]).fetchone()
        return row[0] if row else None
    except:
        return None
    finally:
        conn.close()

def get_vendor_locally(mac: str) -> Optional[str]:
    if not mac or len(mac) < 8:
        return None
    prefix = mac.lower()[:8]
    
    # Tier 0: Hardcoded fast list
    hardcoded = COMMON_OUIS.get(prefix)
    if hardcoded: return hardcoded
    
    # Tier 1: Local DuckDB table (full IEEE copy)
    return get_vendor_from_db(mac)

def classify_device(
    hostname: Optional[str], 
    vendor: Optional[str], 
    ports: list[int] = []
) -> Tuple[str, str]:
    """
    Returns (device_type, icon_name) based on heuristics.
    """
    hostname = (hostname or "").lower()
    vendor = (vendor or "").lower()
    
    # 1. Routers / Infrastructure
    if "router" in hostname or "gateway" in hostname:
        return "Router/Gateway", TYPE_TO_ICON["Router/Gateway"]
    if "asus" in vendor and (80 in ports or 443 in ports):
        return "Router/Gateway", TYPE_TO_ICON["Router/Gateway"]
    if "tplink" in vendor or "d-link" in vendor or "cisco" in vendor:
         return "Router/Gateway", TYPE_TO_ICON["Router/Gateway"]

    # 2. Mobile / Tablets
    if "iphone" in hostname or "android" in hostname or "phone" in hostname:
        return "Smartphone", TYPE_TO_ICON["Smartphone"]
    if "ipad" in hostname or "tablet" in hostname:
        return "Tablet", TYPE_TO_ICON["Tablet"]
    if "apple" in vendor:
        if "iphone" in hostname: return "Smartphone", TYPE_TO_ICON["Smartphone"]
        if "ipad" in hostname: return "Tablet", TYPE_TO_ICON["Tablet"]
        if "macbook" in hostname: return "Laptop", TYPE_TO_ICON["Laptop"]
        return "Desktop", TYPE_TO_ICON["Desktop"] # Default Apple to Desktop

    # 3. Storage
    if "nas" in hostname or "synology" in vendor or "qnap" in vendor:
        return "NAS/Storage", TYPE_TO_ICON["NAS/Storage"]
    if 548 in ports or 445 in ports: # AFP / SMB
        if "nas" in hostname: return "NAS/Storage", TYPE_TO_ICON["NAS/Storage"]

    # 4. Entertainment
    if "tv" in hostname or "bravia" in hostname or "samsung" in vendor and "tv" in hostname:
        return "TV/Entertainment", TYPE_TO_ICON["TV/Entertainment"]
    if "playstation" in hostname or "nintendo" in hostname or "xbox" in hostname:
        return "Game Console", TYPE_TO_ICON["Game Console"]

    # 5. Printers
    if "printer" in hostname or "hp" in vendor or "canon" in vendor or "epson" in vendor:
        return "Printer", TYPE_TO_ICON["Printer"]

    # 6. Servers
    if "server" in hostname or "proxmox" in hostname or "esxi" in hostname:
        return "Server", TYPE_TO_ICON["Server"]

    # 7. Smart Home / IoT (The "Guessing" part)
    iot_keywords = ["hue", "lifx", "light", "bulb", "led", "lamp"]
    if any(k in hostname for k in iot_keywords) or any(k in vendor for k in iot_keywords):
        return "Smart Bulb", TYPE_TO_ICON["Smart Bulb"]

    if any(k in hostname for k in ["plug", "switch", "sonoff", "tuya", "shelly"]):
        return "Smart Plug/Switch", TYPE_TO_ICON["Smart Plug/Switch"]
    
    if "camera" in hostname or any(k in vendor for k in ["dahua", "hikvision", "reolink", "wyze"]):
        return "Security Camera", TYPE_TO_ICON["Security Camera"]
    
    if "sonos" in hostname or "sonos" in vendor:
        return "Audio/Speaker", TYPE_TO_ICON["Audio/Speaker"]

    if "roku" in hostname or "roku" in vendor:
        return "Streaming Device", TYPE_TO_ICON["Streaming Device"]

    # 8. Microcontrollers (ESP8266, ESP32, Arduino)
    if "espressif" in vendor or "esp32" in hostname or "esp8266" in hostname or "nodemcu" in hostname:
        return "Microcontroller", TYPE_TO_ICON["Microcontroller"]
    if "arduino" in vendor or "arduino" in hostname:
        return "Microcontroller", TYPE_TO_ICON["Microcontroller"]

    # Default based on ports
    if 80 in ports or 443 in ports:
        return "Generic", TYPE_TO_ICON["Generic"]
        
    return "unknown", TYPE_TO_ICON["unknown"]
