from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MacroSeriesDefinition:
    code: str
    provider: str
    provider_code: str
    name: str
    country: str
    category: str
    unit: str
    frequency: str
    transform: str = "identity"

    def as_record(self) -> dict[str, object]:
        return asdict(self)


MACRO_CATALOG: tuple[MacroSeriesDefinition, ...] = (
    MacroSeriesDefinition("BR_SELIC", "bcb_sgs", "1178", "Selic efetiva", "BR", "interest", "% a.a.", "daily"),
    MacroSeriesDefinition("BR_CDI", "bcb_sgs", "12", "CDI", "BR", "interest", "% a.a.", "daily", "annualize_daily"),
    MacroSeriesDefinition("BR_IPCA", "bcb_sgs", "433", "IPCA em 12 meses", "BR", "inflation", "% a.a.", "monthly", "compound_12m"),
    MacroSeriesDefinition("BR_IGPM", "bcb_sgs", "189", "IGP-M em 12 meses", "BR", "inflation", "% a.a.", "monthly", "compound_12m"),
    MacroSeriesDefinition("US_FEDFUNDS", "fred_csv", "FEDFUNDS", "Fed Funds efetiva", "US", "interest", "% a.a.", "monthly"),
    MacroSeriesDefinition("US_CPI", "fred_csv", "CPIAUCSL", "CPI em 12 meses", "US", "inflation", "% a.a.", "monthly", "pct_change_12m"),
    MacroSeriesDefinition("US_T10Y", "fred_csv", "DGS10", "Treasury 10 anos", "US", "interest", "% a.a.", "daily"),
    MacroSeriesDefinition("US_DOLLAR", "fred_csv", "DTWEXBGS", "Dolar amplo", "US", "currency", "indice", "daily"),
)

MACRO_BY_CODE = {series.code: series for series in MACRO_CATALOG}
