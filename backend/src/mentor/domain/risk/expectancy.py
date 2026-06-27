"""Expectancy & R-multiple math.

> Expectancy = (win% × avg win) − (loss% × avg loss); the average profit per
> trade over many trades.   — Mentor glossary

R-multiples (Tharp) normalise trade outcomes by the initial risk: a trade
that returned 2x what was risked is +2R; a full stop-out is −1R. R-multiples
let a trader compare strategies independently of position size and account
size, which is why the mentor framing teaches them.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.money import Money, Percent, to_decimal


@dataclass(frozen=True, slots=True)
class Expectancy:
    """A summary of how an edge translates into per-trade expected value."""

    win_rate: Percent
    avg_win_r: Decimal
    avg_loss_r: Decimal
    expected_value_r: Decimal
    profit_factor: Decimal | None
    sample_size: int

    @property
    def is_positive(self) -> bool:
        return self.expected_value_r > 0


def expectancy(
    *,
    win_rate: Percent,
    avg_win_r: Decimal | int | str | float,
    avg_loss_r: Decimal | int | str | float,
    sample_size: int = 0,
) -> Expectancy:
    """Compute expectancy in R-multiples.

    `avg_loss_r` is supplied as a positive magnitude (e.g. `1.0` for a
    full-R loss). The formula treats it as a loss internally so callers
    never have to remember sign conventions.
    """
    if sample_size < 0:
        raise ValidationError("sample_size must be >= 0", field="sample_size")

    win = win_rate.fraction
    loss = Decimal("1") - win

    aw = to_decimal(avg_win_r, field="avg_win_r")
    al = to_decimal(avg_loss_r, field="avg_loss_r")
    if aw < 0:
        raise ValidationError("avg_win_r must be >= 0", field="avg_win_r")
    if al < 0:
        raise ValidationError("avg_loss_r must be >= 0 (supplied as magnitude)", field="avg_loss_r")

    ev = win * aw - loss * al

    total_wins = win * aw
    total_losses = loss * al
    profit_factor = total_wins / total_losses if total_losses > 0 else None

    return Expectancy(
        win_rate=win_rate,
        avg_win_r=aw,
        avg_loss_r=al,
        expected_value_r=ev,
        profit_factor=profit_factor,
        sample_size=sample_size,
    )


def r_multiple(*, entry: Money, exit_: Money, initial_risk: Money) -> Decimal:
    """Express a realised trade outcome in R-multiples.

    A trade where the entry → exit P&L is `2 × initial_risk` returns `2`.
    A trade stopped out exactly at the initial stop returns `-1`.
    """
    if entry.currency != exit_.currency or entry.currency != initial_risk.currency:
        raise ValidationError("entry, exit, and initial_risk must share a currency")
    if initial_risk.amount <= 0:
        raise ValidationError("initial_risk must be positive", field="initial_risk")

    pnl = exit_.amount - entry.amount
    return pnl / initial_risk.amount
