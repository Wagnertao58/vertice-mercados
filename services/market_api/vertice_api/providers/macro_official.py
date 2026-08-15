from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..macro_catalog import MacroSeriesDefinition


class MacroDataError(RuntimeError):
    pass


class OfficialMacroProvider:
    """Keyless feeds published by Brazilian and U.S. public institutions."""

    name = "official_macro"
    bcb_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
    nyfed_url = "https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json"
    bls_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    treasury_url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
    fed_ddp_url = "https://www.federalreserve.gov/datadownload/Output.aspx"
    fed_ddp_package = "122e3bcb627e8e53f1bf72a1a09cfb81"

    def __init__(self, timeout_seconds: int = 15):
        self.timeout_seconds = timeout_seconds

    def history(self, series: MacroSeriesDefinition, years: int = 5) -> list[dict[str, object]]:
        if series.provider == "bcb_sgs":
            return self._bcb_history(series, years)
        if series.provider == "nyfed_effr":
            return self._nyfed_history(series, years)
        if series.provider == "bls_public_api":
            return self._bls_history(series, years)
        if series.provider == "treasury_xml":
            return self._treasury_history(series, years)
        if series.provider == "fed_ddp":
            return self._fed_ddp_history(series, years)
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

    def _nyfed_history(self, series: MacroSeriesDefinition, years: int) -> list[dict[str, object]]:
        end = date.today()
        start = date.today() - timedelta(days=366 * years)
        query = urlencode({
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "type": "rate",
            "limit": 2000,
        })
        request = Request(
            f"{self.nyfed_url}?{query}",
            headers={"User-Agent": "VerticeMarketResearch/0.2"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload: dict[str, Any] = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MacroDataError(f"Unable to fetch {series.code} from New York Fed: {exc}") from exc

        rows: list[dict[str, object]] = []
        for item in payload.get("refRates", []):
            raw_date = item.get("effectiveDate")
            raw_value = item.get("percentRate")
            if raw_date is None or raw_value is None:
                continue
            try:
                rows.append({"observation_date": date.fromisoformat(str(raw_date)).isoformat(), "value": float(raw_value)})
            except ValueError:
                continue
        return self._require_rows(series, rows, "New York Fed")

    def _bls_history(self, series: MacroSeriesDefinition, years: int) -> list[dict[str, object]]:
        end_year = date.today().year
        body = json.dumps({
            "seriesid": [series.provider_code],
            "startyear": str(end_year - years),
            "endyear": str(end_year),
        }).encode("utf-8")
        request = Request(
            self.bls_url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": "VerticeMarketResearch/0.2"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload: dict[str, Any] = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MacroDataError(f"Unable to fetch {series.code} from BLS: {exc}") from exc

        rows: list[dict[str, object]] = []
        result_series = payload.get("Results", {}).get("series", [])
        for item in result_series[0].get("data", []) if result_series else []:
            period = str(item.get("period", ""))
            if not period.startswith("M") or period == "M13":
                continue
            try:
                rows.append({
                    "observation_date": date(int(item["year"]), int(period[1:]), 1).isoformat(),
                    "value": float(item["value"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
        rows.sort(key=lambda row: str(row["observation_date"]))
        return self._require_rows(series, rows, "BLS")

    def _treasury_history(self, series: MacroSeriesDefinition, years: int) -> list[dict[str, object]]:
        current_year = date.today().year
        rows: list[dict[str, object]] = []
        for year in range(current_year - years, current_year + 1):
            query = urlencode({"data": "daily_treasury_yield_curve", "field_tdr_date_value": year})
            request = Request(
                f"{self.treasury_url}?{query}",
                headers={"User-Agent": "VerticeMarketResearch/0.2"},
            )
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    root = ET.fromstring(response.read())
            except (HTTPError, URLError, TimeoutError, ET.ParseError) as exc:
                raise MacroDataError(f"Unable to fetch {series.code} from U.S. Treasury: {exc}") from exc

            for properties in (element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "properties"):
                values = {child.tag.rsplit("}", 1)[-1]: child.text for child in properties}
                raw_date = values.get("NEW_DATE")
                raw_value = values.get(series.provider_code)
                if not raw_date or not raw_value:
                    continue
                try:
                    rows.append({"observation_date": raw_date[:10], "value": float(raw_value)})
                except ValueError:
                    continue
        rows.sort(key=lambda row: str(row["observation_date"]))
        return self._require_rows(series, rows, "U.S. Treasury")

    def _fed_ddp_history(self, series: MacroSeriesDefinition, years: int) -> list[dict[str, object]]:
        end = date.today()
        start = end - timedelta(days=366 * years)
        query = urlencode({
            "rel": "H10",
            "series": self.fed_ddp_package,
            "lastobs": "",
            "from": start.strftime("%m/%d/%Y"),
            "to": end.strftime("%m/%d/%Y"),
            "filetype": "csv",
            "label": "include",
            "layout": "seriescolumn",
        })
        request = Request(
            f"{self.fed_ddp_url}?{query}",
            headers={"User-Agent": "VerticeMarketResearch/0.2"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                content = response.read().decode("utf-8-sig")
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
            raise MacroDataError(f"Unable to fetch {series.code} from Federal Reserve Board: {exc}") from exc

        rows: list[dict[str, object]] = []
        value_index: int | None = None
        for columns in csv.reader(io.StringIO(content)):
            if value_index is None and series.provider_code in columns:
                value_index = columns.index(series.provider_code)
                continue
            if value_index is None or len(columns) <= value_index:
                continue
            raw_date, raw_value = columns[0].strip(), columns[value_index].strip()
            if not raw_value or raw_value.upper() in {"ND", "NA"}:
                continue
            try:
                parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(raw_date, "%m/%d/%Y").date()
                except ValueError:
                    continue
            try:
                rows.append({"observation_date": parsed_date.isoformat(), "value": float(raw_value)})
            except ValueError:
                continue
        return self._require_rows(series, rows, "Federal Reserve Board")

    @staticmethod
    def _require_rows(
        series: MacroSeriesDefinition,
        rows: list[dict[str, object]],
        source: str,
    ) -> list[dict[str, object]]:
        if not rows:
            raise MacroDataError(f"No observations returned for {series.code} from {source}")
        return rows
