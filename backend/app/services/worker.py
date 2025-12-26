import asyncio
from datetime import datetime, timedelta, timezone
from app.core.db import get_connection
from app.services.scans import run_scan_job

POLL_INTERVAL_SECONDS = 5

async def scheduler_loop():
    while True:
        try:
            await handle_schedules()
        except Exception:
            # TODO: log error
            pass
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

async def scan_runner_loop():
    while True:
        try:
            await handle_queued_scans()
        except Exception:
            # TODO: log error
            pass
        await asyncio.sleep(1)

async def handle_schedules():
    conn = get_connection()
    now = datetime.now(timezone.utc)
    rows = conn.execute(
        """
        SELECT id, scan_type, target, interval_seconds
        FROM scan_schedules
        WHERE enabled = TRUE AND (next_run_at IS NULL OR next_run_at <= ?)
        """,
        [now],
    ).fetchall()

    for sched_id, scan_type, target, interval in rows:
        # insert scan row
        scan_id = await enqueue_scan(target, scan_type)
        # update schedule times
        next_run_at = now + timedelta(seconds=interval)
        conn.execute(
            """
            UPDATE scan_schedules
            SET last_run_at = ?, next_run_at = ?
            WHERE id = ?
            """,
            [now, next_run_at, sched_id],
        )

async def enqueue_scan(target: str, scan_type: str) -> str:
    from uuid import uuid4
    conn = get_connection()
    scan_id = str(uuid4())
    now = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT INTO scans (id, target, scan_type, status, created_at)
        VALUES (?, ?, ?, 'queued', ?)
        """,
        [scan_id, target, scan_type, now],
    )
    return scan_id

async def handle_queued_scans():
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, target, scan_type
        FROM scans
        WHERE status = 'queued'
        ORDER BY created_at
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return

    scan_id, target, scan_type = row
    now = datetime.now(timezone.utc)
    conn.execute(
        "UPDATE scans SET status='running', started_at=? WHERE id=?", [now, scan_id]
    )

    try:
        await run_scan_job(scan_id, target, scan_type)
        conn.execute(
            "UPDATE scans SET status='done', finished_at=? WHERE id=?",
            [datetime.now(timezone.utc), scan_id],
        )
    except Exception as exc:
        conn.execute(
            "UPDATE scans SET status='error', finished_at=?, error_message=? WHERE id=?",
            [datetime.now(timezone.utc), str(exc), scan_id],
        )
