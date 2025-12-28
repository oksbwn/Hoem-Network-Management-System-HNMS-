import duckdb
from pathlib import Path
from app.core.config import get_settings

def get_connection() -> duckdb.DuckDBPyConnection:
    settings = get_settings()
    db_path = Path(settings.db_path)
    
    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Return a new connection. DuckDB is fast at this.
    return duckdb.connect(str(db_path))

def init_db() -> None:
    settings = get_settings()
    print(f"Initializing database at {settings.db_path}...")
    
    # Use a temporary connection for initialization
    conn = get_connection()
    try:
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
        
        # Migrations
        migrate_db(conn)
        
        print("Database initialized successfully.")
    finally:
        conn.close()

def migrate_db(conn: duckdb.DuckDBPyConnection) -> None:
    """Adds missing columns to existing tables."""
    # Check if vendor/icon exist in devices
    cols = conn.execute("PRAGMA table_info('devices')").fetchall()
    col_names = [c[1] for c in cols]
    
    if 'vendor' not in col_names:
        print("Migration: Adding 'vendor' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN vendor TEXT")
    
    if 'icon' not in col_names:
        print("Migration: Adding 'icon' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN icon TEXT")

    if 'open_ports' not in col_names:
        print("Migration: Adding 'open_ports' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN open_ports TEXT")
