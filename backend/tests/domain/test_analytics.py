"""Journal analytics over a list of closed trades."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from mentor.domain.journal.analytics import compute_analytics
from mentor.domain.journal.trade import Trade, TradeStatus
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction


def _closed_trade(r: Decimal) -> Trade:
    return Trade(
        id=uuid.uuid4(),
        symbol="EURUSD",
        direction=Direction.LONG,
        status=TradeStatus.CLOSED,
        size_lots=Decimal("0.10"),
        planned_entry=Decimal("1.08500"),
        planned_stop=Decimal("1.08200"),
        planned_target=Decimal("1.09100"),
        initial_risk=Money.of("100", "USD"),
        reason="ok",
        actual_entry=Decimal("1.08500"),
        actual_exit=Decimal("1.08600"),
        entry_ts=datetime(2026, 1, 1, tzinfo=UTC),
        exit_ts=datetime(2026, 1, 1, 12, tzinfo=UTC),
        realised_pnl=Money(r * Decimal("100"), "USD"),
        realised_r=r,
    )


def test_empty_analytics() -> None:
    a = compute_analytics([])
    assert a.sample_size == 0
    assert a.profit_factor is None


def test_classic_40_percent_2to1() -> None:
    """4 wins at +2R, 6 losses at -1R = 10 trades, +0.2R expectancy."""
    trades = [_closed_trade(Decimal("2"))] * 4 + [_closed_trade(Decimal("-1"))] * 6
    a = compute_analytics(trades)
    assert a.sample_size == 10
    assert a.wins == 4
    assert a.losses == 6
    assert a.expectancy_r == Decimal("0.2")
    assert a.win_rate.as_percent == Decimal("40")
    assert a.total_r == Decimal("2")
    assert a.largest_win_r == Decimal("2")
    assert a.largest_loss_r == Decimal("-1")


def test_planned_trades_ignored() -> None:
    closed = _closed_trade(Decimal("1"))
    planned = Trade(
        id=uuid.uuid4(),
        symbol="EURUSD",
        direction=Direction.LONG,
        status=TradeStatus.PLANNED,
        size_lots=Decimal("0.10"),
        planned_entry=Decimal("1.085"),
        planned_stop=Decimal("1.082"),
        planned_target=None,
        initial_risk=Money.of("50", "USD"),
        reason="ok",
    )
    a = compute_analytics([closed, planned])
    assert a.sample_size == 1
