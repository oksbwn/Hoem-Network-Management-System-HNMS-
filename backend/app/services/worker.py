import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
import json
from app.core.db import get_connection
from app.services.scans import run_scan_job

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 5

async def scheduler_loop():
    while True:
        try:
            await handle_schedules()
        except Exception as e:
            logger.error(f"Error in scheduler_loop: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

async def scan_runner_loop():
    while True:
        try:
            await handle_queued_scans()
        except Exception as e:
            logger.error(f"Error in scan_runner_loop: {e}")
        await asyncio.sleep(1)

async def handle_schedules():
    def sync_check():
        conn = get_connection()
        try:
            now = datetime.now(timezone.utc)
            # 1. Fetch Config for Global Discovery
            config_rows = conn.execute("SELECT key, value FROM config WHERE key IN ('scan_subnets', 'scan_interval', 'last_discovery_run_at')").fetchall()
            config = {r[0]: r[1] for r in config_rows}
            
            scan_subnets_raw = config.get('scan_subnets')
            scan_interval = int(config.get('scan_interval', '300'))
            last_run_str = config.get('last_discovery_run_at')
            
            last_run = None
            if last_run_str:
                try:
                    last_run = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
                    if last_run.tzinfo is None: last_run = last_run.replace(tzinfo=timezone.utc)
                except: pass
                
            trigger_global = False
            if scan_subnets_raw:
                if last_run is None:
                    logger.info("No last run record found for global discovery. Triggering now.")
                    trigger_global = True
                elif now >= last_run + timedelta(seconds=scan_interval):
                    diff = (now - last_run).total_seconds()
                    logger.info(f"Global discovery interval reached ({diff}s since last run, interval: {scan_interval}s). Triggering.")
                    trigger_global = True
                else:
                    wait_time = (last_run + timedelta(seconds=scan_interval) - now).total_seconds()
                    # logger.debug(f"Global discovery interval not reached. Waiting {wait_time:.1f}s more.")
                    pass

            # 2. Handle specific schedules
            rows = conn.execute(
                """
                SELECT id, scan_type, target, interval_seconds
                FROM scan_schedules
                WHERE enabled = TRUE AND (next_run_at IS NULL OR next_run_at <= ?)
                """,
                [now],
            ).fetchall()
            
            return trigger_global, scan_subnets_raw, rows, now
        finally:
            conn.close()

    trigger_global, scan_subnets_raw, schedule_rows, now = await asyncio.to_thread(sync_check)

    if trigger_global:
        target = None
        try:
            subnets = json.loads(scan_subnets_raw)
            if isinstance(subnets, list) and subnets:
                target = " ".join(sorted([s.strip() for s in subnets if s.strip()]))
        except:
            target = scan_subnets_raw.strip()
        
        if target:
            enqueued = await enqueue_scan(target, "arp")
            if enqueued:
                def update_last_run():
                    conn = get_connection()
                    try:
                        # Use isoformat(timespec='seconds') for cleaner storage
                        conn.execute("INSERT OR REPLACE INTO config (key, value, updated_at) VALUES ('last_discovery_run_at', ?, ?)", [now.isoformat(), now])
                        conn.commit()
                    finally: conn.close()
                await asyncio.to_thread(update_last_run)

    for sched_id, scan_type, target, interval in schedule_rows:
        enqueued = await enqueue_scan(target, scan_type)
        if enqueued:
            def update_sched():
                conn = get_connection()
                try:
                    next_run_at = now + timedelta(seconds=interval)
                    conn.execute("UPDATE scan_schedules SET last_run_at = ?, next_run_at = ? WHERE id = ?", [now, next_run_at, sched_id])
                    conn.commit()
                finally: conn.close()
            await asyncio.to_thread(update_sched)

async def enqueue_scan(target: str, scan_type: str) -> Optional[str]:
    from uuid import uuid4
    def sync_enqueue():
        conn = get_connection()
        try:
            t = target.strip()
            now = datetime.now(timezone.utc)
            
            # Check for exactly same scan (target + type) already queued or running
            active = conn.execute(
                "SELECT id FROM scans WHERE status IN ('queued', 'running') AND target = ? AND scan_type = ?", 
                [t, scan_type]
            ).fetchone()
            
            if active:
                logger.info(f"Scan for {t} ({scan_type}) already in progress. Skipping.")
                return None

            scan_id = str(uuid4())
            conn.execute("INSERT INTO scans (id, target, scan_type, status, created_at) VALUES (?, ?, ?, 'queued', ?)", [scan_id, t, scan_type, now])
            conn.commit()
            return scan_id
        finally:
            conn.close()
    return await asyncio.to_thread(sync_enqueue)

async def handle_queued_scans():
    def get_job():
        conn = get_connection()
        try:
            now = datetime.now(timezone.utc)
            # Re-clean stale scans (interrupted)
            stale_cutoff = now - timedelta(minutes=20)
            conn.execute(
                "UPDATE scans SET status='error', finished_at=?, error_message='Job timed out or interrupted' WHERE status='running' AND started_at < ?", 
                [now, stale_cutoff]
            )
            
            # One scan at a time for stability on Pi
            running = conn.execute("SELECT id FROM scans WHERE status = 'running'").fetchone()
            if running:
                conn.commit()
                return None
            
            row = conn.execute("SELECT id, target, scan_type FROM scans WHERE status = 'queued' ORDER BY created_at LIMIT 1").fetchone()
            if row:
                conn.execute("UPDATE scans SET status='running', started_at=? WHERE id=?", [now, row[0]])
            
            conn.commit()
            return row
        finally:
            conn.close()

    job = await asyncio.to_thread(get_job)
    if not job: return
    
    scan_id, target, scan_type = job
    try:
        await run_scan_job(scan_id, target, scan_type)
        # Note: run_scan_job now marks itself as 'done' or 'error' 
    except Exception as e:
        logger.error(f"Unexpected top-level worker error for {scan_id}: {e}")
