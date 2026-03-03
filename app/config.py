from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    default_since_hours: int = int(os.getenv("DEFAULT_SINCE_HOURS", "24"))
    ingest_interval_minutes: int = int(os.getenv("INGEST_INTERVAL_MINUTES", "15"))
    gdelt_timespan: str = os.getenv("GDELT_TIMESPAN", "7d")
    sources_file: str = os.getenv("SOURCES_FILE", "data/sources.yaml")
    max_age_days: int = int(os.getenv("MAX_AGE_DAYS", "30"))
    api_token: str = os.getenv("API_TOKEN", "")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()
