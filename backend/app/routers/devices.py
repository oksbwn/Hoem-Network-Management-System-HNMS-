from fastapi import APIRouter, Query, HTTPException
from typing import List, Annotated, Optional, Dict, Any
from app.core.db import get_connection
from app.models.devices import DeviceRead, DeviceUpdate, PaginatedDevicesResponse
from app.services.devices import update_device_fields
import json, asyncio, math

router = APIRouter()

async def _internal_list_devices(
    device_type: str | None = None, 
    status: str | None = None,
    search: str | None = None,
    sort_by: str = "ip",
    sort_order: str = "asc",
    page: int = 1,
    limit: int = 20
):
    def query():
        conn = get_connection()
        try:
            # First, get total count for pagination
            count_sql = "SELECT COUNT(*) FROM devices"
            clauses: list[str] = []
            params: list[object] = []
            
            if device_type:
                clauses.append("device_type = ?")
                params.append(device_type)
            if status:
                clauses.append("status = ?")
                params.append(status)
            if search:
                clauses.append("(ip LIKE ? OR mac LIKE ? OR name LIKE ? OR display_name LIKE ? OR vendor LIKE ?)")
                search_param = f"%{search}%"
                params.extend([search_param] * 5)
            
            if clauses:
                count_sql += " WHERE " + " AND ".join(clauses)
                
            total = conn.execute(count_sql, params).fetchone()[0]
            
            # Calculate global stats for top cards
            global_stats = {
                "total": conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0],
                "online": conn.execute("SELECT COUNT(*) FROM devices WHERE status = 'online'").fetchone()[0],
                "offline": conn.execute("SELECT COUNT(*) FROM devices WHERE status = 'offline'").fetchone()[0]
            }
            vendor_row = conn.execute("""
                SELECT vendor, COUNT(*) as count 
                FROM devices 
                WHERE vendor IS NOT NULL AND vendor != 'Unknown' AND vendor != ''
                GROUP BY vendor ORDER BY count DESC LIMIT 1
            """).fetchone()
            global_stats["top_vendor"] = vendor_row[0] if vendor_row else "None"
            global_stats["top_vendor_count"] = vendor_row[1] if vendor_row else 0

            # Now fetch the data
            base_sql = """
                SELECT id, ip, mac, name, display_name, device_type,
                       first_seen, last_seen, vendor, icon, open_ports, status, attributes
                FROM devices
            """
            if clauses:
                base_sql += " WHERE " + " AND ".join(clauses)
                
            # Validate sort_by to prevent injection
            allowed_sort = ["ip", "mac", "display_name", "device_type", "last_seen", "status", "vendor"]
            if sort_by not in allowed_sort:
                safe_sort = "ip"
            else:
                safe_sort = sort_by
                
            order = "DESC" if sort_order.lower() == "desc" else "ASC"
            base_sql += f" ORDER BY {safe_sort} {order}"
            
            # Pagination
            if limit > 0:
                offset = (page - 1) * limit
                base_sql += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            rows = conn.execute(base_sql, params).fetchall()
            items = [
                DeviceRead(
                    id=r[0], ip=r[1], mac=r[2], name=r[3], display_name=r[4], device_type=r[5],
                    first_seen=r[6], last_seen=r[7], vendor=r[8], icon=r[9],
                    open_ports=json.loads(r[10]) if r[10] else [],
                    status=r[11],
                    attributes=json.loads(r[12]) if r[12] else {}
                )
                for r in rows
            ]
            
            # Calculate total pages correctly
            total_pages = 1
            if limit > 0:
                total_pages = math.ceil(total / limit) if total > 0 else 1

            return PaginatedDevicesResponse(
                items=items,
                total=total,
                page=page,
                limit=limit if limit > 0 else total,
                total_pages=total_pages,
                global_stats=global_stats
            )
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.get("/", response_model=PaginatedDevicesResponse)
async def list_devices(
    device_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "ip",
    sort_order: Annotated[str, Query()] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return await _internal_list_devices(
        device_type=device_type, 
        status=status, 
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )

@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: str):
    def query():
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, ip, mac, name, display_name, device_type,
                       first_seen, last_seen, vendor, icon, open_ports, status, attributes
                FROM devices WHERE id = ?
                """,
                [device_id],
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Device not found")
            ports_rows = conn.execute("SELECT port, service, protocol FROM device_ports WHERE device_id = ? ORDER BY port", [device_id]).fetchall()
            detailed_ports = [{"port": r[0], "service": r[1], "protocol": r[2]} for r in ports_rows] if ports_rows else (json.loads(row[10]) if row[10] else [])
            return DeviceRead(
                id=row[0], ip=row[1], mac=row[2], name=row[3], display_name=row[4], device_type=row[5],
                first_seen=row[6], last_seen=row[7], vendor=row[8], icon=row[9],
                open_ports=detailed_ports, status=row[11],
                attributes=json.loads(row[12]) if row[12] else {}
            )
        finally:
            conn.close()
    try:
        return await asyncio.to_thread(query)
    except HTTPException as e: raise e

@router.patch("/{device_id}", response_model=DeviceRead)
async def update_device_by_patch(device_id: str, update_data: DeviceUpdate):
    fields = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not fields: raise HTTPException(status_code=400, detail="No fields provided for update")
    
    # If attributes is a dict, stringify it for the service/DB
    if fields.get("attributes") is not None:
        if isinstance(fields["attributes"], dict):
            fields["attributes"] = json.dumps(fields["attributes"])
        elif not isinstance(fields["attributes"], str):
            fields["attributes"] = json.dumps(fields["attributes"])
        
    updated_device = await update_device_fields(device_id, fields)
    if not updated_device: raise HTTPException(status_code=404, detail="Device not found")
    return await get_device(device_id)

@router.put("/{device_id}", response_model=DeviceRead)
async def update_device_by_put(device_id: str, update_data: DeviceUpdate):
    """Identical to PATCH to support frontend axios.put calls."""
    return await update_device_by_patch(device_id, update_data)

@router.get("/export/json")
async def export_devices():
    return await _internal_list_devices(limit=-1)

@router.post("/import/json")
async def import_devices(devices_data: List[DeviceRead]):
    def sync_import():
        conn = get_connection()
        try:
            count = 0
            for d in devices_data:
                # Store as string in DB
                attrs_raw = json.dumps(d.attributes) if d.attributes else "{}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO devices 
                    (id, ip, mac, name, display_name, device_type, first_seen, last_seen, vendor, icon, status, open_ports, attributes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        d.id, d.ip, d.mac, d.name, d.display_name, d.device_type,
                        d.first_seen, d.last_seen, d.vendor, d.icon, d.status, json.dumps(d.open_ports), attrs_raw
                    ]
                )
                count += 1
            conn.commit()
            return count
        finally:
            conn.close()
    count = await asyncio.to_thread(sync_import)
    return {"status": "success", "imported": count}

@router.delete("/{device_id}")
async def delete_device(device_id: str):
    def sync_delete():
        conn = get_connection()
        try:
            row = conn.execute("SELECT id FROM devices WHERE id = ?", [device_id]).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Device not found")
            conn.execute("DELETE FROM device_ports WHERE device_id = ?", [device_id])
            conn.execute("DELETE FROM device_status_history WHERE device_id = ?", [device_id])
            conn.execute("DELETE FROM devices WHERE id = ?", [device_id])
            conn.commit()
        finally:
            conn.close()
    try:
        await asyncio.to_thread(sync_delete)
        return {"status": "success", "message": f"Device {device_id} deleted"}
    except HTTPException as e: raise e
