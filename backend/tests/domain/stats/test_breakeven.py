"""The hurdle a call must clear is not 50%, and the arithmetic must say so."""

from __future__ import annotations

import math
import random

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.stats.breakeven import (
    breakeven_win_rate,
    estimate_breakeven,
    mean_abs_move,
)
from mentor.domain.stats.significance import assess_proportion


def _walk(n: int, *, step: float, start: float = 1.08) -> list[float]:
    """A seeded random walk — deterministic, but with real dispersion.

    A strict alternating zigzag was the first version and it was useless:
    over any even horizon it returns exactly to where it started, so the
    measured move is 0 and every hurdle collapses. (The estimator handled
    it correctly — it reported "unmeasurable" rather than dividing by
    zero — which is how the fixture bug surfaced.)
    """
    rng = random.Random(7)
    out = [start]
    for _ in range(n - 1):
        out.append(out[-1] + rng.uniform(-step, step))
    return out


# ---------- the formula ----------


def test_free_trading_puts_the_hurdle_at_a_coin_flip() -> None:
    assert breakeven_win_rate(mean_abs_move=0.002, cost_per_trade=0.0) == 0.5


def test_the_hurdle_rises_with_cost_and_falls_with_horizon() -> None:
    cheap = breakeven_win_rate(mean_abs_move=0.002, cost_per_trade=0.0001)
    dear = breakeven_win_rate(mean_abs_move=0.002, cost_per_trade=0.0004)
    longer = breakeven_win_rate(mean_abs_move=0.008, cost_per_trade=0.0001)

    assert 0.5 < cheap < dear
    # Same cost over a four-times-bigger move is a quarter of the hurdle.
    assert longer - 0.5 == pytest.approx((cheap - 0.5) / 4)


def test_the_hurdle_matches_the_closed_form() -> None:
    p = breakeven_win_rate(mean_abs_move=0.00218, cost_per_trade=0.000086)
    assert p == pytest.approx(0.5 + 0.000086 / (2 * 0.00218))


def test_cost_swallowing_the_move_is_capped_rather_than_exceeding_certainty() -> None:
    """A hurdle at or above 100% is not a usable baseline — and
    `assess_proportion` rejects one outright — but the situation it
    describes (friction as large as the move) is real and must not crash."""
    p = breakeven_win_rate(mean_abs_move=0.0001, cost_per_trade=0.01)
    assert p < 1.0
    assess_proportion(50, 100, baseline=p)  # must not raise


def test_nonsense_inputs_are_rejected() -> None:
    with pytest.raises(ValidationError):
        breakeven_win_rate(mean_abs_move=0.0, cost_per_trade=0.0001)
    with pytest.raises(ValidationError):
        breakeven_win_rate(mean_abs_move=0.002, cost_per_trade=-1.0)


# ---------- measuring the move ----------


def test_windows_do_not_overlap() -> None:
    """Overlapping windows share bars, so they are not independent draws —
    the same mistake the significance layer refuses to make when grading
    predictions. 100 bars at horizon 10 is 9 disjoint windows, not 90."""
    _, n = mean_abs_move(_walk(100, step=0.001), horizon_bars=10)
    assert n == 9


def test_a_bigger_horizon_measures_a_bigger_move() -> None:
    closes = [1.08 + 0.0001 * i for i in range(200)]  # steady drift
    short, _ = mean_abs_move(closes, horizon_bars=5)
    long_, _ = mean_abs_move(closes, horizon_bars=20)
    assert long_ > short * 3


def test_too_few_bars_measures_nothing_rather_than_guessing() -> None:
    move, n = mean_abs_move([1.08, 1.09], horizon_bars=24)
    assert (move, n) == (0.0, 0)


def test_a_zero_horizon_is_rejected() -> None:
    with pytest.raises(ValidationError):
        mean_abs_move([1.0] * 50, horizon_bars=0)


# ---------- the estimate ----------


def test_a_measured_hurdle_sits_above_a_coin_flip_and_says_why() -> None:
    basis = estimate_breakeven(
        _walk(1000, step=0.0005), horizon_bars=5, cost_per_trade_price=0.00012
    )
    assert basis.measured
    assert basis.breakeven > 0.5
    assert basis.n_windows >= 30
    assert "Breakeven" in basis.note
    assert basis.hurdle_pp == pytest.approx((basis.breakeven - 0.5) * 100)


def test_zero_cost_reproduces_the_coin_flip_exactly() -> None:
    basis = estimate_breakeven(
        _walk(1000, step=0.0005), horizon_bars=5, cost_per_trade_price=0.0
    )
    assert basis.measured
    assert basis.breakeven == 0.5


def test_too_few_windows_admits_it_instead_of_quoting_a_number() -> None:
    """The fallback is the old behaviour — a coin flip — but flagged, so a
    caller can show that the economic bar is unknown rather than met."""
    basis = estimate_breakeven(
        _walk(100, step=0.0005), horizon_bars=24, cost_per_trade_price=0.00012
    )
    assert not basis.measured
    assert basis.breakeven == 0.5
    assert "could not be measured" in basis.note
    assert "understates the real bar" in basis.note


def test_the_hurdle_shrinks_as_the_horizon_grows() -> None:
    """The finding that reorders the roadmap: a fixed cost is a smaller
    share of a bigger move, so the 5-day lane is far easier to clear than
    the 24-hour one, and grading both against 50% hid that completely."""
    closes = _walk(4000, step=0.0004)
    short = estimate_breakeven(closes, horizon_bars=24, cost_per_trade_price=0.00012)
    long_ = estimate_breakeven(closes, horizon_bars=120, cost_per_trade_price=0.00012)

    assert short.measured and long_.measured
    assert short.breakeven > long_.breakeven > 0.5


def test_friction_as_large_as_the_move_names_the_cost_as_the_problem() -> None:
    basis = estimate_breakeven(
        _walk(1000, step=0.000005), horizon_bars=5, cost_per_trade_price=0.0012
    )
    assert basis.measured
    assert "the cost, not the forecast, is the binding constraint" in basis.note


def test_negative_cost_is_rejected() -> None:
    with pytest.raises(ValidationError):
        estimate_breakeven([1.08] * 100, horizon_bars=5, cost_per_trade_price=-0.001)


def test_non_positive_closes_do_not_divide_by_zero() -> None:
    basis = estimate_breakeven([0.0] * 200, horizon_bars=5, cost_per_trade_price=0.00012)
    assert not basis.measured
    assert math.isfinite(basis.breakeven)


# ---------- what it changes downstream ----------


def test_a_rate_that_beats_a_coin_but_not_the_spread_is_no_longer_an_edge() -> None:
    """The defect this exists to fix. 5,200 of 10,000 is 52%: significantly
    better than a coin flip, and a loser after costs on the 24-hour lane."""
    naive = assess_proportion(5_200, 10_000)
    honest = assess_proportion(5_200, 10_000, baseline=0.5197)

    assert naive.significant  # "the edge is real"
    assert not honest.significant  # ...it is not
    assert not honest.worse_than_baseline  # nor is it proven worse — just unproven


def test_the_verdict_names_the_bar_it_was_graded_against() -> None:
    v = assess_proportion(
        5_100,
        10_000,
        baseline=0.5197,
        label="independent windows",
        baseline_label="the spread-adjusted breakeven",
    )
    assert "51.97%" in v.verdict
    assert "the spread-adjusted breakeven" in v.verdict
    assert "coin flip" not in v.verdict


def test_a_coin_flip_baseline_still_reads_as_a_coin_flip() -> None:
    v = assess_proportion(24, 40)
    assert "50%" in v.verdict
    assert "coin flip" in v.verdict
