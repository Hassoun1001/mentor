"""Sizing must refuse to present arithmetic as a tradeable position."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.instruments import get_instrument
from mentor.domain.money import Money, Percent
from mentor.domain.risk.position_sizing import (
    Direction,
    RiskInputs,
    calculate_position,
)

EURUSD = get_instrument("EURUSD")


def _size(entry: str, stop: str, target: str | None = None) -> object:
    return calculate_position(
        RiskInputs(
            account_balance=Money(Decimal("10000"), "USD"),
            risk=Percent.from_percent(Decimal("1")),
            entry=Decimal(entry),
            stop=Decimal(stop),
            target=Decimal(target) if target else None,
            direction=Direction.LONG,
            instrument=EURUSD,
            quote_to_account_rate=Decimal("1"),
        )
    )


def test_a_stop_inside_the_spread_is_called_out() -> None:
    """Regression: a 0.1-pip stop produced 100 lots on a $10,000 account —
    about 1100:1 leverage — with no warning at all. The risk figure read a
    tidy $100, but a dealing spread is several times that stop, so the trade
    would be closed by the spread before it moved. The number described
    nothing that could actually happen."""
    sizing = _size("1.10000", "1.09999")
    joined = " ".join(sizing.notes)  # type: ignore[attr-defined]

    assert "inside a normal dealing spread" in joined
    assert "leverage" in joined


def test_extreme_leverage_is_named_as_arithmetic() -> None:
    sizing = _size("1.10000", "1.09999")
    note = next(n for n in sizing.notes if "leverage" in n)  # type: ignore[attr-defined]
    assert "not a trade" in note


def test_a_normal_trade_carries_neither_warning() -> None:
    sizing = _size("1.10000", "1.09500", "1.11000")
    joined = " ".join(sizing.notes)  # type: ignore[attr-defined]

    assert "spread" not in joined
    assert "leverage" not in joined


def test_the_risk_budget_is_still_never_exceeded() -> None:
    """Rounding is down, never up — the property that matters most here."""
    sizing = _size("1.10000", "1.09930")  # 7 pips, awkward division
    assert sizing.money_at_risk.amount <= Decimal("100")  # type: ignore[attr-defined]
