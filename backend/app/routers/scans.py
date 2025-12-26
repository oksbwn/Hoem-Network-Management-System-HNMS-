from fastapi import APIRouter
from app.core.db import get_connection
from app.models.scans import ScanCreate, ScanRead, ScanRead, ScanResultRead
from datetime import datetime
import json, uuid

router = APIRouter()

@router.post("/", response_model=ScanRead)
def create_scan(payload: ScanCreate):
    conn = get_connection()
    scan_id = str(uuid.uuid4())
    now = datetime.utcnow()
    options_json = json.dumps(payload.options) if payload.options else None
    conn.execute(
        """
        INSERT INTO scans (id, target, scan_type, options, status, created_at)
        VALUES (?, ?, ?, ?, 'queued', ?)
        """,
        [scan_id, payload.target, payload.scan_type, options_json, now],
    )
    return ScanRead(
        id=scan_id,
        target=payload.target,
        scan_type=payload.scan_type,
        options=payload.options,
        status="queued",
        created_at=now,
        started_at=None,
        finished_at=None,
        error_message=None,
    )

@router.get("/", response_model=list[ScanRead])
def list_scans():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, target, scan_type, options, status,
               created_at, started_at, finished_at, error_message
        FROM scans ORDER BY created_at DESC
        """
    ).fetchall()
    result: list[ScanRead] = []
    for r in rows:
        options = json.loads(r[3]) if r[3] else None
        result.append(
            ScanRead(
                id=r[0],
                target=r[1],
                scan_type=r[2],
                options=options,
                status=r[4],
                created_at=r[5],
                started_at=r[6],
                finished_at=r[7],
                error_message=r[8],
            )
        )
    return result

@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(scan_id: str):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, target, scan_type, options, status,
               created_at, started_at, finished_at, error_message
        FROM scans WHERE id = ?
        """,
        [scan_id],
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    options = json.loads(row[3]) if row[3] else None
    return ScanRead(
        id=row[0],
        target=row[1],
        scan_type=row[2],
        options=options,
        status=row[4],
        created_at=row[5],
        started_at=row[6],
        finished_at=row[7],
        error_message=row[8],
    )

@router.get("/{scan_id}/results", response_model=list[ScanResultRead])
def get_scan_results(scan_id: str):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, scan_id, ip, mac, hostname, open_ports, os, first_seen, last_seen
        FROM scan_results
        WHERE scan_id = ?
        ORDER BY ip
        """,
        [scan_id],
    ).fetchall()
    result: list[ScanResultRead] = []
    for r in rows:
        open_ports = json.loads(r[5]) if r[5] else None
        result.append(
            ScanResultRead(
                id=r[0],
                scan_id=r[1],
                ip=r[2],
                mac=r[3],
                hostname=r[4],
                open_ports=open_ports,
                os=r[6],
                first_seen=r[7],
                last_seen=r[8],
            )
        )
    return result
