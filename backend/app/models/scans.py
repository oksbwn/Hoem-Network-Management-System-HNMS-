from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

class ScanCreate(BaseModel):
    target: str
    scan_type: str = Field(..., examples=["arp", "ping", "tcp-syn"])
    options: dict[str, Any] | None = None

class ScanRead(BaseModel):
    id: str
    target: str
    scan_type: str
    options: dict[str, Any] | None = None
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

class ScanResultRead(BaseModel):
    id: str
    scan_id: str
    ip: str
    mac: str | None = None
    hostname: str | None = None
    open_ports: list[dict[str, Any]] | None = None
    os: str | None = None
    first_seen: datetime
    last_seen: datetime