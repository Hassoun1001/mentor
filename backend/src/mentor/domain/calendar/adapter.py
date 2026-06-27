"""Calendar adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime

from mentor.domain.calendar.event import ImpactLevel


@dataclass(frozen=True, slots=True)
class RawEconomicEvent:
    source: str
    external_id: str  # provider-side unique id — used for dedup
    ts: datetime
    name: str
    country: str
    impact: ImpactLevel
    forecast: str | None
    previous: str | None
    actual: str | None


class EconomicCalendarAdapter(ABC):
    name: str

    @abstractmethod
    def fetch(self, *, since: datetime, until: datetime) -> AsyncIterator[RawEconomicEvent]:
        """Async generator in concrete adapters; plain async-iterator
        signature here so the abstract has no unreachable `yield`."""
        ...
