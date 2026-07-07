"""Market-data source factory.

Turns the configured source order into concrete adapters and a failover
chain. Twelve Data is only included when its key is set; Yahoo always
qualifies (no key). Keeping this in one place means the CLI, the
ingestion scheduler, and any endpoint build sources the same way.
"""

from __future__ import annotations

from mentor.config import Settings
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.infrastructure.adapters.failover import FailoverMarketDataAdapter
from mentor.infrastructure.adapters.twelve_data import TwelveDataAdapter
from mentor.infrastructure.adapters.yahoo import YahooFinanceAdapter


def build_adapter(name: str, settings: Settings) -> MarketDataAdapter | None:
    """Construct one named adapter, or None if it can't be configured
    (e.g. a keyed source whose key is missing)."""
    if name == "yahoo":
        return YahooFinanceAdapter()
    if name == "twelve_data":
        key = settings.twelve_data_api_key.get_secret_value().strip()
        return TwelveDataAdapter(api_key=key) if key else None
    return None


def build_sources(settings: Settings) -> list[MarketDataAdapter]:
    """All configured, usable sources in priority order."""
    out: list[MarketDataAdapter] = []
    for name in settings.price_source_order:
        adapter = build_adapter(name, settings)
        if adapter is not None:
            out.append(adapter)
    if not out:  # never leave the system with zero sources
        out.append(YahooFinanceAdapter())
    return out


def build_failover(settings: Settings) -> FailoverMarketDataAdapter:
    return FailoverMarketDataAdapter(build_sources(settings))


async def close_sources(sources: list[MarketDataAdapter]) -> None:
    for source in sources:
        aclose = getattr(source, "aclose", None)
        if aclose is not None:
            await aclose()
