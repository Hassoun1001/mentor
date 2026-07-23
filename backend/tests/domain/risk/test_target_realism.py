"""Reward:risk is arithmetic, not edge — the plan must say so."""

from __future__ import annotations

from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.risk.target_realism import assess_target


def _at(reward: str, sigma: str = "30", win: str | None = None) -> object:
    stop = Decimal("45")
    return assess_target(
        stop_pips=stop,
        target_pips=stop * Decimal(reward),
        expected_move_pips=Decimal(sigma),
        model_win_rate=Decimal(win) if win is not None else None,
    )


def test_two_to_one_demands_a_third_of_trades() -> None:
    r = _at("2")
    assert r.reward_risk == Decimal("2.00")
    assert r.breakeven_win_rate == pytest.approx(Decimal("0.3333"), abs=Decimal("0.0001"))
    assert "33%" in r.note


def test_the_no_edge_hit_rate_equals_the_breakeven_rate() -> None:
    """The whole point: widening the target cannot manufacture an edge.

    A driftless walk touches the target first s/(s+t) of the time, which is
    algebraically identical to the 1/(1+R) needed to break even. The two
    move together at every reward multiple.
    """
    for reward in ("1", "1.5", "2", "3", "5"):
        r = _at(reward)
        assert r.random_walk_hit_rate == r.breakeven_win_rate


def test_a_distant_target_is_flagged_against_the_time_stop() -> None:
    # stop 45 pips on a 30-pip sigma, target 2R -> 3 sigma away.
    r = _at("2", sigma="30")
    assert r.target_sigma == Decimal("3.00")
    assert "most of these trades will end at the time stop" in r.note


def test_a_near_target_is_not_flagged() -> None:
    # A big sigma makes the same target close in sigma terms.
    r = _at("1", sigma="90")
    assert r.target_sigma < Decimal("2")
    assert "time stop" not in r.note or "end at the time stop" not in r.note


def test_a_model_below_the_bar_is_called_out() -> None:
    # 53% accuracy against a 3:1 target needing 25%... that clears. Use 5:1.
    r = _at("2", win="0.30")  # needs 33%, has 30%
    assert r.has_edge is False
    assert "no expected edge" in r.note


def test_a_model_above_the_bar_is_credited_without_overselling() -> None:
    r = _at("2", win="0.53")
    assert r.has_edge is True
    assert "Thin" in r.note


def test_unknown_accuracy_is_stated_as_unknown() -> None:
    r = _at("2")
    assert r.has_edge is None
    assert "unknown" in r.note


def test_zero_sigma_does_not_divide_by_zero() -> None:
    r = assess_target(
        stop_pips=Decimal("45"),
        target_pips=Decimal("90"),
        expected_move_pips=Decimal("0"),
        model_win_rate=None,
    )
    assert r.target_sigma == Decimal("0.00")
    assert r.breakeven_win_rate > 0


def test_bad_inputs_are_rejected() -> None:
    with pytest.raises(ValidationError):
        assess_target(
            stop_pips=Decimal("0"),
            target_pips=Decimal("90"),
            expected_move_pips=Decimal("30"),
        )
    with pytest.raises(ValidationError):
        assess_target(
            stop_pips=Decimal("45"),
            target_pips=Decimal("-1"),
            expected_move_pips=Decimal("30"),
        )
