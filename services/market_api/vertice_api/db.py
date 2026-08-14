from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from .catalog import AssetDefinition


SQLITE_SCHEMA = (
    """
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
    )
    """,
    """
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
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker_date
    ON daily_prices(ticker, price_date DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT NOT NULL,
        rows_received INTEGER NOT NULL DEFAULT 0,
        error_message TEXT
    )
    """,
)

POSTGRES_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS assets (
        ticker TEXT PRIMARY KEY,
        provider_symbol TEXT NOT NULL,
        name TEXT NOT NULL,
        asset_class TEXT NOT NULL,
        market TEXT NOT NULL,
        currency TEXT NOT NULL,
        benchmark TEXT,
        underlying TEXT,
        bdr_ratio DOUBLE PRECISION,
        active BOOLEAN NOT NULL DEFAULT TRUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_prices (
        ticker TEXT NOT NULL REFERENCES assets(ticker),
        price_date TEXT NOT NULL,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION NOT NULL,
        adjusted_close DOUBLE PRECISION NOT NULL,
        volume DOUBLE PRECISION,
        provider TEXT NOT NULL,
        fetched_at TEXT NOT NULL,
        PRIMARY KEY (ticker, price_date)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker_date
    ON daily_prices(ticker, price_date DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_runs (
        id BIGSERIAL PRIMARY KEY,
        ticker TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        status TEXT NOT NULL,
        rows_received INTEGER NOT NULL DEFAULT 0,
        error_message TEXT
    )
    """,
)


class _Backend(Protocol):
    name: str

    def initialize(self) -> None: ...
    def seed_assets(self, assets: Iterable[AssetDefinition]) -> None: ...
    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]: ...
    def upsert_prices(self, ticker: str, rows: Iterable[dict[str, object]], provider: str) -> int: ...
    def get_prices(self, ticker: str, limit: int = 260) -> list[dict[str, object]]: ...
    def latest_fetch(self, ticker: str) -> datetime | None: ...
    def ping(self) -> None: ...


class _SqliteBackend:
    name = "sqlite"

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
            for statement in SQLITE_SCHEMA:
                conn.execute(statement)
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

    def ping(self) -> None:
        with self.connection() as conn:
            conn.execute("SELECT 1").fetchone()


class _PostgresBackend:
    name = "postgresql"

    def __init__(self, database_url: str):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgreSQL requires psycopg; install the production requirements") from exc
        self._psycopg = psycopg
        self._dict_row = dict_row
        self.database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)

    @contextmanager
    def connection(self):
        with self._psycopg.connect(self.database_url, row_factory=self._dict_row) as conn:
            yield conn

    def initialize(self) -> None:
        with self.connection() as conn:
            for statement in POSTGRES_SCHEMA:
                conn.execute(statement)

    def seed_assets(self, assets: Iterable[AssetDefinition]) -> None:
        sql = """
        INSERT INTO assets (
            ticker, provider_symbol, name, asset_class, market, currency,
            benchmark, underlying, bdr_ratio
        ) VALUES (
            %(ticker)s, %(provider_symbol)s, %(name)s, %(asset_class)s, %(market)s,
            %(currency)s, %(benchmark)s, %(underlying)s, %(bdr_ratio)s
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
            active=TRUE
        """
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(sql, [asset.as_record() for asset in assets])

    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]:
        query = "SELECT * FROM assets WHERE active=TRUE"
        params: tuple[object, ...] = ()
        if asset_class:
            query += " AND asset_class=%s"
            params = (asset_class,)
        query += " ORDER BY asset_class, ticker"
        with self.connection() as conn:
            return list(conn.execute(query, params).fetchall())

    def upsert_prices(self, ticker: str, rows: Iterable[dict[str, object]], provider: str) -> int:
        now = datetime.now(UTC).isoformat()
        payload = [{**row, "ticker": ticker, "provider": provider, "fetched_at": now} for row in rows]
        sql = """
        INSERT INTO daily_prices (
            ticker, price_date, open, high, low, close, adjusted_close,
            volume, provider, fetched_at
        ) VALUES (
            %(ticker)s, %(price_date)s, %(open)s, %(high)s, %(low)s, %(close)s,
            %(adjusted_close)s, %(volume)s, %(provider)s, %(fetched_at)s
        )
        ON CONFLICT(ticker, price_date) DO UPDATE SET
            open=excluded.open, high=excluded.high, low=excluded.low,
            close=excluded.close, adjusted_close=excluded.adjusted_close,
            volume=excluded.volume, provider=excluded.provider,
            fetched_at=excluded.fetched_at
        """
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(sql, payload)
        return len(payload)

    def get_prices(self, ticker: str, limit: int = 260) -> list[dict[str, object]]:
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM daily_prices WHERE ticker=%s
                ORDER BY price_date DESC LIMIT %s""",
                (ticker, limit),
            ).fetchall()
        return list(reversed(rows))

    def latest_fetch(self, ticker: str) -> datetime | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT MAX(fetched_at) AS fetched_at FROM daily_prices WHERE ticker=%s",
                (ticker,),
            ).fetchone()
        value = row["fetched_at"] if row else None
        return datetime.fromisoformat(value) if value else None

    def ping(self) -> None:
        with self.connection() as conn:
            conn.execute("SELECT 1").fetchone()


class Database:
    def __init__(self, target: str | Path):
        if isinstance(target, Path):
            self._backend: _Backend = _SqliteBackend(target)
        elif target.startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
            self._backend = _PostgresBackend(target)
        elif target.startswith("sqlite:///"):
            self._backend = _SqliteBackend(Path(target.removeprefix("sqlite:///")))
        else:
            self._backend = _SqliteBackend(Path(target))

    @property
    def backend_name(self) -> str:
        return self._backend.name

    def initialize(self) -> None:
        self._backend.initialize()

    def seed_assets(self, assets: Iterable[AssetDefinition]) -> None:
        self._backend.seed_assets(assets)

    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]:
        return self._backend.list_assets(asset_class)

    def upsert_prices(self, ticker: str, rows: Iterable[dict[str, object]], provider: str) -> int:
        return self._backend.upsert_prices(ticker, rows, provider)

    def get_prices(self, ticker: str, limit: int = 260) -> list[dict[str, object]]:
        return self._backend.get_prices(ticker, limit)

    def latest_fetch(self, ticker: str) -> datetime | None:
        return self._backend.latest_fetch(ticker)

    def ping(self) -> None:
        self._backend.ping()

