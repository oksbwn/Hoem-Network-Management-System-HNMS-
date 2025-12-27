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

@router.post("/", response_model=list[ConfigItem])
def bulk_update_config(payload: dict[str, str]):
    conn = get_connection()
    results = []
    
    # We use a transaction effectively by being in one request context (DuckDB handling)
    for key, value in payload.items():
        conn.execute(
            """
            INSERT INTO config (key, value)
            VALUES (?, ?)
            ON CONFLICT (key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """,
            [key, str(value)],
        )
        results.append(ConfigItem(key=key, value=str(value)))
        
    return results
