from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from vertice_api.catalog import CATALOG
from vertice_api.config import Settings
from vertice_api.db import Database
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


if __name__ == "__main__":
    unittest.main()
