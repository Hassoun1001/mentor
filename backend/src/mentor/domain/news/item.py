"""NewsItem value object."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from mentor.domain.errors import ValidationError
from mentor.domain.news.classifier import NewsClassification


@dataclass(frozen=True, slots=True)
class NewsItem:
    id: uuid.UUID
    source: str
    url: str
    ts: datetime
    headline: str
    summary: str | None
    classification: NewsClassification | None

    def __post_init__(self) -> None:
        if not self.headline.strip():
            raise ValidationError("headline required", field="headline")
        if not self.source.strip():
            raise ValidationError("source required", field="source")
        if self.ts.tzinfo is None:
            raise ValidationError("ts must be timezone-aware", field="ts")
