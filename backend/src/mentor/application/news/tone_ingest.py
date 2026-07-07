"""GDELT tone ingestion — backfill the daily news-sentiment cache.

Pulls the Average-Tone and Volume-Intensity timelines for the configured
macro query over a date range and upserts them. Idempotent: re-running
overwrites the same (query_key, day) rows, so it's safe to schedule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mentor.infrastructure.adapters.news.gdelt import GdeltNewsAdapter
from mentor.infrastructure.repositories.news_tone import NewsToneRepository
from mentor.logging import get_logger

log = get_logger("mentor.news.tone_ingest")


@dataclass(frozen=True, slots=True)
class ToneIngestResult:
    query_key: str
    days_fetched: int
    rows_written: int
    first_day: str | None
    last_day: str | None


class ToneIngestService:
    def __init__(
        self,
        *,
        repo: NewsToneRepository,
        query: str,
        query_key: str,
    ) -> None:
        self._repo = repo
        self._query = query
        self._query_key = query_key

    async def backfill(self, *, start: datetime, end: datetime) -> ToneIngestResult:
        async with GdeltNewsAdapter(query=self._query) as adapter:
            points = await adapter.fetch_range(start=start, end=end)
        written = await self._repo.upsert(query_key=self._query_key, points=points)
        log.info(
            "tone_ingest.done",
            query_key=self._query_key,
            days=len(points),
            written=written,
        )
        return ToneIngestResult(
            query_key=self._query_key,
            days_fetched=len(points),
            rows_written=written,
            first_day=points[0].day.date().isoformat() if points else None,
            last_day=points[-1].day.date().isoformat() if points else None,
        )
