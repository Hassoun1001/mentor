"""FRED macro ingestion — backfill the macro-driver cache.

Pulls the configured FRED series over a date range and upserts them.
Idempotent: re-running overwrites the same (series_id, day) rows, so it's
safe to schedule. Mirrors ``news.tone_ingest``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from mentor.domain.forecasting.macro_features import FRED_SERIES_IDS
from mentor.infrastructure.adapters.macro.fred import FredAdapter
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.logging import get_logger

log = get_logger("mentor.macro.ingest")


@dataclass(frozen=True, slots=True)
class MacroIngestResult:
    series_ids: tuple[str, ...]
    observations_fetched: int
    rows_written: int
    counts_by_series: dict[str, int] = field(default_factory=dict)


class MacroIngestService:
    def __init__(
        self,
        *,
        repo: MacroSeriesRepository,
        series_ids: tuple[str, ...] = FRED_SERIES_IDS,
    ) -> None:
        self._repo = repo
        self._series_ids = series_ids

    async def backfill(self, *, start: datetime, end: datetime) -> MacroIngestResult:
        async with FredAdapter(series_ids=self._series_ids) as adapter:
            observations = await adapter.fetch_all(start=start, end=end)
        written = await self._repo.upsert(observations)
        counts = await self._repo.counts_by_series()
        log.info(
            "macro_ingest.done",
            series=len(self._series_ids),
            fetched=len(observations),
            written=written,
        )
        return MacroIngestResult(
            series_ids=self._series_ids,
            observations_fetched=len(observations),
            rows_written=written,
            counts_by_series=counts,
        )
