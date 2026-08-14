from __future__ import annotations

import unittest

from vertice_api.analytics import annualized_volatility, beta, max_drawdown, normalized_bars, simple_return


class AnalyticsTests(unittest.TestCase):
    def test_simple_return(self) -> None:
        self.assertAlmostEqual(simple_return(100, 112), 12.0)

    def test_max_drawdown(self) -> None:
        self.assertAlmostEqual(max_drawdown([100, 120, 90, 105]), -25.0)

    def test_flat_series_has_zero_volatility(self) -> None:
        self.assertAlmostEqual(annualized_volatility([10, 10, 10, 10]) or 0, 0.0)

    def test_beta_tracks_scaled_benchmark(self) -> None:
        benchmark = [100, 102, 101, 104, 103, 106]
        asset = [100, 104, 102, 108, 106, 112]
        result = beta(asset, benchmark)
        self.assertIsNotNone(result)
        self.assertGreater(result or 0, 1.5)

    def test_normalized_bars_are_bounded(self) -> None:
        bars = normalized_bars([1, 2, 3, 4, 5])
        self.assertEqual(len(bars), 5)
        self.assertGreaterEqual(min(bars), 24)
        self.assertLessEqual(max(bars), 96)


if __name__ == "__main__":
    unittest.main()
