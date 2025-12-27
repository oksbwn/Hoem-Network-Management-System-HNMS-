from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "LAN Scanner"
    app_env: str = "development"
    app_debug: bool = False

    db_path: str = "data/network_scanner_v2.duckdb"
    db_schema_path: str = "app/schema.sql"
    db_init_mode: str = "create"  # create | recreate

    max_concurrent_scans: int = 4
    default_subnet: str = "192.168.1.0/24"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
