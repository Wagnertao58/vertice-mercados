from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    dashboard_origin: str
    cache_minutes: int
    request_timeout_seconds: int


def load_settings() -> Settings:
    service_root = Path(__file__).resolve().parents[1]
    default_db = service_root / "data" / "vertice.db"
    return Settings(
        database_path=Path(os.getenv("VERTICE_DATABASE_PATH", default_db)),
        dashboard_origin=os.getenv("DASHBOARD_ORIGIN", "http://localhost:3000"),
        cache_minutes=int(os.getenv("MARKET_CACHE_MINUTES", "30")),
        request_timeout_seconds=int(os.getenv("MARKET_REQUEST_TIMEOUT", "15")),
    )
