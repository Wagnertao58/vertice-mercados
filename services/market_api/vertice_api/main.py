from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .catalog import CATALOG
from .config import load_settings
from .db import Database
from .providers.yahoo_chart import MarketDataError, YahooChartProvider
from .service import MarketService, UnknownAssetError

settings = load_settings()
database = Database(settings.database_path)
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
    version="0.1.0",
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
    return {"status": "ok", "service": "vertice-market-api", "time": datetime.now(UTC).isoformat()}


@app.get("/v1/assets")
def assets(asset_class: str | None = None) -> dict[str, object]:
    return {"assets": database.list_assets(asset_class), "count": len(database.list_assets(asset_class))}


@app.get("/v1/assets/{ticker}/snapshot")
def asset_snapshot(ticker: str, refresh: bool = Query(False)) -> dict[str, object]:
    try:
        return service.snapshot(ticker, force=refresh)
    except UnknownAssetError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker.upper()}")
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
    tickers: str = Query("TEAM,RNG,T1AM34,R2NG34,NVDA,PETR4,IBOV,SP500,NASDAQ,USD-BRL,VIX"),
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
