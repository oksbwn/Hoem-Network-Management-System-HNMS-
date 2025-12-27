from fastapi import APIRouter, Query, HTTPException
from typing import List, Annotated
from app.core.db import get_connection
from app.models.devices import DeviceRead

router = APIRouter()

def _internal_list_devices(device_type: str | None = None, online_only: bool = False):
    conn = get_connection()
    try:
        base_sql = """
            SELECT id, ip, mac, name, display_name, device_type,
                   first_seen, last_seen, vendor, icon, attributes
            FROM devices
        """
        clauses: list[str] = []
        params: list[object] = []
    
        if device_type:
            clauses.append("device_type = ?")
            params.append(device_type)
        
        if clauses:
            base_sql += " WHERE " + " AND ".join(clauses)
        base_sql += " ORDER BY ip"
    
        print(f"DEBUG: _internal_list_devices called with device_type={device_type} (type={type(device_type)})")
        print(f"DEBUG: params={params}")
        
        rows = conn.execute(base_sql, params).fetchall()
        return [
            DeviceRead(
                id=r[0],
                ip=r[1],
                mac=r[2],
                name=r[3],
                display_name=r[4],
                device_type=r[5],
                first_seen=r[6],
                last_seen=r[7],
                vendor=r[8],
                icon=r[9],
                attributes=r[10],
            )
            for r in rows
        ]
    finally:
        conn.close()

@router.get("/", response_model=list[DeviceRead])
def list_devices(
    device_type: Annotated[str | None, Query()] = None,
    online_only: Annotated[bool, Query()] = False,
):
    return _internal_list_devices(device_type=device_type, online_only=online_only)

@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: str):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, ip, mac, name, display_name, device_type,
                   first_seen, last_seen, vendor, icon, attributes
            FROM devices
            WHERE id = ?
            """,
            [device_id],
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Device not found")
        return DeviceRead(
            id=row[0],
            ip=row[1],
            mac=row[2],
            name=row[3],
            display_name=row[4],
            device_type=row[5],
            first_seen=row[6],
            last_seen=row[7],
            vendor=row[8],
            icon=row[9],
            attributes=row[10],
        )
    finally:
        conn.close()

from app.models.devices import DeviceUpdate

@router.put("/{device_id}", response_model=DeviceRead)
def update_device(device_id: str, payload: DeviceUpdate):
    conn = get_connection()
    try:
        # Verify existence
        row = conn.execute("SELECT id FROM devices WHERE id = ?", [device_id]).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Device not found")
            
        # Construct update query dynamically
        updates = []
        params = []
        
        if payload.name is not None:
            updates.append("name = ?")
            params.append(payload.name)
            
        if payload.display_name is not None:
            updates.append("display_name = ?")
            params.append(payload.display_name)
            
        if payload.device_type is not None:
            updates.append("device_type = ?")
            params.append(payload.device_type)

        if payload.vendor is not None:
            updates.append("vendor = ?")
            params.append(payload.vendor)

        if payload.icon is not None:
            updates.append("icon = ?")
            params.append(payload.icon)
            
        if not updates:
            # no-op
            return get_device(device_id)
            
        sql = f"UPDATE devices SET {', '.join(updates)} WHERE id = ?"
        params.append(device_id)
        
        conn.execute(sql, params)
        
        return get_device(device_id)
    finally:
        conn.close()

@router.get("/export/json")
def export_devices():
    """Returns all devices for backup purposes."""
    return _internal_list_devices()

from app.models.devices import DeviceRead

@router.post("/import/json")
def import_devices(devices_data: List[DeviceRead]):
    """Imports/Restores devices from a list. Uses INSERT OR REPLACE."""
    conn = get_connection()
    try:
        count = 0
        for d in devices_data:
            conn.execute(
                """
                INSERT OR REPLACE INTO devices 
                (id, ip, mac, name, display_name, device_type, first_seen, last_seen, vendor, icon, attributes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    d.id, d.ip, d.mac, d.name, d.display_name, d.device_type,
                    d.first_seen, d.last_seen, d.vendor, d.icon, d.attributes
                ]
            )
            count += 1
        return {"status": "success", "imported": count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to import: {str(e)}")
    finally:
        conn.close()
