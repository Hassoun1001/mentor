"""Economic-calendar ingestion orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from mentor.domain.calendar.adapter import EconomicCalendarAdapter
from mentor.infrastructure.repositories.economic_events import EconomicEventRepository
from mentor.logging import get_logger

log = get_logger("mentor.calendar.service")


@dataclass(frozen=True, slots=True)
class CalendarIngestionResult:
    fetched: int
    upserted: int


class CalendarService:
    def __init__(self, *, adapter: EconomicCalendarAdapter, repo: EconomicEventRepository) -> None:
        self._adapter = adapter
        self._repo = repo

    async def ingest(self, *, since: datetime, until: datetime) -> CalendarIngestionResult:
        batch = []
        async for item in self._adapter.fetch(since=since, until=until):
            batch.append(item)
        upserted = await self._repo.upsert_raw(batch)
        log.info("calendar.ingest.done", fetched=len(batch), upserted=upserted)
        return CalendarIngestionResult(fetched=len(batch), upserted=upserted)
