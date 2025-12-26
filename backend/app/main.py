from fastapi import FastAPI
from app.core.db import init_db
from app.routers import config as config_router
from app.routers import scans as scans_router
from app.routers import devices as devices_router
from app.routers import schedules as schedules_router

app = FastAPI(title="Network Scanner API")

@app.on_event("startup")
def on_startup():
    init_db()
    asyncio.create_task(scheduler_loop())
    asyncio.create_task(scan_runner_loop())
    
app.include_router(config_router.router, prefix="/api/v1/config", tags=["config"])
app.include_router(scans_router.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(devices_router.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(schedules_router.router, prefix="/api/v1/schedules", tags=["schedules"])
