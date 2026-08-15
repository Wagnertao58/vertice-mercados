from __future__ import annotations

import hmac
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .catalog import CATALOG
from .config import load_settings
from .db import Database
from .providers.yahoo_chart import MarketDataError, YahooChartProvider
from .service import MarketService, UnknownAssetError

settings = load_settings()
database = Database(settings.database_url)
provider = YahooChartProvider(settings.request_timeout_seconds)
service = MarketService(database, provider, settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    database.seed_assets(CATALOG)
    yield


app = FastAPI(
    title="Vertice Market API",
    description="Daily market data, analytics and BDR parity for the Vertice dashboard.",
    version="0.5.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.dashboard_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    try:
        database.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {
        "status": "ok",
        "service": "vertice-market-api",
        "database": database.backend_name,
        "time": datetime.now(UTC).isoformat(),
    }


@app.get("/v1/assets")
def assets(asset_class: str | None = None) -> dict[str, object]:
    items = database.list_assets(asset_class)
    return {"assets": items, "count": len(items)}


@app.get("/v1/assets/{ticker}/snapshot")
def asset_snapshot(ticker: str, refresh: bool = Query(False)) -> dict[str, object]:
    try:
        return service.snapshot(ticker, force=refresh)
    except UnknownAssetError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker.upper()}")
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/v1/assets/{ticker}/history")
def asset_history(
    ticker: str,
    period: str = Query("1M", pattern="^(1D|5D|1M|6M|1A|5A)$"),
    refresh: bool = Query(False),
) -> dict[str, object]:
    try:
        return service.history(ticker, period=period, force=refresh)
    except UnknownAssetError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker.upper()}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/v1/bdr/{ticker}/parity")
def bdr_parity(ticker: str, refresh: bool = Query(False)) -> dict[str, object]:
    try:
        return service.bdr_parity(ticker, force=refresh)
    except UnknownAssetError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker.upper()}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/v1/market/overview")
def market_overview(
    tickers: str = Query(
        "TEAM,RNG,NVDA,AAPL,MSFT,AMZN,GOOGL,META,PETR4,VALE3,ITUB4,"
        "T1AM34,R2NG34,IBOV,SP500,NASDAQ,VIX,USD-BRL,EUR-BRL,EUR-USD"
    ),
) -> dict[str, object]:
    requested = [ticker.strip().upper() for ticker in tickers.split(",") if ticker.strip()]
    snapshots: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for ticker in requested[:20]:
        try:
            snapshots.append(service.snapshot(ticker))
        except (UnknownAssetError, MarketDataError) as exc:
            errors.append({"ticker": ticker, "error": str(exc)})
    return {
        "mode": "live" if snapshots else "unavailable",
        "as_of": datetime.now(UTC).isoformat(),
        "assets": snapshots,
        "errors": errors,
    }


@app.get("/v1/market/data-health")
def market_data_health() -> dict[str, object]:
    return service.data_health()


@app.post("/v1/admin/sync")
def scheduled_market_sync(
    x_sync_key: str | None = Header(None),
    tickers: str | None = Query(None),
) -> dict[str, object]:
    if not settings.sync_api_key:
        raise HTTPException(status_code=503, detail="Scheduled sync is not configured")
    if not x_sync_key or not hmac.compare_digest(x_sync_key, settings.sync_api_key):
        raise HTTPException(status_code=401, detail="Invalid sync credential")
    requested = [ticker.strip().upper() for ticker in tickers.split(",") if ticker.strip()] if tickers else None
    return service.run_scheduled_sync(requested)
