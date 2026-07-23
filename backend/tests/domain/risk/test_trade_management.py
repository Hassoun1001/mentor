"""Trade-management rules: direction symmetry and volatility adaptation."""

from __future__ import annotations

from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.risk.trade_management import build_trade_management

PIP = Decimal("0.0001")


def _long(expected_move_pips: str = "30") -> object:
    return build_trade_management(
        direction=Direction.LONG,
        entry=Decimal("1.1000"),
        stop=Decimal("1.0950"),  # 50 pips risk
        pip_size=PIP,
        expected_move_pips=Decimal(expected_move_pips),
        horizon_bars=24,
    )


def test_long_levels_sit_above_entry() -> None:
    plan = _long()
    assert plan.break_even_pips == Decimal("50.0")  # 1R
    assert plan.break_even_price > Decimal("1.1000")
    assert plan.partial_close_price > Decimal("1.1000")


def test_short_levels_mirror_below_entry() -> None:
    plan = build_trade_management(
        direction=Direction.SHORT,
        entry=Decimal("1.1000"),
        stop=Decimal("1.1050"),  # 50 pips risk
        pip_size=PIP,
        expected_move_pips=Decimal("30"),
        horizon_bars=24,
    )
    assert plan.break_even_pips == Decimal("50.0")
    assert plan.break_even_price < Decimal("1.1000")
    assert plan.partial_close_price < Decimal("1.1000")


def test_trail_follows_volatility_not_a_fixed_guess() -> None:
    calm = _long("20")
    wild = _long("80")
    assert calm.trail_distance_pips == Decimal("20.0")
    assert wild.trail_distance_pips == Decimal("80.0")
    assert wild.trail_distance_pips > calm.trail_distance_pips


def test_zero_expected_move_falls_back_to_risk_distance() -> None:
    plan = _long("0")
    assert plan.trail_distance_pips == Decimal("50.0")  # the 1R risk


def test_time_stop_matches_the_forecast_horizon() -> None:
    plan = _long()
    assert plan.time_stop_bars == 24
    assert any("Time stop" in r for r in plan.rules)


def test_rules_include_the_never_widen_discipline() -> None:
    plan = _long()
    assert any("never move the stop away" in r.lower() for r in plan.rules)


def test_partial_close_is_half_by_default() -> None:
    assert _long().partial_close_fraction == Decimal("0.5")


def test_identical_entry_and_stop_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_trade_management(
            direction=Direction.LONG,
            entry=Decimal("1.1000"),
            stop=Decimal("1.1000"),
            pip_size=PIP,
            expected_move_pips=Decimal("30"),
            horizon_bars=24,
        )


def test_bad_horizon_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_trade_management(
            direction=Direction.LONG,
            entry=Decimal("1.1000"),
            stop=Decimal("1.0950"),
            pip_size=PIP,
            expected_move_pips=Decimal("30"),
            horizon_bars=0,
        )
