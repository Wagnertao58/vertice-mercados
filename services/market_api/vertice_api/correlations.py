from __future__ import annotations

from math import sqrt


def month_end_values(rows: list[dict[str, object]], value_key: str) -> dict[str, float]:
    monthly: dict[str, tuple[str, float]] = {}
    for row in rows:
        observation_date = str(row.get("observation_date") or row.get("price_date") or "")
        if len(observation_date) < 7 or row.get(value_key) is None:
            continue
        month = observation_date[:7]
        value = float(row[value_key])
        current = monthly.get(month)
        if current is None or observation_date > current[0]:
            monthly[month] = (observation_date, value)
    return {month: item[1] for month, item in sorted(monthly.items())}


def changes(values: dict[str, float], percent: bool) -> dict[str, float]:
    result: dict[str, float] = {}
    previous: float | None = None
    for month, value in sorted(values.items()):
        if previous is not None:
            result[month] = (value / previous - 1.0) * 100.0 if percent and previous else value - previous
        previous = value
    return result


def pearson(left: dict[str, float], right: dict[str, float], minimum_points: int = 6) -> tuple[float | None, int]:
    months = sorted(set(left) & set(right))
    if len(months) < minimum_points:
        return None, len(months)
    x = [left[month] for month in months]
    y = [right[month] for month in months]
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    covariance = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    variance_x = sum((a - mean_x) ** 2 for a in x)
    variance_y = sum((b - mean_y) ** 2 for b in y)
    denominator = sqrt(variance_x * variance_y)
    if denominator == 0:
        return None, len(months)
    return round(max(-1.0, min(1.0, covariance / denominator)), 3), len(months)


def correlation_matrix(series: dict[str, dict[str, float]]) -> dict[str, object]:
    labels = list(series)
    cells: list[dict[str, object]] = []
    for row in labels:
        for column in labels:
            if row == column:
                value, observations = 1.0, len(series[row])
            else:
                value, observations = pearson(series[row], series[column])
            cells.append({"row": row, "column": column, "value": value, "observations": observations})
    return {"labels": labels, "cells": cells}
