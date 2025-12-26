from fastapi import APIRouter, Query, HTTPException
from app.core.db import get_connection
from app.models.devices import DeviceRead

router = APIRouter()

@router.get("/", response_model=list[DeviceRead])
def list_devices(
    device_type: str | None = Query(default=None),
    online_only: bool = Query(default=False),
):
    conn = get_connection()
    base_sql = """
        SELECT id, ip, mac, name, display_name, device_type,
               first_seen, last_seen
        FROM devices
    """
    clauses: list[str] = []
    params: list[object] = []

    if device_type:
        clauses.append("device_type = ?")
        params.append(device_type)
    if online_only:
        # later, you can base this on last_seen freshness
        pass

    if clauses:
        base_sql += " WHERE " + " AND ".join(clauses)
    base_sql += " ORDER BY ip"

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
        )
        for r in rows
    ]

@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: str):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, ip, mac, name, display_name, device_type,
               first_seen, last_seen
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
    )
