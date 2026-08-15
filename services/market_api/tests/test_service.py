from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from vertice_api.catalog import CATALOG
from vertice_api.config import Settings
from vertice_api.db import Database
from vertice_api.macro_catalog import MACRO_CATALOG, MacroSeriesDefinition
from vertice_api.service import MarketService


class FakeProvider:
    name = "test_provider"

    def history(self, symbol: str, range_: str = "1y", interval: str = "1d") -> list[dict[str, object]]:
        start = date(2025, 1, 1)
        return [
            {
                "price_date": (start + timedelta(days=index)).isoformat(),
                "open": 99 + index,
                "high": 102 + index,
                "low": 98 + index,
                "close": 100 + index,
                "adjusted_close": 100 + index,
                "volume": 1000 + index,
            }
            for index in range(300)
        ]


class FakeMacroProvider:
    name = "test_macro"

    def history(self, series: MacroSeriesDefinition, years: int = 5) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for index in range(72):
            year = 2020 + index // 12
            month = index % 12 + 1
            if series.transform == "pct_change_12m":
                value = 250 + index * 0.8
            elif series.transform == "annualize_daily":
                value = 0.035 + index * 0.00001
            elif series.transform == "compound_12m":
                value = 0.25 + (index % 6) * 0.03
            else:
                value = 2.0 + index * 0.04
            rows.append({"observation_date": f"{year:04d}-{month:02d}-01", "value": value})
        return rows


class MarketServiceHistoryTests(unittest.TestCase):
    def test_history_is_persisted_and_returned_for_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "history.db")
            db.initialize()
            db.seed_assets(CATALOG)
            settings = Settings("", "http://localhost:3000", 30, 15)
            service = MarketService(db, FakeProvider(), settings)  # type: ignore[arg-type]

            result = service.history("TEAM", "1M")

            self.assertEqual(result["period"], "1M")
            self.assertEqual(result["stored_rows"], 22)
            self.assertEqual(len(result["points"]), 22)
            self.assertGreater(result["points"][-1]["return_pct"], 0)
            self.assertEqual(len(db.get_prices("TEAM")), 260)

    def test_history_rejects_unknown_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "history.db")
            db.initialize()
            db.seed_assets(CATALOG)
            settings = Settings("", "http://localhost:3000", 30, 15)
            service = MarketService(db, FakeProvider(), settings)  # type: ignore[arg-type]

            with self.assertRaises(ValueError):
                service.history("TEAM", "2A")

    def test_scheduled_sync_records_health_for_selected_assets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "scheduled.db")
            db.initialize()
            db.seed_assets(CATALOG)
            settings = Settings("", "http://localhost:3000", 30, 15, "secret")
            service = MarketService(db, FakeProvider(), settings)  # type: ignore[arg-type]

            result = service.run_scheduled_sync(["TEAM", "RNG"])
            health = service.data_health()

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["assets_succeeded"], 2)
            self.assertEqual(health["current_assets"], 2)
            self.assertGreater(health["total_price_rows"], 500)

    def test_macro_dashboard_normalizes_series_and_builds_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "macro-dashboard.db")
            db.initialize()
            db.seed_assets(CATALOG)
            db.seed_macro_series(MACRO_CATALOG)
            settings = Settings("", "http://localhost:3000", 30, 15)
            service = MarketService(db, FakeProvider(), settings, FakeMacroProvider())  # type: ignore[arg-type]
            service.run_scheduled_sync(["IBOV", "SP500", "NASDAQ", "USD-BRL"])

            result = service.macro_dashboard(24)

            self.assertEqual(result["status"], "live")
            self.assertEqual(len(result["series"]), len(MACRO_CATALOG))
            self.assertEqual(len(result["correlation"]["labels"]), 8)
            self.assertEqual(len(result["correlation"]["cells"]), 64)
            ipca = next(item for item in result["series"] if item["code"] == "BR_IPCA")
            self.assertGreater(ipca["latest_value"], 3.0)

    def test_full_sync_includes_market_and_macro(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "full-sync.db")
            db.initialize()
            db.seed_assets(CATALOG)
            db.seed_macro_series(MACRO_CATALOG)
            settings = Settings("", "http://localhost:3000", 30, 15, "secret")
            service = MarketService(db, FakeProvider(), settings, FakeMacroProvider())  # type: ignore[arg-type]

            result = service.run_full_scheduled_sync()

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["market"]["assets_succeeded"], len(CATALOG))
            self.assertEqual(result["macro"]["series_succeeded"], len(MACRO_CATALOG))


if __name__ == "__main__":
    unittest.main()
