from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from vertice_api.macro_catalog import MACRO_BY_CODE
from vertice_api.providers.macro_official import OfficialMacroProvider


class _Response:
    def __init__(self, content: str):
        self._content = content.encode("utf-8")

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._content


class OfficialMacroProviderTests(unittest.TestCase):
    @patch("vertice_api.providers.macro_official.urlopen")
    def test_fred_series_are_downloaded_in_one_request(self, mocked_urlopen: object) -> None:
        csv_payload = io.StringIO()
        csv_payload.write("observation_date,FEDFUNDS,CPIAUCSL,DGS10,DTWEXBGS\n")
        csv_payload.write("2026-01-01,3.64,329.8,4.16,120.5\n")
        mocked_urlopen.return_value = _Response(csv_payload.getvalue())
        definitions = [
            MACRO_BY_CODE["US_FEDFUNDS"],
            MACRO_BY_CODE["US_CPI"],
            MACRO_BY_CODE["US_T10Y"],
            MACRO_BY_CODE["US_DOLLAR"],
        ]

        result = OfficialMacroProvider(timeout_seconds=15).fred_histories(definitions)

        self.assertEqual(mocked_urlopen.call_count, 1)
        self.assertEqual(result["US_T10Y"][0]["value"], 4.16)
        self.assertEqual(result["US_DOLLAR"][0]["observation_date"], "2026-01-01")


if __name__ == "__main__":
    unittest.main()
