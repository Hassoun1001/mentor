"""Ingestion service — pull bars from an adapter and persist them.

Idempotent by construction: new bars are inserted with `INSERT … ON
CONFLICT DO NOTHING`, so the same window can be requested again with no
effect. That makes resumes after failure trivial — just re-run.

Only settled bars are stored. Every feed hands back the bar still forming;
storing it meant keeping a few minutes of an hour as if they were the hour
(see ``domain/market/settlement.py`` for what that did in production). A
row that was nevertheless stored early — every one written before this
rule existed — is *provisional*, and the first fetch that returns its
settled version replaces it, logging the old values so the change can be
reverted.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.settlement import (
    BarCorrection,
    StoredBar,
    plan_corrections,
    screen,
)
from mentor.logging import get_logger

log = get_logger("mentor.ingestion")

CORRECTION_REASON = "stored before its period closed; replaced by the settled bar"


class BarStore(Protocol):
    """What ingestion needs from storage (``PriceBarRepository`` satisfies it)."""

    async def upsert_many(self, bars: Sequence[PriceBar]) -> int: ...

    async def provisional(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[StoredBar]: ...

    async def apply_corrections(
        self,
        corrections: Sequence[BarCorrection],
        *,
        batch_id: str,
        reason: str,
        now: datetime,
    ) -> int: ...


@dataclass(frozen=True, slots=True)
class IngestionResult:
    symbol: str
    timeframe: Timeframe
    requested_start: datetime
    requested_end: datetime
    fetched: int
    persisted: int  # new rows
    corrected: int = 0  # provisional rows replaced by their settled bar
    skipped_forming: int = 0  # period not over yet — fetched again next time
    skipped_misaligned: int = 0  # not on a bar boundary (a feed's live tick)


def correction_batch_id(timeframe: Timeframe, now: datetime) -> str:
    """One revision batch per ingest run, so a single run can be reverted."""
    return f"ingest:{timeframe.value}:{now.astimezone(UTC):%Y%m%dT%H%M%SZ}"


class IngestionService:
    def __init__(self, *, adapter: MarketDataAdapter, repo: BarStore) -> None:
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
        now: datetime | None = None,
    ) -> IngestionResult:
        now = now or datetime.now(UTC)
        fetched = [
            bar
            async for bar in self._adapter.fetch_bars(
                symbol=symbol, timeframe=timeframe, start=start, end=end
            )
        ]
        screened = screen(fetched, now=now)
        settled = screened.settled

        persisted = 0
        for i in range(0, len(settled), batch_size):
            persisted += await self._repo.upsert_many(settled[i : i + batch_size])

        corrected = 0
        if settled:
            stale = await self._repo.provisional(
                symbol=symbol,
                timeframe=timeframe,
                start=min(b.ts for b in settled),
                end=max(b.ts for b in settled) + timedelta(seconds=timeframe.seconds),
            )
            corrections = plan_corrections(stale, settled, timeframe)
            if corrections:
                corrected = await self._repo.apply_corrections(
                    corrections,
                    batch_id=correction_batch_id(timeframe, now),
                    reason=CORRECTION_REASON,
                    now=now,
                )

        log.info(
            "ingestion.completed",
            symbol=symbol,
            timeframe=timeframe.value,
            fetched=len(fetched),
            persisted=persisted,
            corrected=corrected,
            skipped_forming=screened.forming,
            skipped_misaligned=screened.misaligned,
            source=self._adapter.name,
        )

        return IngestionResult(
            symbol=symbol,
            timeframe=timeframe,
            requested_start=start,
            requested_end=end,
            fetched=len(fetched),
            persisted=persisted,
            corrected=corrected,
            skipped_forming=screened.forming,
            skipped_misaligned=screened.misaligned,
        )
