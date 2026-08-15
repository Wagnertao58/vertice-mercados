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
        return self.fred_histories([series], years)[series.code]

    def fred_histories(
        self,
        series_list: list[MacroSeriesDefinition],
        years: int = 5,
    ) -> dict[str, list[dict[str, object]]]:
        """Download multiple FRED series in one CSV request.

        Render's free services can time out when four independent FRED graph
        downloads are made in sequence. FRED accepts comma-separated series
        identifiers, so a single request is both faster and gentler on the
        upstream service.
        """
        if not series_list:
            return {}
        start = date.today() - timedelta(days=366 * years)
        provider_codes = ",".join(series.provider_code for series in series_list)
        query = urlencode({"id": provider_codes, "cosd": start.isoformat()})
        request = Request(
            f"{self.fred_url}?{query}",
            headers={"User-Agent": "VerticeMarketResearch/0.2"},
        )
        try:
            with urlopen(request, timeout=max(self.timeout_seconds, 60)) as response:
                content = response.read().decode("utf-8-sig")
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
            codes = ", ".join(series.code for series in series_list)
            raise MacroDataError(f"Unable to fetch {codes} from FRED: {exc}") from exc

        rows_by_code: dict[str, list[dict[str, object]]] = {
            series.code: [] for series in series_list
        }
        for item in csv.DictReader(io.StringIO(content)):
            raw_date = item.get("observation_date") or item.get("DATE")
            if not raw_date:
                continue
            for series in series_list:
                raw_value = item.get(series.provider_code)
                if not raw_value or raw_value == ".":
                    continue
                try:
                    rows_by_code[series.code].append({
                        "observation_date": date.fromisoformat(raw_date).isoformat(),
                        "value": float(raw_value),
                    })
                except ValueError:
                    continue
        missing = [code for code, rows in rows_by_code.items() if not rows]
        if missing:
            raise MacroDataError(f"No FRED observations returned for {', '.join(missing)}")
        return rows_by_code
