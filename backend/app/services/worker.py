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
    from app.services.mqtt import MQTTManager
    while True:
        try:
            # 1. Handle background schedules
            await handle_schedules()
            
            # 2. Check MQTT Health
            MQTTManager.get_instance().check_health()
            
        except Exception as e:
            logger.error(f"Error in scheduler_loop: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

async def scan_runner_loop():
    last_cleanup = datetime.min.replace(tzinfo=timezone.utc)
    while True:
        try:
            now = datetime.now(timezone.utc)
            # Only cleanup stale scans every 60 seconds
            run_cleanup = (now - last_cleanup).total_seconds() > 60
            
            job = await handle_queued_scans(cleanup=run_cleanup)
            if run_cleanup:
                last_cleanup = now
                
        except Exception as e:
            logger.error(f"Error in scan_runner_loop: {e}")
            
        # Sleep 2s to reduce idle CPU (responsiveness is still good enough)
        await asyncio.sleep(2)

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
            
            # 3. Handle OpenWRT Integration
            trigger_openwrt = False
            openwrt_conf = {}
            try:
                # Check for integrations table existence
                if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='integrations'").fetchone():
                    ow_row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
                    if ow_row:
                        ow_config = json.loads(ow_row[0])
                        # Config: url, username, password, interval (mins), last_sync (iso)
                        if ow_config.get("url") and ow_config.get("username"):
                            interval_mins = int(ow_config.get("interval", 15))
                            last_sync_str = ow_config.get("last_sync")
                            
                            should_run = False
                            if not last_sync_str:
                                should_run = True
                            else:
                                last_sync = datetime.fromisoformat(last_sync_str)
                                if now >= last_sync + timedelta(minutes=interval_mins):
                                    should_run = True
                            
                            if should_run:
                                trigger_openwrt = True
                                openwrt_conf = ow_config
            except Exception as e:
                logger.error(f"Error checking OpenWRT schedule: {e}")

            return trigger_global, scan_subnets_raw, rows, now, trigger_openwrt, openwrt_conf
        finally:
            conn.close()

    trigger_global, scan_subnets_raw, schedule_rows, now, trigger_openwrt, openwrt_conf = await asyncio.to_thread(sync_check)

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

    if trigger_openwrt:
        from app.services.openwrt import OpenWRTClient
        async def run_openwrt_sync():
            try:
                logger.info("Starting scheduled OpenWRT sync...")
                client = OpenWRTClient(openwrt_conf["url"], openwrt_conf["username"], openwrt_conf.get("password"))
                await asyncio.to_thread(client.sync)
                
                # Update last_sync
                def update_ts():
                    conn = get_connection()
                    try:
                        # fetch again to merge
                        row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
                        if row:
                            c = json.loads(row[0])
                            c["last_sync"] = datetime.now(timezone.utc).isoformat()
                            conn.execute("UPDATE integrations SET config = ? WHERE name = 'openwrt'", [json.dumps(c)])
                            conn.commit()
                    finally: conn.close()
                await asyncio.to_thread(update_ts)
                logger.info("OpenWRT sync completed.")
            except Exception as e:
                logger.error(f"OpenWRT sync failed: {e}")
        
        asyncio.create_task(run_openwrt_sync())

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

async def handle_queued_scans(cleanup=False):
    def get_job():
        conn = get_connection()
        try:
            now = datetime.now(timezone.utc)
            
            if cleanup:
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
