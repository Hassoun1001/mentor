"""News-source adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RawNewsItem:
    source: str
    url: str
    ts: datetime
    headline: str
    summary: str | None


class NewsAdapter(ABC):
    name: str

    @abstractmethod
    def fetch(self, *, query: str, since: datetime) -> AsyncIterator[RawNewsItem]:
        """Yield raw news items since `since`, descending by recency.

        Implemented as an async generator in concrete adapters; declared
        here as a plain method returning an async iterator so the abstract
        signature has no unreachable `yield`.
        """
        ...
