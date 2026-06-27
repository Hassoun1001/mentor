"""Forecast value object.

A forecast is **only**:

- A probability of an up move over a defined horizon.
- A confidence band (how far from 50/50).
- A direction lean (long / short / neutral) derived from p_up.
- A short, plain-language reasoning string.
- The features that drove it (so the calibration log is auditable).

A forecast is **never**:

- A price target.
- A timeline ("by tomorrow").
- A guarantee.

Principle 02 from the plan: reasoning, never verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import Timeframe


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


def direction_from_probability(
    p_up: Decimal, *, neutral_band: Decimal = Decimal("0.05")
) -> Direction:
    """`neutral_band` is half-width: |p - 0.5| < band → neutral."""
    if p_up >= Decimal("0.5") + neutral_band:
        return Direction.LONG
    if p_up <= Decimal("0.5") - neutral_band:
        return Direction.SHORT
    return Direction.NEUTRAL


@dataclass(frozen=True, slots=True)
class Forecast:
    symbol: str
    timeframe: Timeframe
    asof: datetime
    asof_close: Decimal
    horizon_bars: int
    p_up: Decimal
    confidence: Decimal
    direction: Direction
    model_name: str
    reasoning: str
    features: dict[str, Decimal]

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.p_up <= Decimal("1")):
            raise ValidationError("p_up must be in [0, 1]", field="p_up")
        if not (Decimal("0") <= self.confidence <= Decimal("1")):
            raise ValidationError("confidence must be in [0, 1]", field="confidence")
        if self.horizon_bars < 1:
            raise ValidationError("horizon_bars must be >= 1", field="horizon_bars")
        if self.asof.tzinfo is None:
            raise ValidationError("asof must be timezone-aware", field="asof")
        if not self.reasoning.strip():
            raise ValidationError("reasoning required", field="reasoning")
