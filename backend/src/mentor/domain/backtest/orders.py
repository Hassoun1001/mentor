"""Order intents and position state.

`OrderIntent` is the **strategy's** vocabulary: "I'd like to go long this
size with this stop." It is *never* a fill. The broker simulator turns
the intent into a fill at the *next* bar's open — preventing the
strategy from acting on the current bar's close (which would be
borderline lookahead in a live system).

`Position` is the **broker's** record of an open trade. `ClosedTrade`
captures everything needed for the metrics layer to compute R, costs,
and P&L without re-deriving them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.money import to_decimal
from mentor.domain.risk.position_sizing import Direction


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class ExitReason(StrEnum):
    STOP = "stop"
    TARGET = "target"
    SIGNAL = "signal"
    END_OF_DATA = "end_of_data"


@dataclass(frozen=True, slots=True)
class OrderIntent:
    direction: Direction
    size_lots: Decimal
    stop_price: Decimal
    target_price: Decimal | None
    reason: str

    def __post_init__(self) -> None:
        for name, raw in (
            ("size_lots", self.size_lots),
            ("stop_price", self.stop_price),
        ):
            d = to_decimal(raw, field=name)
            if d <= 0 and name == "stop_price":
                raise ValidationError(f"{name} must be positive", field=name)
            if d < 0:
                raise ValidationError(f"{name} must be >= 0", field=name)
            object.__setattr__(self, name, d)
        if self.target_price is not None:
            object.__setattr__(
                self, "target_price", to_decimal(self.target_price, field="target_price")
            )


@dataclass(frozen=True, slots=True)
class Position:
    direction: Direction
    size_lots: Decimal
    entry_price: Decimal
    entry_ts: datetime
    stop_price: Decimal
    target_price: Decimal | None
    initial_risk_amount: Decimal  # in account currency
    reason: str


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    direction: Direction
    size_lots: Decimal
    entry_price: Decimal
    exit_price: Decimal
    entry_ts: datetime
    exit_ts: datetime
    initial_risk_amount: Decimal
    realised_pnl_account: Decimal
    realised_r: Decimal
    costs_paid: Decimal
    exit_reason: ExitReason
    reason: str
