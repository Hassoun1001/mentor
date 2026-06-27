"""News classifier contract + value objects.

Categories follow the plan's vocabulary (§6.C): macro, regulatory,
geopolitical, risk-off, hype, other. The classifier never says "buy" —
it scores impact and confidence so the forecaster can downweight or
ignore low-confidence noise.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError


class NewsCategory(StrEnum):
    MACRO = "macro"
    REGULATORY = "regulatory"
    GEOPOLITICAL = "geopolitical"
    RISK_OFF = "risk-off"
    HYPE = "hype"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class NewsClassification:
    category: NewsCategory
    impact: Decimal  # 0–1
    confidence: Decimal  # 0–1
    rationale: str

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.impact <= Decimal("1")):
            raise ValidationError("impact must be in [0, 1]", field="impact")
        if not (Decimal("0") <= self.confidence <= Decimal("1")):
            raise ValidationError("confidence must be in [0, 1]", field="confidence")
        if not self.rationale.strip():
            raise ValidationError("rationale required", field="rationale")


class NewsClassifier(ABC):
    @abstractmethod
    async def classify(self, *, headline: str, summary: str | None) -> NewsClassification: ...
