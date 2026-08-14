from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vertice_api.catalog import CATALOG, CATALOG_BY_TICKER
from vertice_api.db import Database


class DatabaseTests(unittest.TestCase):
    def test_catalog_covers_phase_one_markets(self) -> None:
        self.assertEqual(len(CATALOG), len(CATALOG_BY_TICKER))
        self.assertGreaterEqual(len(CATALOG), 20)
        classes = {asset.asset_class for asset in CATALOG}
        self.assertTrue({"stock", "bdr", "index", "etf", "currency"}.issubset(classes))
        self.assertTrue({"AAPL", "MSFT", "VALE3", "IBOV", "USD-BRL"}.issubset(CATALOG_BY_TICKER))

    def test_seed_and_prices_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Database(Path(directory) / "test.db")
            db.initialize()
            db.seed_assets(CATALOG)
            self.assertGreater(len(db.list_assets()), 10)
            inserted = db.upsert_prices(
                "TEAM",
                [{"price_date": "2026-08-13", "open": 100, "high": 105, "low": 99, "close": 104, "adjusted_close": 104, "volume": 1234}],
                "test",
            )
            self.assertEqual(inserted, 1)
            self.assertEqual(db.get_prices("TEAM")[0]["close"], 104)


if __name__ == "__main__":
    unittest.main()
