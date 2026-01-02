import duckdb
from pathlib import Path
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

_shared_conn: duckdb.DuckDBPyConnection = None

def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a cursor from a shared DuckDB connection.
    This pattern is much more stable on Windows to prevent 'Database is locked' errors.
    The shared connection handles the file lock, and each call returns a thread-safe cursor.
    """
    global _shared_conn
    if _shared_conn is None:
        settings = get_settings()
        db_path = Path(settings.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open the master connection for the process
        _shared_conn = duckdb.connect(str(db_path))
        
        # Optimize DuckDB for concurrency
        _shared_conn.execute("SET threads TO 4")
        _shared_conn.execute("SET memory_limit = '512MB'")
    
    # Return a cursor based on the master connection
    return _shared_conn.cursor()

def commit(conn: duckdb.DuckDBPyConnection) -> None:
    """Commits the given connection."""
    if conn:
        conn.commit()

def init_db() -> None:
    settings = get_settings()
    print(f"Initializing database at {settings.db_path}...")
    
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
                DROP TABLE IF EXISTS classification_rules;
            """)

        print(f"Loading schema from {settings.db_schema_path}...")
        schema_sql = Path(settings.db_schema_path).read_text(encoding="utf-8")
        conn.execute(schema_sql)
        
        # Migrations
        migrate_db(conn)
        
        # Seeding
        seed_classification_rules(conn)
        
        print("Database initialized successfully.")
        conn.commit()
    except Exception as e:
        print(f"ERROR during database initialization: {e}")
        raise e
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

    if 'status' not in col_names:
        print("Migration: Adding 'status' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN status TEXT DEFAULT 'unknown'")

    if 'ip_type' not in col_names:
        print("Migration: Adding 'ip_type' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN ip_type TEXT")

    if 'is_trusted' not in col_names:
        print("Migration: Adding 'is_trusted' column to 'devices'")
        conn.execute("ALTER TABLE devices ADD COLUMN is_trusted BOOLEAN DEFAULT FALSE")

    # Ensure device_status_history table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS device_status_history (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            status TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure device_traffic_history table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS device_traffic_history (
            id          TEXT PRIMARY KEY,
            device_id   TEXT NOT NULL,
            timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rx_bytes    BIGINT NOT NULL DEFAULT 0,
            tx_bytes    BIGINT NOT NULL DEFAULT 0,
            down_rate   BIGINT DEFAULT 0, 
            up_rate     BIGINT DEFAULT 0
        )
    """)

    # Migration for device_ports UNIQUE constraint
    # DuckDB doesn't allow adding UNIQUE to existing tables.
    # We check if it exists by looking at indexes or trying a dummy insert (or just check table_info if supported)
    # Safer: check if we've already run this migration using a config key or checking schema
    # PRAGMA table_info doesn't show UNIQUE easily, but we can check the table definition
    master = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'device_ports'").fetchone()
    if master and "UNIQUE" not in master[0]:
        print("Migration: Adding UNIQUE constraint to 'device_ports'")
        # Ensure we start fresh
        conn.execute("DROP TABLE IF EXISTS device_ports_new")
        conn.execute("""
            CREATE TABLE device_ports_new (
                device_id  TEXT NOT NULL,
                port       INTEGER NOT NULL,
                protocol   TEXT NOT NULL,
                service    TEXT,
                banner     TEXT,
                last_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, port, protocol)
            );
        """)
        # De-duplicate: Keep the most recent last_seen and any service/banner
        conn.execute("""
            INSERT INTO device_ports_new (device_id, port, protocol, service, banner, last_seen)
            SELECT device_id, port, protocol, arg_max(service, last_seen), arg_max(banner, last_seen), MAX(last_seen)
            FROM device_ports
            GROUP BY device_id, port, protocol
        """)
        conn.execute("DROP TABLE device_ports")
        conn.execute("ALTER TABLE device_ports_new RENAME TO device_ports")
    
    # 3. Normalize protocol to lowercase and deduplicate
    try:
        current_data = conn.execute("SELECT device_id, port, protocol FROM device_ports").fetchall()
        has_uppercase = any(d[2] != d[2].lower() for d in current_data)
        
        if has_uppercase:
            print("Migration: Normalizing protocols to lowercase and deduplicating...")
            # We'll use a temporary table to deduplicate
            conn.execute("CREATE TABLE device_ports_dedup (device_id TEXT, port INTEGER, protocol TEXT, service TEXT, banner TEXT, last_seen TIMESTAMP, UNIQUE(device_id, port, protocol))")
            
            # Insert with REPLACE to keep the latest service name/time for the lowercase version
            conn.execute("""
                INSERT OR REPLACE INTO device_ports_dedup (device_id, port, protocol, service, banner, last_seen)
                SELECT device_id, port, LOWER(protocol), service, banner, last_seen
                FROM device_ports
                ORDER BY last_seen ASC
            """)
            
            conn.execute("DROP TABLE device_ports")
            conn.execute("ALTER TABLE device_ports_dedup RENAME TO device_ports")
            print("Migration: Protocols normalized successfully.")
    except Exception as e:
        print(f"Migration error (normalization): {e}")



    conn.commit()

def seed_classification_rules(conn: duckdb.DuckDBPyConnection) -> None:
    """Seeds the classification_rules table from initial_rules.json if empty."""
    try:
        count = conn.execute("SELECT count(*) FROM classification_rules").fetchone()[0]
        if count > 0:
            return

        print("Seeding initial classification rules...")
        import json
        import uuid
        from pathlib import Path
        
        rules_path = Path(__file__).parent.parent / "core" / "initial_rules.json"
        if not rules_path.exists():
            print(f"Warning: {rules_path} not found. Skipping seeding.")
            return
            
        rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
        for rule in rules_data:
            conn.execute(
                """
                INSERT INTO classification_rules (id, name, pattern_hostname, pattern_vendor, ports, device_type, icon, priority, is_builtin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    str(uuid.uuid4()),
                    rule["name"],
                    rule.get("pattern_hostname"),
                    rule.get("pattern_vendor"),
                    json.dumps(rule.get("ports", [])),
                    rule["device_type"],
                    rule["icon"],
                    rule.get("priority", 100),
                    True # is_builtin
                ]
            )
        conn.commit()
        print(f"Successfully seeded {len(rules_data)} classification rules.")
    except Exception as e:
        print(f"Error seeding classification rules: {e}")
