from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AssetDefinition:
    ticker: str
    provider_symbol: str
    name: str
    asset_class: str
    market: str
    currency: str
    benchmark: str | None = None
    underlying: str | None = None
    bdr_ratio: float | None = None

    def as_record(self) -> dict[str, object]:
        return asdict(self)


CATALOG: tuple[AssetDefinition, ...] = (
    AssetDefinition("TEAM", "TEAM", "Atlassian", "stock", "NASDAQ", "USD", "SPY"),
    AssetDefinition("RNG", "RNG", "RingCentral", "stock", "NYSE", "USD", "SPY"),
    AssetDefinition("NVDA", "NVDA", "NVIDIA", "stock", "NASDAQ", "USD", "SPY"),
    AssetDefinition("AAPL", "AAPL", "Apple", "stock", "NASDAQ", "USD", "SPY"),
    AssetDefinition("MSFT", "MSFT", "Microsoft", "stock", "NASDAQ", "USD", "SPY"),
    AssetDefinition("AMZN", "AMZN", "Amazon", "stock", "NASDAQ", "USD", "SPY"),
    AssetDefinition("GOOGL", "GOOGL", "Alphabet", "stock", "NASDAQ", "USD", "SPY"),
    AssetDefinition("META", "META", "Meta Platforms", "stock", "NASDAQ", "USD", "SPY"),
    AssetDefinition("PETR4", "PETR4.SA", "Petrobras PN", "stock", "B3", "BRL", "IBOV"),
    AssetDefinition("VALE3", "VALE3.SA", "Vale ON", "stock", "B3", "BRL", "IBOV"),
    AssetDefinition("ITUB4", "ITUB4.SA", "Itau Unibanco PN", "stock", "B3", "BRL", "IBOV"),
    AssetDefinition("T1AM34", "T1AM34.SA", "Atlassian BDR", "bdr", "B3", "BRL", "IBOV", "TEAM", 20),
    AssetDefinition("R2NG34", "R2NG34.SA", "RingCentral BDR", "bdr", "B3", "BRL", "IBOV", "RNG", 25),
    AssetDefinition("IBOV", "^BVSP", "Ibovespa", "index", "B3", "BRL"),
    AssetDefinition("SP500", "^GSPC", "S&P 500", "index", "NYSE", "USD"),
    AssetDefinition("NASDAQ", "^IXIC", "Nasdaq Composite", "index", "NASDAQ", "USD"),
    AssetDefinition("VIX", "^VIX", "CBOE Volatility Index", "index", "CBOE", "USD"),
    AssetDefinition("SPY", "SPY", "SPDR S&P 500 ETF", "etf", "NYSE", "USD"),
    AssetDefinition("QQQ", "QQQ", "Invesco QQQ", "etf", "NASDAQ", "USD"),
    AssetDefinition("USD-BRL", "BRL=X", "Dolar / Real", "currency", "FX", "BRL"),
    AssetDefinition("EUR-BRL", "EURBRL=X", "Euro / Real", "currency", "FX", "BRL"),
    AssetDefinition("EUR-USD", "EURUSD=X", "Euro / Dolar", "currency", "FX", "USD"),
)

CATALOG_BY_TICKER = {asset.ticker: asset for asset in CATALOG}
