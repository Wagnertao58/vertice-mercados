from __future__ import annotations

import io
import json
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
    def test_new_york_fed_effr_response(self, mocked_urlopen: object) -> None:
        mocked_urlopen.return_value = _Response(json.dumps({
            "refRates": [{"effectiveDate": "2026-01-02", "percentRate": 3.64}],
        }))

        result = OfficialMacroProvider().history(MACRO_BY_CODE["US_FEDFUNDS"])

        self.assertEqual(result, [{"observation_date": "2026-01-02", "value": 3.64}])

    @patch("vertice_api.providers.macro_official.urlopen")
    def test_bls_cpi_response(self, mocked_urlopen: object) -> None:
        mocked_urlopen.return_value = _Response(json.dumps({
            "Results": {"series": [{"data": [
                {"year": "2026", "period": "M02", "value": "330.1"},
                {"year": "2026", "period": "M01", "value": "329.8"},
            ]}]},
        }))

        result = OfficialMacroProvider().history(MACRO_BY_CODE["US_CPI"])

        self.assertEqual(result[0], {"observation_date": "2026-01-01", "value": 329.8})

    @patch("vertice_api.providers.macro_official.urlopen")
    def test_treasury_ten_year_xml_response(self, mocked_urlopen: object) -> None:
        mocked_urlopen.return_value = _Response("""<?xml version="1.0"?>
        <feed xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
              xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices">
          <entry><content><m:properties>
            <d:NEW_DATE>2026-01-02T00:00:00</d:NEW_DATE>
            <d:BC_10YEAR>4.16</d:BC_10YEAR>
          </m:properties></content></entry>
        </feed>""")

        result = OfficialMacroProvider().history(MACRO_BY_CODE["US_T10Y"])

        self.assertEqual(result[0], {"observation_date": "2026-01-02", "value": 4.16})

    @patch("vertice_api.providers.macro_official.urlopen")
    def test_federal_reserve_broad_dollar_csv_response(self, mocked_urlopen: object) -> None:
        csv_payload = io.StringIO()
        csv_payload.write("Series Description,Nominal Broad Dollar Index\n")
        csv_payload.write("Time Period,JRXWTFB_N.B\n")
        csv_payload.write("2026-01-02,120.5\n")
        mocked_urlopen.return_value = _Response(csv_payload.getvalue())

        result = OfficialMacroProvider().history(MACRO_BY_CODE["US_DOLLAR"])

        self.assertEqual(result, [{"observation_date": "2026-01-02", "value": 120.5}])


if __name__ == "__main__":
    unittest.main()
