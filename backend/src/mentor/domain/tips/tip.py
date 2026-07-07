"""Stock-tip value objects.

A "tip" is one actionable call from a tipster (a friend, a newsletter, a
Discord). We keep the tipster's own vocabulary — category and action —
because the whole point is to score *their* framing honestly, not to
relabel it into ours.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from mentor.domain.errors import ValidationError


class TipCategory(StrEnum):
    SAFE = "safe"
    HIGH_RISK = "high_risk"
    PICKS_AND_SHOVELS = "picks_and_shovels"
    OTHER = "other"


class TipAction(StrEnum):
    BUY = "buy"
    BUY_ON_DIP = "buy_on_dip"
    HOLD = "hold"
    WATCH = "watch"
    AVOID = "avoid"


class Conviction(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class ParsedTip:
    """One tip as extracted from a raw message."""

    ticker: str
    category: TipCategory
    action: TipAction
    conviction: Conviction
    note: str

    def __post_init__(self) -> None:
        if not self.ticker.strip():
            raise ValidationError("tip ticker is required", field="ticker")
        # Normalise ticker to uppercase, no surrounding whitespace.
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
