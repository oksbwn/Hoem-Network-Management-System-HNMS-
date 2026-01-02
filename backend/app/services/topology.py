import logging
from typing import Dict, Any, List
from app.core.db import get_connection

logger = logging.getLogger(__name__)

class TopologyService:
    def get_graph(self) -> Dict[str, Any]:
        """
        Generates a graph representation of the network.
        Currently implements a simple Star Topology (Gateway -> Devices).
        """
        conn = get_connection()
        try:
            # Fetch all active devices
            rows = conn.execute(
                "SELECT id, ip, mac, display_name, device_type, vendor, status, icon, parent_id FROM devices ORDER BY ip"
            ).fetchall()
            
            nodes = {}
            edges = {}
            
            # 1. Identify or Create Gateway
            gateway_id = "gateway_node"
            gateway_ip = None
            
            # Try to find a real gateway (usually .1)
            for row in rows:
                ip = row[1]
                if ip and ip.endswith('.1'):
                    gateway_id = row[0]
                    gateway_ip = ip
                    break
            
            # If no real gateway found, add a virtual one
            if gateway_id == "gateway_node":
                nodes[gateway_id] = {
                    "name": "Router / Gateway",
                    "type": "Router",
                    "status": "online",
                    "ip": "Unknown",
                    "icon": "Router"
                }

            # 2. Build Nodes
            for row in rows:
                dev_id, ip, mac, name, dev_type, vendor, status, icon, parent_id = row
                
                # Infer icon from type if not set
                if not icon:
                    icon = self._get_icon_for_type(dev_type)

                # Add Node
                nodes[dev_id] = {
                    "name": name or ip,
                    "type": dev_type or "Unknown",
                    "vendor": vendor,
                    "status": status,
                    "ip": ip,
                    "mac": mac,
                    "icon": icon or "HelpCircle",
                    "parent_id": parent_id
                }

            # 3. Build Edges
            for dev_id, node in nodes.items():
                if dev_id == gateway_id:
                    continue
                
                # Use explicit parent_id if it exists and exists in nodes
                parent = node.get("parent_id")
                if parent and parent in nodes:
                    source_id = parent
                else:
                    source_id = gateway_id
                
                edge_id = f"edge_{source_id}_{dev_id}"
                edges[edge_id] = {
                    "source": source_id,
                    "target": dev_id,
                    "label": "" 
                }

            return {"nodes": nodes, "edges": edges}

        except Exception as e:
            logger.error(f"Failed to generate topology: {e}")
            return {"nodes": {}, "edges": {}}
        finally:
            conn.close()

    def _get_icon_for_type(self, dev_type: str) -> str:
        if not dev_type:
            return None
        
        dt = dev_type.lower()
        if "param" in dt: return None # Ignore internal types
        
        mapping = {
            "mobile": "Smartphone",
            "phone": "Smartphone",
            "android": "Smartphone",
            "iphone": "Smartphone",
            "tablet": "Tablet",
            "ipad": "Tablet",
            "desktop": "Desktop",
            "computer": "Desktop",
            "pc": "Desktop",
            "server": "Server",
            "laptop": "Laptop",
            "macbook": "Laptop",
            "printer": "Printer",
            "tv": "Tv",
            "television": "Tv",
            "camera": "Camera",
            "webcam": "Camera",
            "game": "Gamepad",
            "console": "Gamepad",
            "xbox": "Gamepad",
            "playstation": "Gamepad",
            "nintendo": "Gamepad",
            "watch": "Watch",
            "wearable": "Watch",
            "speaker": "Speaker",
            "audio": "Speaker",
            "alexa": "Speaker",
            "google home": "Speaker",
            "router": "Router",
            "gateway": "Router",
            "access point": "Wifi",
            "ap": "Wifi",
            "switch": "Server"
        }
        
        for key, icon in mapping.items():
            if key in dt:
                return icon
        
        return None
