from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .analytics import summarize
from .catalog import CATALOG_BY_TICKER, AssetDefinition
from .config import Settings
from .db import Database
from .providers.yahoo_chart import YahooChartProvider


class UnknownAssetError(KeyError):
    pass


HISTORY_PERIODS: dict[str, tuple[int, str]] = {
    "1D": (2, "1y"),
    "5D": (5, "1y"),
    "1M": (22, "1y"),
    "6M": (126, "1y"),
    "1A": (253, "1y"),
    "5A": (1260, "5y"),
}


def _sample_rows(rows: list[dict[str, object]], max_points: int = 90) -> list[dict[str, object]]:
    if len(rows) <= max_points:
        return rows
    step = (len(rows) - 1) / (max_points - 1)
    indexes = [round(index * step) for index in range(max_points)]
    return [rows[index] for index in indexes]


class MarketService:
    def __init__(self, db: Database, provider: YahooChartProvider, settings: Settings):
        self.db = db
        self.provider = provider
        self.settings = settings

    def asset(self, ticker: str) -> AssetDefinition:
        normalized = ticker.upper()
        try:
            return CATALOG_BY_TICKER[normalized]
        except KeyError as exc:
            raise UnknownAssetError(normalized) from exc

    def sync(self, ticker: str, force: bool = False) -> list[dict[str, object]]:
        asset = self.asset(ticker)
        latest_fetch = self.db.latest_fetch(asset.ticker)
        fresh_after = datetime.now(UTC) - timedelta(minutes=self.settings.cache_minutes)
        if not force and latest_fetch and latest_fetch >= fresh_after:
            cached = self.db.get_prices(asset.ticker)
            if cached:
                return cached
        rows = self.provider.history(asset.provider_symbol)
        self.db.upsert_prices(asset.ticker, rows, self.provider.name)
        return self.db.get_prices(asset.ticker)

    def snapshot(self, ticker: str, force: bool = False) -> dict[str, object]:
        asset = self.asset(ticker)
        rows = self.sync(asset.ticker, force=force)
        benchmark_rows = self.sync(asset.benchmark) if asset.benchmark else None
        return {**asset.as_record(), **summarize(rows, benchmark_rows), "provider": self.provider.name}

    def history(self, ticker: str, period: str = "1M", force: bool = False) -> dict[str, object]:
        asset = self.asset(ticker)
        normalized_period = period.upper()
        if normalized_period not in HISTORY_PERIODS:
            raise ValueError(f"Unsupported period: {period}")

        row_limit, provider_range = HISTORY_PERIODS[normalized_period]
        stored = self.db.get_prices(asset.ticker, limit=row_limit)
        latest_fetch = self.db.latest_fetch(asset.ticker)
        fresh_after = datetime.now(UTC) - timedelta(minutes=self.settings.cache_minutes)
        needs_extended_history = normalized_period == "5A" and len(stored) < 700
        if force or len(stored) < min(row_limit, 2) or needs_extended_history or not latest_fetch or latest_fetch < fresh_after:
            rows = self.provider.history(asset.provider_symbol, range_=provider_range)
            self.db.upsert_prices(asset.ticker, rows, self.provider.name)
            stored = self.db.get_prices(asset.ticker, limit=row_limit)

        sampled = _sample_rows(stored)
        if not sampled:
            raise ValueError(f"No history available for {asset.ticker}")
        start = float(sampled[0]["adjusted_close"])
        points = [
            {
                "date": row["price_date"],
                "close": float(row["close"]),
                "adjusted_close": float(row["adjusted_close"]),
                "return_pct": (float(row["adjusted_close"]) / start - 1.0) * 100.0 if start else 0.0,
                "volume": row.get("volume"),
            }
            for row in sampled
        ]
        return {
            "ticker": asset.ticker,
            "name": asset.name,
            "market": asset.market,
            "currency": asset.currency,
            "period": normalized_period,
            "as_of": points[-1]["date"],
            "provider": self.provider.name,
            "stored_rows": len(stored),
            "points": points,
        }

    def run_scheduled_sync(self, tickers: list[str] | None = None) -> dict[str, object]:
        requested = {ticker.upper() for ticker in tickers or []}
        assets = [
            asset for asset in self.db.list_assets()
            if not requested or str(asset["ticker"]).upper() in requested
        ]
        started_at = datetime.now(UTC)
        results: list[dict[str, object]] = []
        for asset in assets:
            ticker = str(asset["ticker"])
            run_id = self.db.create_sync_run(ticker)
            try:
                rows = self.provider.history(str(asset["provider_symbol"]))
                rows_received = self.db.upsert_prices(ticker, rows, self.provider.name)
                self.db.finish_sync_run(run_id, "success", rows_received)
                results.append({"ticker": ticker, "status": "success", "rows_received": rows_received})
            except Exception as exc:
                message = str(exc)[:500]
                self.db.finish_sync_run(run_id, "failed", 0, message)
                results.append({"ticker": ticker, "status": "failed", "rows_received": 0, "error": message})

        succeeded = sum(item["status"] == "success" for item in results)
        failed = len(results) - succeeded
        return {
            "status": "ok" if failed == 0 else "partial" if succeeded else "failed",
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(UTC).isoformat(),
            "assets_requested": len(assets),
            "assets_succeeded": succeeded,
            "assets_failed": failed,
            "results": results,
        }

    def data_health(self) -> dict[str, object]:
        now = datetime.now(UTC)
        stale_before = now - timedelta(hours=72)
        items: list[dict[str, object]] = []
        for row in self.db.data_health():
            fetched_at_value = row.get("last_fetched_at")
            fetched_at = datetime.fromisoformat(str(fetched_at_value)) if fetched_at_value else None
            if int(row.get("price_rows") or 0) == 0:
                status = "missing"
            elif row.get("last_sync_status") == "failed":
                status = "error"
            elif not fetched_at or fetched_at < stale_before:
                status = "stale"
            else:
                status = "current"
            items.append({**row, "status": status})

        counts = {status: sum(item["status"] == status for item in items) for status in ("current", "stale", "error", "missing")}
        latest_updates = [str(item["last_fetched_at"]) for item in items if item.get("last_fetched_at")]
        total = len(items)
        return {
            "status": "healthy" if total and counts["current"] == total else "attention" if total else "empty",
            "checked_at": now.isoformat(),
            "total_assets": total,
            "current_assets": counts["current"],
            "stale_assets": counts["stale"],
            "error_assets": counts["error"],
            "missing_assets": counts["missing"],
            "coverage_pct": round((total - counts["missing"]) / total * 100, 1) if total else 0.0,
            "total_price_rows": sum(int(item.get("price_rows") or 0) for item in items),
            "last_update_at": max(latest_updates) if latest_updates else None,
            "items": items,
        }

    def bdr_parity(self, ticker: str, force: bool = False) -> dict[str, object]:
        bdr = self.asset(ticker)
        if bdr.asset_class != "bdr" or not bdr.underlying or not bdr.bdr_ratio:
            raise ValueError(f"{ticker} is not a configured BDR")
        bdr_snapshot = self.snapshot(bdr.ticker, force=force)
        underlying = self.snapshot(bdr.underlying, force=force)
        fx = self.snapshot("USD-BRL", force=force)
        theoretical = float(underlying["price"]) * float(fx["price"]) / bdr.bdr_ratio
        observed = float(bdr_snapshot["price"])
        premium = (observed / theoretical - 1.0) * 100.0 if theoretical else None
        return {
            "ticker": bdr.ticker,
            "underlying": bdr.underlying,
            "ratio": bdr.bdr_ratio,
            "underlying_price_usd": underlying["price"],
            "usd_brl": fx["price"],
            "theoretical_price_brl": theoretical,
            "observed_price_brl": observed,
            "premium_discount_pct": premium,
            "as_of": min(str(bdr_snapshot["as_of"]), str(underlying["as_of"]), str(fx["as_of"])),
        }
