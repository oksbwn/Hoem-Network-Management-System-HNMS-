from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScheduleCreate(BaseModel):
    name: str
    scan_type: str
    target: str
    interval_seconds: int
    enabled: bool = True

class ScheduleRead(BaseModel):
    id: str
    name: str
    scan_type: str
    target: str
    interval_seconds: int
    enabled: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
