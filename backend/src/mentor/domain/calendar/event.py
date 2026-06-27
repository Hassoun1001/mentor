"""Economic event value object."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import IntEnum

from mentor.domain.errors import ValidationError


class ImpactLevel(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @property
    def normalised(self) -> Decimal:
        return {
            ImpactLevel.LOW: Decimal("0.25"),
            ImpactLevel.MEDIUM: Decimal("0.55"),
            ImpactLevel.HIGH: Decimal("0.9"),
        }[self]


@dataclass(frozen=True, slots=True)
class EconomicEvent:
    id: uuid.UUID
    source: str
    ts: datetime
    name: str
    country: str  # ISO-ish country/region code: "US", "EU", "UK", "JP", …
    impact: ImpactLevel
    forecast: str | None
    previous: str | None
    actual: str | None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("name required", field="name")
        if not self.source.strip():
            raise ValidationError("source required", field="source")
        if not self.country.strip():
            raise ValidationError("country required", field="country")
        if self.ts.tzinfo is None:
            raise ValidationError("ts must be timezone-aware", field="ts")
