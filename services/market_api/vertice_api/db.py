from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Iterator

from .catalog import AssetDefinition


SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    ticker TEXT PRIMARY KEY,
    provider_symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    market TEXT NOT NULL,
    currency TEXT NOT NULL,
    benchmark TEXT,
    underlying TEXT,
    bdr_ratio REAL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS daily_prices (
    ticker TEXT NOT NULL REFERENCES assets(ticker),
    price_date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL NOT NULL,
    adjusted_close REAL NOT NULL,
    volume REAL,
    provider TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (ticker, price_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker_date
ON daily_prices(ticker, price_date DESC);

CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    rows_received INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA)
            conn.execute("PRAGMA optimize")

    def seed_assets(self, assets: Iterable[AssetDefinition]) -> None:
        sql = """
        INSERT INTO assets (
            ticker, provider_symbol, name, asset_class, market, currency,
            benchmark, underlying, bdr_ratio
        ) VALUES (
            :ticker, :provider_symbol, :name, :asset_class, :market, :currency,
            :benchmark, :underlying, :bdr_ratio
        )
        ON CONFLICT(ticker) DO UPDATE SET
            provider_symbol=excluded.provider_symbol,
            name=excluded.name,
            asset_class=excluded.asset_class,
            market=excluded.market,
            currency=excluded.currency,
            benchmark=excluded.benchmark,
            underlying=excluded.underlying,
            bdr_ratio=excluded.bdr_ratio,
            active=1
        """
        with self.connection() as conn:
            conn.executemany(sql, [asset.as_record() for asset in assets])

    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]:
        query = "SELECT * FROM assets WHERE active=1"
        params: tuple[object, ...] = ()
        if asset_class:
            query += " AND asset_class=?"
            params = (asset_class,)
        query += " ORDER BY asset_class, ticker"
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def upsert_prices(self, ticker: str, rows: Iterable[dict[str, object]], provider: str) -> int:
        now = datetime.now(UTC).isoformat()
        payload = [{**row, "ticker": ticker, "provider": provider, "fetched_at": now} for row in rows]
        sql = """
        INSERT INTO daily_prices (
            ticker, price_date, open, high, low, close, adjusted_close,
            volume, provider, fetched_at
        ) VALUES (
            :ticker, :price_date, :open, :high, :low, :close, :adjusted_close,
            :volume, :provider, :fetched_at
        )
        ON CONFLICT(ticker, price_date) DO UPDATE SET
            open=excluded.open, high=excluded.high, low=excluded.low,
            close=excluded.close, adjusted_close=excluded.adjusted_close,
            volume=excluded.volume, provider=excluded.provider,
            fetched_at=excluded.fetched_at
        """
        with self.connection() as conn:
            conn.executemany(sql, payload)
        return len(payload)

    def get_prices(self, ticker: str, limit: int = 260) -> list[dict[str, object]]:
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM daily_prices WHERE ticker=?
                ORDER BY price_date DESC LIMIT ?""",
                (ticker, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def latest_fetch(self, ticker: str) -> datetime | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT MAX(fetched_at) AS fetched_at FROM daily_prices WHERE ticker=?",
                (ticker,),
            ).fetchone()
        value = row["fetched_at"] if row else None
        return datetime.fromisoformat(value) if value else None
