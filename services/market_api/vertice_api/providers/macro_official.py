from __future__ import annotations

import csv
import io
import json
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..macro_catalog import MacroSeriesDefinition


class MacroDataError(RuntimeError):
    pass


class OfficialMacroProvider:
    """Keyless feeds published by Banco Central do Brasil and FRED."""

    name = "official_macro"
    bcb_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
    fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def __init__(self, timeout_seconds: int = 15):
        self.timeout_seconds = timeout_seconds

    def history(self, series: MacroSeriesDefinition, years: int = 5) -> list[dict[str, object]]:
        if series.provider == "bcb_sgs":
            return self._bcb_history(series, years)
        if series.provider == "fred_csv":
            return self._fred_history(series, years)
        raise MacroDataError(f"Unsupported macro provider: {series.provider}")

    def _bcb_history(self, series: MacroSeriesDefinition, years: int) -> list[dict[str, object]]:
        end = date.today()
        start = end - timedelta(days=366 * years)
        query = urlencode({
            "formato": "json",
            "dataInicial": start.strftime("%d/%m/%Y"),
            "dataFinal": end.strftime("%d/%m/%Y"),
        })
        request = Request(
            f"{self.bcb_url.format(code=series.provider_code)}?{query}",
            headers={"User-Agent": "VerticeMarketResearch/0.2"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload: list[dict[str, Any]] = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MacroDataError(f"Unable to fetch {series.code} from BCB: {exc}") from exc

        rows: list[dict[str, object]] = []
        for item in payload:
            try:
                observation_date = datetime.strptime(str(item["data"]), "%d/%m/%Y").date().isoformat()
                value = float(str(item["valor"]).replace(",", "."))
            except (KeyError, TypeError, ValueError):
                continue
            rows.append({"observation_date": observation_date, "value": value})
        if not rows:
            raise MacroDataError(f"No BCB observations returned for {series.code}")
        return rows

    def _fred_history(self, series: MacroSeriesDefinition, years: int) -> list[dict[str, object]]:
        start = date.today() - timedelta(days=366 * years)
        query = urlencode({"id": series.provider_code, "cosd": start.isoformat()})
        request = Request(
            f"{self.fred_url}?{query}",
            headers={"User-Agent": "VerticeMarketResearch/0.2"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                content = response.read().decode("utf-8-sig")
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
            raise MacroDataError(f"Unable to fetch {series.code} from FRED: {exc}") from exc

        rows: list[dict[str, object]] = []
        for item in csv.DictReader(io.StringIO(content)):
            raw_value = item.get(series.provider_code)
            raw_date = item.get("observation_date") or item.get("DATE")
            if not raw_date or not raw_value or raw_value == ".":
                continue
            try:
                rows.append({"observation_date": date.fromisoformat(raw_date).isoformat(), "value": float(raw_value)})
            except ValueError:
                continue
        if not rows:
            raise MacroDataError(f"No FRED observations returned for {series.code}")
        return rows
