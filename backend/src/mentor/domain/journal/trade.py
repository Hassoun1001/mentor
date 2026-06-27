"""The Trade aggregate — a small, explicit state machine.

States:    planned → open → closed
                  ↓
              cancelled

Transitions are pure: each `open_trade` / `close_trade` returns a *new*
Trade rather than mutating in place. The application layer persists the
result; the domain itself is timeless and testable in isolation.

R-multiple is **always recomputed** from the trade's own fields when a
trade enters `closed`. It is never user-editable. If a regulator (or you)
ever audits the journal, every R can be reproduced from the row.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.money import Money, to_decimal
from mentor.domain.risk.position_sizing import Direction


class TradeStatus(StrEnum):
    PLANNED = "planned"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# --------------------------------------------------------------------- plan


@dataclass(frozen=True, slots=True)
class TradePlan:
    """The inputs that define a planned trade before it has been opened."""

    symbol: str
    direction: Direction
    size_lots: Decimal
    entry: Decimal
    stop: Decimal
    target: Decimal | None
    initial_risk: Money
    reason: str

    def __post_init__(self) -> None:
        if not self.reason or not self.reason.strip():
            raise ValidationError(
                "reason is required — no trade without a written rationale",
                field="reason",
            )
        for name, raw in (
            ("size_lots", self.size_lots),
            ("entry", self.entry),
            ("stop", self.stop),
        ):
            d = to_decimal(raw, field=name)
            if d <= 0 and name != "size_lots":
                raise ValidationError(f"{name} must be positive", field=name)
            if name == "size_lots" and d < 0:
                raise ValidationError("size_lots must be >= 0", field=name)
            object.__setattr__(self, name, d)
        if self.target is not None:
            t = to_decimal(self.target, field="target")
            if t <= 0:
                raise ValidationError("target must be positive", field="target")
            object.__setattr__(self, "target", t)
        if self.entry == self.stop:
            raise ValidationError("entry and stop must differ", field="stop")
        if not self.initial_risk.is_positive:
            raise ValidationError("initial_risk must be positive", field="initial_risk")
        if self.direction is Direction.LONG and self.stop >= self.entry:
            raise ValidationError("long stop must be below entry", field="stop")
        if self.direction is Direction.SHORT and self.stop <= self.entry:
            raise ValidationError("short stop must be above entry", field="stop")


# --------------------------------------------------------------------- trade


@dataclass(frozen=True, slots=True)
class Trade:
    """A trade in any state.

    `realised_pnl` and `realised_r` are populated only once `status` is
    `CLOSED`. They are derived from the other fields — never accepted from
    the caller — so journal analytics are reproducible.
    """

    id: uuid.UUID
    symbol: str
    direction: Direction
    status: TradeStatus
    size_lots: Decimal
    planned_entry: Decimal
    planned_stop: Decimal
    planned_target: Decimal | None
    initial_risk: Money
    reason: str
    actual_entry: Decimal | None = None
    actual_exit: Decimal | None = None
    entry_ts: datetime | None = None
    exit_ts: datetime | None = None
    realised_pnl: Money | None = None
    realised_r: Decimal | None = None
    mistake_tags: tuple[str, ...] = ()
    emotion: str | None = None
    notes: str | None = None


# ---------------------------------------------------------- transitions


def plan_trade(plan: TradePlan, *, trade_id: uuid.UUID | None = None) -> Trade:
    return Trade(
        id=trade_id or uuid.uuid4(),
        symbol=plan.symbol.upper(),
        direction=plan.direction,
        status=TradeStatus.PLANNED,
        size_lots=plan.size_lots,
        planned_entry=plan.entry,
        planned_stop=plan.stop,
        planned_target=plan.target,
        initial_risk=plan.initial_risk,
        reason=plan.reason.strip(),
    )


def open_trade(trade: Trade, *, fill_price: Decimal, at: datetime | None = None) -> Trade:
    if trade.status is not TradeStatus.PLANNED:
        raise ValidationError(
            f"only planned trades can be opened (status={trade.status})",
            field="status",
        )
    price = to_decimal(fill_price, field="fill_price")
    if price <= 0:
        raise ValidationError("fill_price must be positive", field="fill_price")
    return replace(
        trade,
        status=TradeStatus.OPEN,
        actual_entry=price,
        entry_ts=at or datetime.now(UTC),
    )


def cancel_trade(trade: Trade) -> Trade:
    if trade.status is not TradeStatus.PLANNED:
        raise ValidationError(
            "only planned trades can be cancelled — close open trades instead",
            field="status",
        )
    return replace(trade, status=TradeStatus.CANCELLED)


def close_trade(
    trade: Trade,
    *,
    exit_price: Decimal,
    instrument: Instrument,
    at: datetime | None = None,
    quote_to_account_rate: Decimal = Decimal("1"),
    mistake_tags: tuple[str, ...] = (),
    emotion: str | None = None,
    notes: str | None = None,
) -> Trade:
    """Close an open trade, deterministically computing P&L and R-multiple.

    Sign convention:

    - long P&L  = (exit - entry) × units × rate
    - short P&L = (entry - exit) × units × rate
    - R         = P&L / initial_risk

    Symmetric so a short closed +50 pips reports the same +R as the long
    that closed +50 pips, just with the price arithmetic flipped.
    """
    if trade.status is not TradeStatus.OPEN:
        raise ValidationError(
            f"only open trades can be closed (status={trade.status})",
            field="status",
        )
    if trade.actual_entry is None:
        # defensive — an OPEN trade should always have entry. Catches data corruption.
        raise ValidationError("open trade missing actual_entry", field="actual_entry")

    exit_p = to_decimal(exit_price, field="exit_price")
    if exit_p <= 0:
        raise ValidationError("exit_price must be positive", field="exit_price")
    rate = to_decimal(quote_to_account_rate, field="quote_to_account_rate")
    if rate <= 0:
        raise ValidationError(
            "quote_to_account_rate must be positive", field="quote_to_account_rate"
        )

    units = trade.size_lots * instrument.contract_size
    direction_sign = Decimal("1") if trade.direction is Direction.LONG else Decimal("-1")
    pnl_quote = direction_sign * (exit_p - trade.actual_entry) * units
    pnl_account = pnl_quote * rate

    pnl_money = Money(pnl_account, trade.initial_risk.currency).quantized()
    r_multiple = (
        pnl_money.amount / trade.initial_risk.amount
        if trade.initial_risk.amount > 0
        else Decimal("0")
    )

    return replace(
        trade,
        status=TradeStatus.CLOSED,
        actual_exit=exit_p,
        exit_ts=at or datetime.now(UTC),
        realised_pnl=pnl_money,
        realised_r=r_multiple,
        mistake_tags=mistake_tags,
        emotion=emotion,
        notes=notes,
    )
