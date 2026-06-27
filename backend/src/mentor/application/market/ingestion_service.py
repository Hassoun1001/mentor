"""Ingestion service — pull bars from an adapter and persist them.

Idempotent by construction: the repository uses `INSERT … ON CONFLICT DO
NOTHING`, so the same window can be requested again with no effect.
That makes resumes after failure trivial — just re-run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.ingestion")


@dataclass(frozen=True, slots=True)
class IngestionResult:
    symbol: str
    timeframe: Timeframe
    requested_start: datetime
    requested_end: datetime
    fetched: int
    persisted: int


class IngestionService:
    def __init__(self, *, adapter: MarketDataAdapter, repo: PriceBarRepository) -> None:
        self._adapter = adapter
        self._repo = repo

    async def ingest(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        batch_size: int = 500,
    ) -> IngestionResult:
        buffer = []
        fetched = 0
        persisted = 0

        async for bar in self._adapter.fetch_bars(
            symbol=symbol, timeframe=timeframe, start=start, end=end
        ):
            buffer.append(bar)
            fetched += 1
            if len(buffer) >= batch_size:
                persisted += await self._repo.upsert_many(buffer)
                buffer.clear()

        if buffer:
            persisted += await self._repo.upsert_many(buffer)

        log.info(
            "ingestion.completed",
            symbol=symbol,
            timeframe=timeframe.value,
            fetched=fetched,
            persisted=persisted,
            source=self._adapter.name,
        )

        return IngestionResult(
            symbol=symbol,
            timeframe=timeframe,
            requested_start=start,
            requested_end=end,
            fetched=fetched,
            persisted=persisted,
        )
