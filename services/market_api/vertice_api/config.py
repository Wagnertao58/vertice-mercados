from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    dashboard_origin: str
    cache_minutes: int
    request_timeout_seconds: int


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def load_settings() -> Settings:
    service_root = Path(__file__).resolve().parents[1]
    default_db = service_root / "data" / "vertice.db"
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        database_path = Path(os.getenv("VERTICE_DATABASE_PATH", default_db))
        database_url = _sqlite_url(database_path)
    return Settings(
        database_url=database_url,
        dashboard_origin=os.getenv("DASHBOARD_ORIGIN", "http://localhost:3000"),
        cache_minutes=int(os.getenv("MARKET_CACHE_MINUTES", "30")),
        request_timeout_seconds=int(os.getenv("MARKET_REQUEST_TIMEOUT", "15")),
    )
