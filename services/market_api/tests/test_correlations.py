from __future__ import annotations

import unittest

from vertice_api.correlations import changes, correlation_matrix, month_end_values, pearson


class CorrelationTests(unittest.TestCase):
    def test_month_end_values_keep_last_observation(self) -> None:
        rows = [
            {"price_date": "2026-01-03", "adjusted_close": 100},
            {"price_date": "2026-01-31", "adjusted_close": 110},
            {"price_date": "2026-02-28", "adjusted_close": 121},
        ]
        monthly = month_end_values(rows, "adjusted_close")
        self.assertEqual(monthly, {"2026-01": 110.0, "2026-02": 121.0})
        self.assertAlmostEqual(changes(monthly, percent=True)["2026-02"], 10.0)

    def test_pearson_and_matrix(self) -> None:
        left = {f"2026-{month:02d}": float(month) for month in range(1, 9)}
        right = {f"2026-{month:02d}": float(month * 2) for month in range(1, 9)}
        value, observations = pearson(left, right)
        matrix = correlation_matrix({"A": left, "B": right})

        self.assertEqual(value, 1.0)
        self.assertEqual(observations, 8)
        self.assertEqual(len(matrix["cells"]), 4)


if __name__ == "__main__":
    unittest.main()
