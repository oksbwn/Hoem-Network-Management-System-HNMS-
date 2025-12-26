from app.core.db import get_connection
from app.models.scans import ScanCreate, ScanRead
import uuid

def insert_scan(payload: ScanCreate) -> ScanRead:
    conn = get_connection()
    scan_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO scans (id, target, scan_type, options, status) VALUES (?, ?, ?, ?, ?)",
        [scan_id, payload.target, payload.scan_type, payload.options_json(), "queued"],
    )
    # map row → ScanRead; or re-select if you want timestamps
    return ScanRead(id=scan_id, **payload.model_dump())
