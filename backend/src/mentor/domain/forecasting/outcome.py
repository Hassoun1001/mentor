"""What a graded call records, and how a re-grade of it is described.

A call's outcome is whether the market closed above the price it was made
from, measured at the close of its own horizon bar. One rule, shared by the
resolver and the re-grade, so the two can never disagree about what "up"
means.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


def outcome_of(asof_close: Decimal, realised_close: Decimal) -> int:
    """1 when the realised close is above the call's starting price, else 0."""
    return 1 if realised_close > asof_close else 0


@dataclass(frozen=True, slots=True)
class OutcomeRegrade:
    """A graded call moved onto its own finished horizon bar."""

    prediction_id: uuid.UUID
    timeframe: str
    old_close: Decimal
    old_outcome: int
    new_close: Decimal
    outcome_bar_ts: datetime
    asof_close: Decimal

    @property
    def new_outcome(self) -> int:
        return outcome_of(self.asof_close, self.new_close)

    @property
    def flips(self) -> bool:
        return self.new_outcome != self.old_outcome
