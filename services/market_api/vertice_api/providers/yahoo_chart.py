from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class MarketDataError(RuntimeError):
    pass


class YahooChartProvider:
    """Keyless development feed. Replace with a licensed feed for production."""

    name = "yahoo_chart_unofficial"
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def __init__(self, timeout_seconds: int = 15):
        self.timeout_seconds = timeout_seconds

    def history(self, symbol: str, range_: str = "1y", interval: str = "1d") -> list[dict[str, object]]:
        url = f"{self.base_url}/{quote(symbol, safe='')}?range={range_}&interval={interval}&events=div%2Csplits"
        request = Request(url, headers={"User-Agent": "VerticeMarketResearch/0.1"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload: dict[str, Any] = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MarketDataError(f"Unable to fetch {symbol}: {exc}") from exc

        chart = payload.get("chart", {})
        if chart.get("error"):
            raise MarketDataError(f"Provider error for {symbol}: {chart['error']}")
        results = chart.get("result") or []
        if not results:
            raise MarketDataError(f"No market data returned for {symbol}")

        result = results[0]
        timestamps = result.get("timestamp") or []
        indicators = result.get("indicators") or {}
        quotes = (indicators.get("quote") or [{}])[0]
        adjusted = (indicators.get("adjclose") or [{}])[0].get("adjclose") or []
        rows: list[dict[str, object]] = []
        for index, timestamp in enumerate(timestamps):
            close = self._value(quotes.get("close"), index)
            if close is None:
                continue
            adjusted_close = self._value(adjusted, index) or close
            rows.append(
                {
                    "price_date": datetime.fromtimestamp(timestamp, UTC).date().isoformat(),
                    "open": self._value(quotes.get("open"), index),
                    "high": self._value(quotes.get("high"), index),
                    "low": self._value(quotes.get("low"), index),
                    "close": close,
                    "adjusted_close": adjusted_close,
                    "volume": self._value(quotes.get("volume"), index),
                }
            )
        if len(rows) < 2:
            raise MarketDataError(f"Insufficient market history for {symbol}")
        return rows

    @staticmethod
    def _value(values: list[object] | None, index: int) -> float | None:
        if not values or index >= len(values) or values[index] is None:
            return None
        return float(values[index])
