from fastapi import APIRouter
from app.core.db import get_connection
from app.models.config import ConfigItem, ConfigUpdate

router = APIRouter()

@router.get("/", response_model=list[ConfigItem])
def list_config():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM config").fetchall()
    return [ConfigItem(key=r[0], value=r[1] or "") for r in rows]

@router.get("/{key}", response_model=ConfigItem)
def get_config_item(key: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT key, value FROM config WHERE key = ?", [key]
    ).fetchone()
    if not row:
        return ConfigItem(key=key, value="")
    return ConfigItem(key=row[0], value=row[1] or "")

@router.put("/{key}", response_model=ConfigItem)
def upsert_config_item(key: str, payload: ConfigUpdate):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO config (key, value)
        VALUES (?, ?)
        ON CONFLICT (key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """,
        [key, payload.value],
    )
    return ConfigItem(key=key, value=payload.value)
