from fastapi import FastAPI
import asyncio
from app.core.db import init_db
from app.routers.config import router as config_router
from app.routers.scans import router as scans_router
from app.routers.devices import router as devices_router
from app.routers.schedules import router as schedules_router
from app.services.worker import scheduler_loop, scan_runner_loop
from app.routers.ssh import router as ssh_router

app = FastAPI(title="Network Scanner API")

def cleanup_stale_scans():
    from app.core.db import get_connection
    from datetime import datetime, timezone
    print("DEBUG: Cleaning up stale scans from previous run...")
    conn = get_connection()
    try:
        # Mark running or queued scans as interrupted on startup
        conn.execute(
            "UPDATE scans SET status = 'interrupted', finished_at = ?, error_message = 'Interrupted by server restart' WHERE status IN ('running', 'queued')",
            [datetime.now(timezone.utc)]
        )
    except Exception as e:
        print(f"DEBUG ERROR during startup cleanup: {e}")
    finally:
        conn.close()

@app.on_event("startup")
async def on_startup():
    cleanup_stale_scans()
    init_db()
    from app.services.oui_downloader import ensure_oui_data
    asyncio.create_task(ensure_oui_data())
    asyncio.create_task(scheduler_loop())
    asyncio.create_task(scan_runner_loop())
    
app.include_router(config_router, prefix="/api/v1/config", tags=["config"])
app.include_router(scans_router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(schedules_router, prefix="/api/v1/schedules", tags=["schedules"])
app.include_router(ssh_router, prefix="/api/v1/ssh", tags=["ssh"])
# Force Reload
# Trigger Migration
