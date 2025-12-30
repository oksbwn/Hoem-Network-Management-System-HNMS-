-- config
CREATE TABLE IF NOT EXISTS config (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- scans
CREATE TABLE IF NOT EXISTS scans (
    id           TEXT PRIMARY KEY,
    target       TEXT NOT NULL,
    scan_type    TEXT NOT NULL,
    options      TEXT,
    status       TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at   TIMESTAMP,
    finished_at  TIMESTAMP,
    error_message TEXT
);

-- scan_results
CREATE TABLE IF NOT EXISTS scan_results (
    id          TEXT PRIMARY KEY,
    scan_id     TEXT NOT NULL,
    ip          TEXT NOT NULL,
    mac         TEXT,
    hostname    TEXT,
    open_ports  TEXT,
    os          TEXT,
    first_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- devices
CREATE TABLE IF NOT EXISTS devices (
    id            TEXT PRIMARY KEY,
    ip            TEXT NOT NULL,
    mac           TEXT,
    name          TEXT,
    display_name  TEXT,
    device_type   TEXT,
    first_seen    TIMESTAMP,
    last_seen     TIMESTAMP,
    internet_path TEXT,
    vendor        TEXT,
    icon          TEXT,
    status TEXT DEFAULT 'unknown',
    open_ports    TEXT,
    attributes    TEXT
);

CREATE TABLE IF NOT EXISTS device_status_history (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    status TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- device_ports
CREATE TABLE IF NOT EXISTS device_ports (
    device_id  TEXT NOT NULL,
    port       INTEGER NOT NULL,
    protocol   TEXT NOT NULL,
    service    TEXT,
    banner     TEXT,
    last_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, port, protocol)
);

-- scan_schedules
CREATE TABLE IF NOT EXISTS scan_schedules (
    id               TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    scan_type        TEXT NOT NULL,
    target           TEXT NOT NULL,
    interval_seconds INTEGER NOT NULL,
    enabled          BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at      TIMESTAMP,
    next_run_at      TIMESTAMP
);

-- classification_rules
CREATE TABLE IF NOT EXISTS classification_rules (
    id               TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    pattern_hostname TEXT,
    pattern_vendor   TEXT,
    ports            TEXT, -- Store as JSON array string
    device_type      TEXT NOT NULL,
    icon             TEXT NOT NULL,
    priority         INTEGER NOT NULL DEFAULT 100,
    is_builtin       BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
