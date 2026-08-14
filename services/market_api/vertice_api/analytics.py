from __future__ import annotations

import math
from statistics import mean, stdev


def simple_return(start: float, end: float) -> float:
    if start == 0:
        return 0.0
    return (end / start - 1.0) * 100.0


def daily_returns(prices: list[float]) -> list[float]:
    return [prices[i] / prices[i - 1] - 1.0 for i in range(1, len(prices)) if prices[i - 1] != 0]


def annualized_volatility(prices: list[float]) -> float | None:
    returns = daily_returns(prices)
    if len(returns) < 2:
        return None
    return stdev(returns) * math.sqrt(252) * 100.0


def max_drawdown(prices: list[float]) -> float | None:
    if not prices:
        return None
    peak = prices[0]
    worst = 0.0
    for price in prices:
        peak = max(peak, price)
        worst = min(worst, price / peak - 1.0)
    return worst * 100.0


def beta(asset_prices: list[float], benchmark_prices: list[float]) -> float | None:
    asset_returns = daily_returns(asset_prices)
    benchmark_returns = daily_returns(benchmark_prices)
    length = min(len(asset_returns), len(benchmark_returns))
    if length < 2:
        return None
    x = asset_returns[-length:]
    y = benchmark_returns[-length:]
    benchmark_mean = mean(y)
    variance = sum((value - benchmark_mean) ** 2 for value in y) / (length - 1)
    if variance == 0:
        return None
    asset_mean = mean(x)
    covariance = sum((x[i] - asset_mean) * (y[i] - benchmark_mean) for i in range(length)) / (length - 1)
    return covariance / variance


def normalized_bars(prices: list[float], points: int = 20) -> list[int]:
    if not prices:
        return []
    step = max(1, len(prices) // points)
    sample = prices[::step][-points:]
    low, high = min(sample), max(sample)
    if high == low:
        return [50 for _ in sample]
    return [round(24 + (value - low) / (high - low) * 72) for value in sample]


def summarize(rows: list[dict[str, object]], benchmark_rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    closes = [float(row["adjusted_close"]) for row in rows]
    latest = rows[-1]
    previous = rows[-2]
    one_month_index = max(0, len(closes) - 22)
    one_year_index = max(0, len(closes) - 253)
    benchmark_prices = [float(row["adjusted_close"]) for row in benchmark_rows or []]
    return {
        "price": float(latest["close"]),
        "as_of": latest["price_date"],
        "day_change_pct": simple_return(float(previous["close"]), float(latest["close"])),
        "return_1m_pct": simple_return(closes[one_month_index], closes[-1]),
        "return_1y_pct": simple_return(closes[one_year_index], closes[-1]),
        "annualized_volatility_pct": annualized_volatility(closes),
        "max_drawdown_pct": max_drawdown(closes),
        "beta": beta(closes, benchmark_prices) if benchmark_prices else None,
        "volume": latest.get("volume"),
        "bars": normalized_bars(closes),
    }
