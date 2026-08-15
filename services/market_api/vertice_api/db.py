from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from .catalog import AssetDefinition
from .macro_catalog import MacroSeriesDefinition


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
    """
    CREATE TABLE IF NOT EXISTS macro_series (
        code TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        provider_code TEXT NOT NULL,
        name TEXT NOT NULL,
        country TEXT NOT NULL,
        category TEXT NOT NULL,
        unit TEXT NOT NULL,
        frequency TEXT NOT NULL,
        transform TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS macro_observations (
        series_code TEXT NOT NULL REFERENCES macro_series(code),
        observation_date TEXT NOT NULL,
        value REAL NOT NULL,
        provider TEXT NOT NULL,
        fetched_at TEXT NOT NULL,
        PRIMARY KEY (series_code, observation_date)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_macro_observations_code_date
    ON macro_observations(series_code, observation_date DESC)
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
    """
    CREATE TABLE IF NOT EXISTS macro_series (
        code TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        provider_code TEXT NOT NULL,
        name TEXT NOT NULL,
        country TEXT NOT NULL,
        category TEXT NOT NULL,
        unit TEXT NOT NULL,
        frequency TEXT NOT NULL,
        transform TEXT NOT NULL,
        active BOOLEAN NOT NULL DEFAULT TRUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS macro_observations (
        series_code TEXT NOT NULL REFERENCES macro_series(code),
        observation_date TEXT NOT NULL,
        value DOUBLE PRECISION NOT NULL,
        provider TEXT NOT NULL,
        fetched_at TEXT NOT NULL,
        PRIMARY KEY (series_code, observation_date)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_macro_observations_code_date
    ON macro_observations(series_code, observation_date DESC)
    """,
)


class _Backend(Protocol):
    name: str

    def initialize(self) -> None: ...
    def seed_assets(self, assets: Iterable[AssetDefinition]) -> None: ...
    def seed_macro_series(self, series: Iterable[MacroSeriesDefinition]) -> None: ...
    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]: ...
    def list_macro_series(self) -> list[dict[str, object]]: ...
    def upsert_prices(self, ticker: str, rows: Iterable[dict[str, object]], provider: str) -> int: ...
    def upsert_macro_observations(self, code: str, rows: Iterable[dict[str, object]], provider: str) -> int: ...
    def get_prices(self, ticker: str, limit: int = 260) -> list[dict[str, object]]: ...
    def get_macro_observations(self, code: str, limit: int = 2000) -> list[dict[str, object]]: ...
    def latest_fetch(self, ticker: str) -> datetime | None: ...
    def latest_macro_fetch(self, code: str) -> datetime | None: ...
    def create_sync_run(self, ticker: str) -> int: ...
    def finish_sync_run(self, run_id: int, status: str, rows_received: int, error_message: str | None = None) -> None: ...
    def data_health(self) -> list[dict[str, object]]: ...
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

    def seed_macro_series(self, series: Iterable[MacroSeriesDefinition]) -> None:
        sql = """
        INSERT INTO macro_series (
            code, provider, provider_code, name, country, category, unit, frequency, transform
        ) VALUES (
            :code, :provider, :provider_code, :name, :country, :category, :unit, :frequency, :transform
        )
        ON CONFLICT(code) DO UPDATE SET
            provider=excluded.provider, provider_code=excluded.provider_code,
            name=excluded.name, country=excluded.country, category=excluded.category,
            unit=excluded.unit, frequency=excluded.frequency, transform=excluded.transform, active=1
        """
        with self.connection() as conn:
            conn.executemany(sql, [item.as_record() for item in series])

    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]:
        query = "SELECT * FROM assets WHERE active=1"
        params: tuple[object, ...] = ()
        if asset_class:
            query += " AND asset_class=?"
            params = (asset_class,)
        query += " ORDER BY asset_class, ticker"
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def list_macro_series(self) -> list[dict[str, object]]:
        with self.connection() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM macro_series WHERE active=1 ORDER BY country, category, code"
            ).fetchall()]

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

    def upsert_macro_observations(self, code: str, rows: Iterable[dict[str, object]], provider: str) -> int:
        now = datetime.now(UTC).isoformat()
        payload = [{**row, "series_code": code, "provider": provider, "fetched_at": now} for row in rows]
        sql = """
        INSERT INTO macro_observations (series_code, observation_date, value, provider, fetched_at)
        VALUES (:series_code, :observation_date, :value, :provider, :fetched_at)
        ON CONFLICT(series_code, observation_date) DO UPDATE SET
            value=excluded.value, provider=excluded.provider, fetched_at=excluded.fetched_at
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

    def get_macro_observations(self, code: str, limit: int = 2000) -> list[dict[str, object]]:
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM macro_observations WHERE series_code=?
                ORDER BY observation_date DESC LIMIT ?""",
                (code, limit),
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

    def latest_macro_fetch(self, code: str) -> datetime | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT MAX(fetched_at) AS fetched_at FROM macro_observations WHERE series_code=?",
                (code,),
            ).fetchone()
        value = row["fetched_at"] if row else None
        return datetime.fromisoformat(value) if value else None

    def create_sync_run(self, ticker: str) -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO sync_runs (ticker, started_at, status) VALUES (?, ?, ?)",
                (ticker, datetime.now(UTC).isoformat(), "running"),
            )
            return int(cursor.lastrowid)

    def finish_sync_run(self, run_id: int, status: str, rows_received: int, error_message: str | None = None) -> None:
        with self.connection() as conn:
            conn.execute(
                """UPDATE sync_runs SET finished_at=?, status=?, rows_received=?, error_message=?
                WHERE id=?""",
                (datetime.now(UTC).isoformat(), status, rows_received, error_message, run_id),
            )

    def data_health(self) -> list[dict[str, object]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT a.ticker, a.name, a.market, a.asset_class,
                    COUNT(p.price_date) AS price_rows,
                    MIN(p.price_date) AS first_price_date,
                    MAX(p.price_date) AS last_price_date,
                    MAX(p.fetched_at) AS last_fetched_at,
                    latest.status AS last_sync_status,
                    latest.finished_at AS last_sync_at,
                    latest.rows_received AS last_rows_received,
                    latest.error_message AS last_error
                FROM assets a
                LEFT JOIN daily_prices p ON p.ticker=a.ticker
                LEFT JOIN (
                    SELECT ticker, status, finished_at, rows_received, error_message
                    FROM (
                        SELECT ticker, status, finished_at, rows_received, error_message,
                            ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY started_at DESC, id DESC) AS row_number
                        FROM sync_runs
                    ) ranked
                    WHERE row_number=1
                ) latest ON latest.ticker=a.ticker
                WHERE a.active=1
                GROUP BY a.ticker, a.name, a.market, a.asset_class,
                    latest.status, latest.finished_at, latest.rows_received, latest.error_message
                ORDER BY a.asset_class, a.ticker
                """
            ).fetchall()
        return [dict(row) for row in rows]

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

    def seed_macro_series(self, series: Iterable[MacroSeriesDefinition]) -> None:
        sql = """
        INSERT INTO macro_series (
            code, provider, provider_code, name, country, category, unit, frequency, transform
        ) VALUES (
            %(code)s, %(provider)s, %(provider_code)s, %(name)s, %(country)s,
            %(category)s, %(unit)s, %(frequency)s, %(transform)s
        )
        ON CONFLICT(code) DO UPDATE SET
            provider=excluded.provider, provider_code=excluded.provider_code,
            name=excluded.name, country=excluded.country, category=excluded.category,
            unit=excluded.unit, frequency=excluded.frequency, transform=excluded.transform, active=TRUE
        """
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(sql, [item.as_record() for item in series])

    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]:
        query = "SELECT * FROM assets WHERE active=TRUE"
        params: tuple[object, ...] = ()
        if asset_class:
            query += " AND asset_class=%s"
            params = (asset_class,)
        query += " ORDER BY asset_class, ticker"
        with self.connection() as conn:
            return list(conn.execute(query, params).fetchall())

    def list_macro_series(self) -> list[dict[str, object]]:
        with self.connection() as conn:
            return list(conn.execute(
                "SELECT * FROM macro_series WHERE active=TRUE ORDER BY country, category, code"
            ).fetchall())

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

    def upsert_macro_observations(self, code: str, rows: Iterable[dict[str, object]], provider: str) -> int:
        now = datetime.now(UTC).isoformat()
        payload = [{**row, "series_code": code, "provider": provider, "fetched_at": now} for row in rows]
        sql = """
        INSERT INTO macro_observations (series_code, observation_date, value, provider, fetched_at)
        VALUES (%(series_code)s, %(observation_date)s, %(value)s, %(provider)s, %(fetched_at)s)
        ON CONFLICT(series_code, observation_date) DO UPDATE SET
            value=excluded.value, provider=excluded.provider, fetched_at=excluded.fetched_at
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

    def get_macro_observations(self, code: str, limit: int = 2000) -> list[dict[str, object]]:
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT * FROM macro_observations WHERE series_code=%s
                ORDER BY observation_date DESC LIMIT %s""",
                (code, limit),
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

    def latest_macro_fetch(self, code: str) -> datetime | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT MAX(fetched_at) AS fetched_at FROM macro_observations WHERE series_code=%s",
                (code,),
            ).fetchone()
        value = row["fetched_at"] if row else None
        return datetime.fromisoformat(value) if value else None

    def create_sync_run(self, ticker: str) -> int:
        with self.connection() as conn:
            row = conn.execute(
                """INSERT INTO sync_runs (ticker, started_at, status)
                VALUES (%s, %s, %s) RETURNING id""",
                (ticker, datetime.now(UTC).isoformat(), "running"),
            ).fetchone()
        return int(row["id"])

    def finish_sync_run(self, run_id: int, status: str, rows_received: int, error_message: str | None = None) -> None:
        with self.connection() as conn:
            conn.execute(
                """UPDATE sync_runs SET finished_at=%s, status=%s, rows_received=%s, error_message=%s
                WHERE id=%s""",
                (datetime.now(UTC).isoformat(), status, rows_received, error_message, run_id),
            )

    def data_health(self) -> list[dict[str, object]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT a.ticker, a.name, a.market, a.asset_class,
                    COUNT(p.price_date) AS price_rows,
                    MIN(p.price_date) AS first_price_date,
                    MAX(p.price_date) AS last_price_date,
                    MAX(p.fetched_at) AS last_fetched_at,
                    latest.status AS last_sync_status,
                    latest.finished_at AS last_sync_at,
                    latest.rows_received AS last_rows_received,
                    latest.error_message AS last_error
                FROM assets a
                LEFT JOIN daily_prices p ON p.ticker=a.ticker
                LEFT JOIN (
                    SELECT ticker, status, finished_at, rows_received, error_message
                    FROM (
                        SELECT ticker, status, finished_at, rows_received, error_message,
                            ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY started_at DESC, id DESC) AS row_number
                        FROM sync_runs
                    ) ranked
                    WHERE row_number=1
                ) latest ON latest.ticker=a.ticker
                WHERE a.active=TRUE
                GROUP BY a.ticker, a.name, a.market, a.asset_class,
                    latest.status, latest.finished_at, latest.rows_received, latest.error_message
                ORDER BY a.asset_class, a.ticker
                """
            ).fetchall()
        return list(rows)

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

    def seed_macro_series(self, series: Iterable[MacroSeriesDefinition]) -> None:
        self._backend.seed_macro_series(series)

    def list_assets(self, asset_class: str | None = None) -> list[dict[str, object]]:
        return self._backend.list_assets(asset_class)

    def list_macro_series(self) -> list[dict[str, object]]:
        return self._backend.list_macro_series()

    def upsert_prices(self, ticker: str, rows: Iterable[dict[str, object]], provider: str) -> int:
        return self._backend.upsert_prices(ticker, rows, provider)

    def upsert_macro_observations(self, code: str, rows: Iterable[dict[str, object]], provider: str) -> int:
        return self._backend.upsert_macro_observations(code, rows, provider)

    def get_prices(self, ticker: str, limit: int = 260) -> list[dict[str, object]]:
        return self._backend.get_prices(ticker, limit)

    def get_macro_observations(self, code: str, limit: int = 2000) -> list[dict[str, object]]:
        return self._backend.get_macro_observations(code, limit)

    def latest_fetch(self, ticker: str) -> datetime | None:
        return self._backend.latest_fetch(ticker)

    def latest_macro_fetch(self, code: str) -> datetime | None:
        return self._backend.latest_macro_fetch(code)

    def create_sync_run(self, ticker: str) -> int:
        return self._backend.create_sync_run(ticker)

    def finish_sync_run(self, run_id: int, status: str, rows_received: int, error_message: str | None = None) -> None:
        self._backend.finish_sync_run(run_id, status, rows_received, error_message)

    def data_health(self) -> list[dict[str, object]]:
        return self._backend.data_health()

    def ping(self) -> None:
        self._backend.ping()

