"""Journal analytics — pure aggregation over closed trades.

Numbers like win rate and expectancy are the only honest measure of a
trader's edge. They are recomputed from the raw trade rows on every call,
not cached, so the user always sees the truth — including the cost of a
single bad trade.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.journal.trade import Trade, TradeStatus
from mentor.domain.money import Percent


@dataclass(frozen=True, slots=True)
class JournalAnalytics:
    sample_size: int
    wins: int
    losses: int
    breakeven: int
    win_rate: Percent
    avg_win_r: Decimal
    avg_loss_r: Decimal  # positive magnitude
    expectancy_r: Decimal
    profit_factor: Decimal | None
    largest_win_r: Decimal
    largest_loss_r: Decimal  # signed (negative)
    total_r: Decimal


def compute_analytics(trades: Sequence[Trade]) -> JournalAnalytics:
    closed = [t for t in trades if t.status is TradeStatus.CLOSED and t.realised_r is not None]
    if not closed:
        zero = Decimal("0")
        return JournalAnalytics(
            sample_size=0,
            wins=0,
            losses=0,
            breakeven=0,
            win_rate=Percent(zero),
            avg_win_r=zero,
            avg_loss_r=zero,
            expectancy_r=zero,
            profit_factor=None,
            largest_win_r=zero,
            largest_loss_r=zero,
            total_r=zero,
        )

    rs = [t.realised_r for t in closed if t.realised_r is not None]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]
    breakeven = sum(1 for r in rs if r == 0)

    win_rate = Decimal(len(wins)) / Decimal(len(rs)) if rs else Decimal("0")
    avg_win = sum(wins, Decimal("0")) / Decimal(len(wins)) if wins else Decimal("0")
    avg_loss_magnitude = (
        -sum(losses, Decimal("0")) / Decimal(len(losses)) if losses else Decimal("0")
    )
    expectancy = win_rate * avg_win - (Decimal("1") - win_rate) * avg_loss_magnitude

    total_wins = sum(wins, Decimal("0"))
    total_losses = -sum(losses, Decimal("0"))
    profit_factor = total_wins / total_losses if total_losses > 0 else None

    return JournalAnalytics(
        sample_size=len(rs),
        wins=len(wins),
        losses=len(losses),
        breakeven=breakeven,
        win_rate=Percent(win_rate),
        avg_win_r=avg_win,
        avg_loss_r=avg_loss_magnitude,
        expectancy_r=expectancy,
        profit_factor=profit_factor,
        largest_win_r=max(rs) if rs else Decimal("0"),
        largest_loss_r=min(rs) if rs else Decimal("0"),
        total_r=sum(rs, Decimal("0")),
    )
