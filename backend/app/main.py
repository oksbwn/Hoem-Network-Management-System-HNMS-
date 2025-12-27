from fastapi import FastAPI
import asyncio
from app.core.db import init_db
from app.routers.config import router as config_router
from app.routers.scans import router as scans_router
from app.routers.devices import router as devices_router
from app.routers.schedules import router as schedules_router
from app.services.worker import scheduler_loop, scan_runner_loop

app = FastAPI(title="Network Scanner API")

@app.on_event("startup")
async def on_startup():
    init_db()
    asyncio.create_task(scheduler_loop())
    asyncio.create_task(scan_runner_loop())
    
app.include_router(config_router, prefix="/api/v1/config", tags=["config"])
app.include_router(scans_router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(schedules_router, prefix="/api/v1/schedules", tags=["schedules"])
