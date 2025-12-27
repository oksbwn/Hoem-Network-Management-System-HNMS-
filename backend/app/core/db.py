import duckdb
from pathlib import Path
from app.core.config import get_settings

_conn: duckdb.DuckDBPyConnection | None = None

def get_connection() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        settings = get_settings()
        db_path = Path(settings.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = duckdb.connect(str(db_path))
    return _conn

def init_db() -> None:
    settings = get_settings()
    print(f"Initializing database at {settings.db_path}...")
    conn = get_connection()

    if settings.db_init_mode == "recreate":
        print("Recreating database tables...")
        conn.execute("""
            DROP TABLE IF EXISTS scan_schedules;
            DROP TABLE IF EXISTS device_ports;
            DROP TABLE IF EXISTS devices;
            DROP TABLE IF EXISTS scan_results;
            DROP TABLE IF EXISTS scans;
            DROP TABLE IF EXISTS config;
        """)

    print(f"Loading schema from {settings.db_schema_path}...")
    schema_sql = Path(settings.db_schema_path).read_text(encoding="utf-8")
    conn.execute(schema_sql)
    print("Database initialized successfully.")
