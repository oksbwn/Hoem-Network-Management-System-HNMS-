from fastapi import APIRouter
from app.core.db import get_connection
from app.models.config import ConfigItem, ConfigUpdate
import asyncio
import json
from typing import Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=list[ConfigItem])
async def list_config():
    def query():
        conn = get_connection()
        try:
            rows = conn.execute("SELECT key, value FROM config").fetchall()
            return [ConfigItem(key=r[0], value=r[1] or "") for r in rows]
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.get("/{key}", response_model=ConfigItem)
async def get_config_item(key: str):
    def query():
        conn = get_connection()
        try:
            row = conn.execute("SELECT key, value FROM config WHERE key = ?", [key]).fetchone()
            if not row:
                return ConfigItem(key=key, value="")
            return ConfigItem(key=row[0], value=row[1] or "")
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.put("/{key}", response_model=ConfigItem)
async def upsert_config_item(key: str, payload: ConfigUpdate):
    def update():
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, now())
                """,
                [key, payload.value],
            )
            conn.commit()
            logger.info(f"Updated config {key} to {payload.value}")
        finally:
            conn.close()
    await asyncio.to_thread(update)
    return ConfigItem(key=key, value=payload.value)

@router.post("/", response_model=list[ConfigItem])
async def bulk_update_config(payload: dict[str, Any]):
    def update():
        conn = get_connection()
        results = []
        try:
            for key, value in payload.items():
                if not isinstance(value, str):
                    val_str = json.dumps(value)
                else:
                    val_str = value
                    
                conn.execute(
                    """
                    INSERT OR REPLACE INTO config (key, value, updated_at)
                    VALUES (?, ?, now())
                    """,
                    [key, val_str],
                )
                results.append(ConfigItem(key=key, value=val_str))
            conn.commit()
            logger.info(f"Bulk updated {len(payload)} config items")
            return results
        finally:
            conn.close()
    return await asyncio.to_thread(update)
