import json
import logging
import httpx
import re
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
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc)
        
        device_id = None
        existing_device = None
        
        if mac:
            existing_device = conn.execute(
                "SELECT id, first_seen, last_seen, ip, attributes FROM devices WHERE mac = ?", [mac]
            ).fetchone()
        
        if not existing_device:
            existing_device = conn.execute(
                "SELECT id, first_seen, last_seen, ip, attributes FROM devices WHERE ip = ?", [ip]
            ).fetchone()

        is_new = False
        is_came_online = False
        
        # Track existing manual overrides (we don't want to overwrite user-set names/types/vendors)
        user_overrode_name = False
        user_overrode_type = False
        user_overrode_vendor = False
        user_overrode_icon = False
        
        if existing_device:
            device_id, first_seen, last_seen, old_ip, attributes_raw = existing_device
            
            # Check if user has already set values (simplistic check for now: if they differ from what we'd guess)
            # Better: we could have a 'manual' flag in attributes, but let's just check if they are set
            # Actually, let's just always update if it was 'unknown' or empty.
            
            if last_seen and last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
                
            time_diff = (now - last_seen).total_seconds() if last_seen else 999999
            if time_diff > 300: 
                is_came_online = True
                
            # We'll use the classification engine to guess type/icon if they are currently unknown
            from app.services.classification import classify_device
            port_numbers = [p["port"] for p in ports]
            guessed_type, guessed_icon = classify_device(hostname, None, port_numbers) # Vendor fetched later in enrichment
            
            # Update
            conn.execute(
                """
                UPDATE devices
                SET last_seen = ?,
                    ip = ?,
                    mac = COALESCE(?, mac),
                    name = COALESCE(name, ?),
                    device_type = COALESCE(device_type, ?),
                    icon = COALESCE(icon, ?),
                    open_ports = ?
                WHERE id = ?
                """,
                [now, ip, mac, hostname, guessed_type, guessed_icon, json.dumps(ports), device_id]
            )
        else:
            is_new = True
            is_came_online = True
            device_id = str(uuid4())
            
            from app.services.classification import classify_device
            port_numbers = [p["port"] for p in ports]
            guessed_type, guessed_icon = classify_device(hostname, None, port_numbers)

            conn.execute(
                """
                INSERT INTO devices (id, ip, mac, name, display_name, device_type, icon, open_ports, first_seen, last_seen, attributes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [device_id, ip, mac, hostname, hostname or ip, guessed_type, guessed_icon, json.dumps(ports), now, now, "{}"]
            )

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

        if mac:
            from app.services.classification import get_vendor_locally
            local_vendor = get_vendor_locally(mac)
            
            if local_vendor:
                 conn.execute("UPDATE devices SET vendor = COALESCE(vendor, ?) WHERE id = ?", [local_vendor, device_id])
            
            # Still schedule enrichment if vendor is unknown or was only local
            # Actually let's just trigger it if we don't have a vendor yet
            row = conn.execute("SELECT vendor FROM devices WHERE id = ?", [device_id]).fetchone()
            if not row or not row[0]:
                await enrich_device(device_id, mac)

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
    finally:
        conn.close()

def format_mac(mac: str) -> str:
    if not mac: return ""
    clean = "".join(c for c in mac if c.isalnum()).upper()
    if len(clean) != 12: return mac
    return ":".join(clean[i:i+2] for i in range(0, 12, 2))

async def enrich_device(device_id: str, mac: str):
    """
    Multi-tier vendor enrichment: 
    1. Local OUI lookup
    2. Primary API (macvendors.com)
    3. Fallback API (maclookup.app or similar)
    """
    if not mac: return
    mac = format_mac(mac)

    # 1. Local check
    from app.services.classification import get_vendor_locally, classify_device
    vendor = get_vendor_locally(mac)
    
    if not vendor:
        # 2. Try Primary API
        url = f"https://api.macvendors.com/{mac}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5.0)
                if resp.status_code == 200:
                    vendor = resp.text.strip()
                elif resp.status_code == 429:
                    logger.warning(f"Rate limited by macvendors.com for {mac}")
                else:
                    # 3. Try Fallback API if primary is 404/Fail
                    # Using maclookup.app (simple JSON API)
                    fallback_url = f"https://api.maclookup.app/v2/macs/{mac}"
                    fresp = await client.get(fallback_url, timeout=5.0)
                    if fresp.status_code == 200:
                        fdata = fresp.json()
                        if fdata.get("success") and fdata.get("company"):
                             vendor = fdata["company"]
        except Exception as e:
            logger.warning(f"API Enrichment failed for {mac}: {e}")

    if vendor:
        conn = get_connection()
        try:
            row = conn.execute("SELECT display_name, device_type, icon, attributes FROM devices WHERE id = ?", [device_id]).fetchone()
            if row:
                display_name, current_type, current_icon, old_attrs_json = row
                
                # Re-classify
                new_type = current_type
                new_icon = current_icon
                if not current_type or current_type == "unknown":
                    new_type, new_icon = classify_device(None, vendor)

                # Set display name if it's currently an IP
                new_display = display_name
                if not display_name or re.match(r"^\d+\.\d+\.\d+\.\d+$", display_name):
                     new_display = vendor

                # Merge attributes
                try:
                    attrs = json.loads(old_attrs_json) if old_attrs_json else {}
                except:
                    attrs = {}
                attrs["vendor"] = vendor

                conn.execute(
                    """
                    UPDATE devices 
                    SET vendor = COALESCE(vendor, ?),
                        device_type = CASE WHEN device_type = 'unknown' OR device_type IS NULL THEN ? ELSE device_type END,
                        icon = CASE WHEN icon = 'help-circle' OR icon IS NULL THEN ? ELSE icon END,
                        display_name = ?,
                        attributes = ?
                    WHERE id = ?
                    """,
                    [vendor, new_type, new_icon, new_display, json.dumps(attrs), device_id]
                )
                logger.info(f"Successfully enriched {device_id} with {vendor}")
        finally:
            conn.close()

