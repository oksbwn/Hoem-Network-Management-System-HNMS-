import os
import shutil
import logging
import duckdb
from pathlib import Path
from app.core.config import get_settings
from app.core.db import get_connection, _shared_conn

logger = logging.getLogger(__name__)

class SystemService:
    @staticmethod
    def get_backup_path() -> Path:
        settings = get_settings()
        return Path(settings.db_path)

    @staticmethod
    def create_backup() -> Path:
        """
        DuckDB raw backup by briefly closing the connection and copying.
        Safe against background tasks via get_db_lock().
        """
        import tempfile
        from app.core.db import close_shared_connection, get_db_lock
        
        settings = get_settings()
        db_path = Path(settings.db_path)
        
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found at {db_path}")

        with get_db_lock():
            # 1. Checkpoint to flush WAL
            conn = get_connection()
            try:
                conn.execute("CHECKPOINT")
            finally:
                conn.close()

            # 2. Close shared connection to release file lock
            logger.info("Closing database connection for backup...")
            close_shared_connection()

            # 3. Create a temporary file path
            fd, temp_path = tempfile.mkstemp(suffix=".duckdb")
            os.close(fd)
            
            try:
                # 4. Copy the file
                logger.info(f"Copying database to {temp_path}...")
                shutil.copy2(db_path, temp_path)
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                logger.error(f"Backup copy failed: {e}")
                raise e
        
        return Path(temp_path)

    @staticmethod
    async def restore_backup(file_content: bytes):
        """
        Restore the database by replacing the current file.
        Holds get_db_lock() to prevent any other database access.
        """
        from app.core.db import get_db_lock
        settings = get_settings()
        db_path = Path(settings.db_path)
        backup_db_path = db_path.with_suffix(".duckdb.bak")

        logger.info(f"Starting database restore to {db_path}")

        def sync_restore():
            with get_db_lock():
                try:
                    # 1. Close the global connection
                    import app.core.db as db_module
                    db_module.close_shared_connection()

                    # 2. Backup current DB just in case
                    if db_path.exists():
                        shutil.copy2(db_path, backup_db_path)
                        logger.info(f"Created temporary backup at {backup_db_path}")

                    # 3. Overwrite with new content
                    with open(db_path, "wb") as f:
                        f.write(file_content)
                    
                    # 4. Remove WAL file if exists
                    wal_path = Path(str(db_path) + ".wal")
                    if wal_path.exists():
                        wal_path.unlink()

                    logger.info("Database file replaced successfully.")
                    
                    # 5. Initialize/Migrate immediately
                    logger.info("Initializing/Migrating restored database...")
                    db_module.init_db()
                    return True
                except Exception as e:
                    logger.error(f"Failed to restore database: {e}")
                    if backup_db_path.exists():
                        shutil.copy2(backup_db_path, db_path)
                        logger.info("Restored from temporary backup after failure.")
                    raise e
                finally:
                    if backup_db_path.exists():
                        backup_db_path.unlink()

        return await asyncio.to_thread(sync_restore)
