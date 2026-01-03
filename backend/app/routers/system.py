from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.services.system import SystemService
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

def cleanup_temp_file(path: Path):
    if path.exists():
        try:
            os.remove(path)
            logger.info(f"Cleaned up temporary backup file: {path}")
        except Exception as e:
            logger.error(f"Failed to cleanup temporary file {path}: {e}")

@router.get("/backup")
async def download_backup(background_tasks: BackgroundTasks):
    """
    Downloads the raw DuckDB database file.
    """
    try:
        temp_db_path = SystemService.create_backup()
        background_tasks.add_task(cleanup_temp_file, temp_db_path)
        
        return FileResponse(
            path=temp_db_path,
            filename="network_scanner_backup.duckdb",
            media_type='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    """
    Uploads and restores a DuckDB database file.
    """
    if not file.filename.endswith(".duckdb"):
        raise HTTPException(status_code=400, detail="Only .duckdb files are allowed")
    
    try:
        content = await file.read()
        await SystemService.restore_backup(content)
        return {"status": "success", "message": "Database restored successfully. Server may need a moment to reconnect."}
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
