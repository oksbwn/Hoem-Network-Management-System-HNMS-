from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceRead(BaseModel):
    id: str
    ip: str
    mac: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    device_type: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
