"""Trade aggregate state machine + deterministic R-multiple."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import get_instrument
from mentor.domain.journal.trade import (
    TradePlan,
    TradeStatus,
    cancel_trade,
    close_trade,
    open_trade,
    plan_trade,
)
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction

EURUSD = get_instrument("EURUSD")


def _plan(**overrides):
    base = {
        "symbol": "EURUSD",
        "direction": Direction.LONG,
        "size_lots": Decimal("0.33"),
        "entry": Decimal("1.08500"),
        "stop": Decimal("1.08200"),
        "target": Decimal("1.09100"),
        "initial_risk": Money.of("99", "USD"),
        "reason": "Pullback to 200-EMA in an uptrend, calm calendar.",
    }
    base.update(overrides)
    return TradePlan(**base)


class TestTradePlan:
    def test_requires_reason(self) -> None:
        with pytest.raises(ValidationError):
            _plan(reason="")

    def test_long_stop_must_be_below_entry(self) -> None:
        with pytest.raises(ValidationError):
            _plan(stop=Decimal("1.090"))

    def test_short_stop_must_be_above_entry(self) -> None:
        with pytest.raises(ValidationError):
            _plan(
                direction=Direction.SHORT,
                entry=Decimal("1.08500"),
                stop=Decimal("1.08200"),
                target=None,
            )

    def test_initial_risk_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            _plan(initial_risk=Money(Decimal("0"), "USD"))


class TestStateMachine:
    def test_plan_creates_planned_trade(self) -> None:
        trade = plan_trade(_plan())
        assert trade.status is TradeStatus.PLANNED
        assert trade.actual_entry is None

    def test_open_only_from_planned(self) -> None:
        trade = plan_trade(_plan())
        opened = open_trade(trade, fill_price=Decimal("1.08510"))
        assert opened.status is TradeStatus.OPEN
        assert opened.actual_entry == Decimal("1.08510")

        # cannot open an already-open trade
        with pytest.raises(ValidationError):
            open_trade(opened, fill_price=Decimal("1.085"))

    def test_cancel_only_planned(self) -> None:
        trade = plan_trade(_plan())
        cancelled = cancel_trade(trade)
        assert cancelled.status is TradeStatus.CANCELLED

        opened = open_trade(trade, fill_price=Decimal("1.08500"))
        with pytest.raises(ValidationError):
            cancel_trade(opened)


class TestCloseTrade:
    def test_long_winner_r_multiple(self) -> None:
        """Long EUR/USD: 0.33 lots, entry 1.08500, stop 1.08200, exit 1.09100.

        units = 0.33 * 100_000 = 33_000
        pnl_quote = (1.09100 - 1.08500) * 33_000 = 0.006 * 33_000 = 198 USD
        initial_risk ≈ 99 USD → R ≈ 2.00
        """
        trade = open_trade(plan_trade(_plan()), fill_price=Decimal("1.08500"))
        closed = close_trade(
            trade,
            exit_price=Decimal("1.09100"),
            instrument=EURUSD,
            at=datetime(2026, 6, 25, 12, 0, tzinfo=UTC),
        )
        assert closed.status is TradeStatus.CLOSED
        assert closed.realised_pnl is not None
        assert closed.realised_pnl.amount == Decimal("198.00")
        assert closed.realised_r is not None
        assert closed.realised_r == Decimal("2.00")

    def test_long_loser_r_minus_one(self) -> None:
        trade = open_trade(plan_trade(_plan()), fill_price=Decimal("1.08500"))
        closed = close_trade(trade, exit_price=Decimal("1.08200"), instrument=EURUSD)
        assert closed.realised_r is not None
        # Risk side: 0.33 lots * 100k * 30 pips * 0.0001 = 99 → R = -99/99 = -1
        assert closed.realised_r == Decimal("-1")

    def test_short_winner_symmetric(self) -> None:
        plan = _plan(
            direction=Direction.SHORT,
            entry=Decimal("1.08500"),
            stop=Decimal("1.08800"),
            target=Decimal("1.07900"),
        )
        trade = open_trade(plan_trade(plan), fill_price=Decimal("1.08500"))
        closed = close_trade(trade, exit_price=Decimal("1.07900"), instrument=EURUSD)
        # Same magnitude as the long winner above
        assert closed.realised_r == Decimal("2.00")

    def test_cannot_close_planned(self) -> None:
        trade = plan_trade(_plan())
        with pytest.raises(ValidationError):
            close_trade(trade, exit_price=Decimal("1.091"), instrument=EURUSD)
