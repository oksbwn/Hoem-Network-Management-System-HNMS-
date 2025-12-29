from fastapi import APIRouter, HTTPException
from app.core.db import get_connection
from app.models.schedules import ScheduleCreate, ScheduleRead
from datetime import datetime
import uuid, asyncio

router = APIRouter()

@router.post("/", response_model=ScheduleRead)
async def create_schedule(payload: ScheduleCreate):
    def sync_create():
        conn = get_connection()
        try:
            sched_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO scan_schedules 
                (id, name, scan_type, target, interval_seconds, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [sched_id, payload.name, payload.scan_type, payload.target, payload.interval_seconds, payload.enabled],
            )
            conn.commit()
            return sched_id
        finally:
            conn.close()
    sched_id = await asyncio.to_thread(sync_create)
    return ScheduleRead(
        id=sched_id, name=payload.name, scan_type=payload.scan_type,
        target=payload.target, interval_seconds=payload.interval_seconds, enabled=payload.enabled
    )

@router.get("/", response_model=list[ScheduleRead])
async def list_schedules():
    def query():
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT id, name, scan_type, target, interval_seconds, enabled, last_run_at, next_run_at FROM scan_schedules"
            ).fetchall()
            return [
                ScheduleRead(
                    id=r[0], name=r[1], scan_type=r[2], target=r[3], 
                    interval_seconds=r[4], enabled=r[5], last_run_at=r[6], next_run_at=r[7]
                )
                for r in rows
            ]
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    def sync_delete():
        conn = get_connection()
        try:
            conn.execute("DELETE FROM scan_schedules WHERE id = ?", [schedule_id])
            conn.commit()
        finally:
            conn.close()
    await asyncio.to_thread(sync_delete)
    return {"status": "deleted"}
