import json
import logging
import httpx
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, List, Dict, Any

from app.core.db import get_connection
from app.services.mqtt import publish_device_online, publish_device_offline

logger = logging.getLogger(__name__)

async def upsert_device_from_scan(
    ip: str,
    mac: Optional[str],
    hostname: Optional[str],
    ports: List[Dict[str, Any]],
) -> str:
    """
    Updates or creates a device based on scan results.
    Triggers MQTT events if the device is new or came online after being offline.
    """
    conn = get_connection()
    now = datetime.now(timezone.utc)
    
    # Check if device exists
    # We try to match by MAC first if available, else IP (though IP can change, for now simplistic)
    # Ideally we trust MAC more.
    device_id = None
    existing_device = None
    
    if mac:
        existing_device = conn.execute(
            "SELECT id, first_seen, last_seen, ip, attributes FROM devices WHERE mac = ?", [mac]
        ).fetchone()
    
    if not existing_device:
        # Fallback to IP matching if no MAC (or MAC not found yet and we want to link by IP - debatable but common for simple scanners)
        # Note: If we find by IP but new scan has MAC, we should update the entry to include MAC.
        existing_device = conn.execute(
            "SELECT id, first_seen, last_seen, ip, attributes FROM devices WHERE ip = ?", [ip]
        ).fetchone()

    is_new = False
    is_came_online = False
    
    if existing_device:
        device_id, first_seen, last_seen, old_ip, attributes = existing_device
        
        # Check if it was offline for a while? (e.g. > 10 mins)
        time_diff = (now - last_seen).total_seconds()
        if time_diff > 300: 
            is_came_online = True
            
        # Heuristic for Gateway
        final_type = "unknown"
        if ip.endswith(".1"):
             final_type = "Router/Gateway"
            
        # Update
        conn.execute(
            """
            UPDATE devices
            SET last_seen = ?,
                ip = ?,
                mac = COALESCE(?, mac),
                name = COALESCE(name, ?),
                device_type = COALESCE(device_type, ?)
            WHERE id = ?
            """,
            [now, ip, mac, hostname, final_type, device_id]
        )
    else:
        is_new = True
        is_came_online = True
        device_id = str(uuid4())
        
        # Heuristic
        initial_type = "unknown"
        if ip.endswith(".1"):
             initial_type = "Router/Gateway"

        conn.execute(
            """
            INSERT INTO devices (id, ip, mac, name, display_name, device_type, first_seen, last_seen, attributes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [device_id, ip, mac, hostname, hostname or ip, initial_type, now, now, "{}"]
        )

    # Update Ports
    # We clear old ports for this device and insert new ones (snapshot view)
    # Or we could merge. Snapshot is safer to remove closed ports.
    conn.execute("DELETE FROM device_ports WHERE device_id = ?", [device_id])
    if ports:
        for p in ports:
            conn.execute(
                """
                INSERT INTO device_ports (device_id, port, protocol, service, last_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                [device_id, p["port"], p["protocol"], p["service"], now]
            )

    # Trigger Enrichment
    if mac:
        # running enrichment async-ish (we await it here but could be bg task)
        # Check if we already have vendor
        attrs = {}
        if existing_device and existing_device[4]:
            try:
                attrs = json.loads(existing_device[4])
            except:
                pass
        
        if "vendor" not in attrs:
            await enrich_device(device_id, mac)

    # Notify MQTT
    if is_new or is_came_online:
        device_info = {
            "id": device_id,
            "ip": ip,
            "mac": mac,
            "hostname": hostname,
            "status": "online",
            "timestamp": now.isoformat()
        }
        publish_device_online(device_info)

    return device_id

async def enrich_device(device_id: str, mac: str):
    """
    Fetches vendor information from macvendors.co and updates the device attributes.
    """
    url = f"https://api.macvendors.com/{mac}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            if resp.status_code == 200:
                vendor = resp.text.strip()
                if vendor:
                    conn = get_connection()
                    # fetch current attributes to merge
                    row = conn.execute("SELECT attributes, display_name FROM devices WHERE id = ?", [device_id]).fetchone()
                    if row:
                        old_attrs_json = row[0]
                        display_name = row[1]
                        try:
                            attrs = json.loads(old_attrs_json) if old_attrs_json else {}
                        except:
                            attrs = {}
                        
                        attrs["vendor"] = vendor
                        
                        # also update display name if it's just IP
                        new_display = display_name
                        if not display_name or display_name == row[0]: # matched ip
                             new_display = vendor
                        
                        conn.execute(
                            "UPDATE devices SET attributes = ?, display_name = COALESCE(display_name, ?) WHERE id = ?",
                            [json.dumps(attrs), vendor, device_id]
                        )
                        logger.info(f"Enriched device {device_id} with vendor {vendor}")
    except Exception as e:
        logger.warning(f"Failed to enrich MAC {mac}: {e}")

