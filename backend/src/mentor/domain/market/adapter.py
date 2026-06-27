"""Abstract market-data adapter.

A concrete implementation per provider lives in `infrastructure/adapters`.
Domain code never imports `httpx`, API keys, or provider-specific JSON
shapes — it talks to this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from mentor.domain.market.bars import PriceBar, Timeframe


class MarketDataAdapter(ABC):
    """Read-only contract for an OHLCV provider."""

    name: str

    @abstractmethod
    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> AsyncIterator[PriceBar]:
        """Yield bars in chronological order within `[start, end)`.

        Implemented as an async generator in concrete adapters; declared
        here as a plain method returning an async iterator so the abstract
        signature has no unreachable `yield`. Implementations must align
        timestamps to the timeframe boundary, skip provider-side errors
        transparently, and apply retries before propagating exceptions.
        """
        ...
