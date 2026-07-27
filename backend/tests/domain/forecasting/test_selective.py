"""Abstention: a coverage floor, honest grading, and no free lunch."""

from __future__ import annotations

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.selective import (
    grade_policy,
    select_margin,
)


def _confident_edge() -> tuple[list[float], list[int]]:
    """Confident calls are usually right; near-coin-flip calls are noise."""
    probs: list[float] = []
    outcomes: list[int] = []
    for i in range(40):  # confident and correct
        probs.append(0.80)
        outcomes.append(1 if i % 10 != 0 else 0)  # 90% right
    for i in range(60):  # unopinionated and random
        probs.append(0.52)
        outcomes.append(i % 2)  # 50% right
    return probs, outcomes


# ---------- grading ----------


def test_zero_margin_covers_everything() -> None:
    p = grade_policy(0.0, [0.9, 0.1, 0.6], [1, 0, 1])
    assert p.coverage == 1.0
    assert p.n_covered == 3
    assert p.brier_covered == pytest.approx(p.brier_all)
    assert not p.abstains


def test_margin_excludes_the_unopinionated_calls() -> None:
    p = grade_policy(0.2, [0.9, 0.52, 0.1], [1, 1, 0])
    assert p.n_covered == 2  # 0.52 is only 0.02 from a coin flip
    assert p.coverage == pytest.approx(2 / 3)


def test_a_margin_nothing_clears_is_reported_not_a_crash() -> None:
    p = grade_policy(0.4, [0.55, 0.45], [1, 0])
    assert p.coverage == 0.0
    assert p.n_covered == 0
    assert p.brier_covered == 1.0


def test_brier_gain_is_positive_when_abstention_helps() -> None:
    probs, outcomes = _confident_edge()
    p = grade_policy(0.2, probs, outcomes)
    assert p.brier_gain > 0
    assert p.accuracy_covered == pytest.approx(0.9)


# ---------- selection ----------


def test_it_finds_the_margin_that_skips_the_noise() -> None:
    probs, outcomes = _confident_edge()
    policy = select_margin(probs, outcomes)
    assert policy.abstains
    assert policy.coverage == pytest.approx(0.4)  # the 40 confident calls
    assert policy.brier_covered < policy.brier_all


def test_no_abstention_when_confidence_carries_no_information() -> None:
    # Confident calls are wrong as often as unopinionated ones — abstaining
    # buys nothing, so the rule should keep speaking.
    probs = [0.9, 0.9, 0.1, 0.1] * 25
    outcomes = [1, 0, 0, 1] * 25
    assert select_margin(probs, outcomes).margin == 0.0


def test_the_coverage_floor_blocks_a_lucky_sliver() -> None:
    # Two perfect, very confident calls surrounded by noise. Without a floor
    # the optimiser would keep only those two and report Brier ~0.
    probs = [0.99, 0.99] + [0.55] * 98
    outcomes = [1, 1] + [i % 2 for i in range(98)]
    policy = select_margin(probs, outcomes)
    assert policy.coverage >= 0.15
    assert policy.n_covered > 2


def test_ties_prefer_more_coverage() -> None:
    # Confident calls (p=0.8, wrong 20% of the time) and unopinionated ones
    # (p=0.6, always right) score an identical 0.16 Brier. Abstaining buys
    # nothing, so the rule should keep speaking.
    probs = [0.8] * 50 + [0.6] * 50
    outcomes = [1] * 40 + [0] * 10 + [1] * 50
    assert grade_policy(0.3, probs, outcomes).brier_covered == pytest.approx(0.16)
    assert select_margin(probs, outcomes).margin == 0.0


def test_selection_never_returns_below_the_floor() -> None:
    probs = [0.5 + 0.001 * i for i in range(100)]
    outcomes = [i % 2 for i in range(100)]
    assert select_margin(probs, outcomes).coverage >= 0.15


# ---------- validation ----------


def test_mismatched_lengths_are_rejected() -> None:
    with pytest.raises(ValidationError):
        grade_policy(0.1, [0.5, 0.6], [1])


def test_empty_input_is_rejected() -> None:
    with pytest.raises(ValidationError):
        select_margin([], [])


def test_negative_margin_is_rejected() -> None:
    with pytest.raises(ValidationError):
        grade_policy(-0.1, [0.5], [1])


def test_absurd_min_coverage_is_rejected() -> None:
    with pytest.raises(ValidationError):
        select_margin([0.5], [1], min_coverage=0)


# ---------- the minimum-gain rule ----------


def test_a_trivial_gain_does_not_buy_silence() -> None:
    """Regression: measured on live EUR/USD, the unconstrained search threw
    away 74% of hours for a ~0.0001 Brier improvement that reversed on the
    test window. Noise must not be able to purchase abstention."""
    # The 0.62 calls are wrong often enough that skipping the 0.52 calls
    # buys nothing at all — the two groups score within 0.002 of each other.
    probs = [0.62] * 30 + [0.52] * 70
    outcomes = [1] * 19 + [0] * 11 + [1] * 70
    tiny = grade_policy(0.10, probs, outcomes)
    assert tiny.coverage == pytest.approx(0.3)  # it would have abstained a lot
    assert abs(tiny.brier_gain) < 0.002  # for no measurable gain
    assert select_margin(probs, outcomes).margin == 0.0  # so it is refused


def test_a_real_gain_still_earns_silence() -> None:
    probs, outcomes = _confident_edge()
    policy = select_margin(probs, outcomes)
    assert policy.abstains
    assert policy.brier_gain >= 0.002


# ---------- the economic criterion (breakeven supplied) ----------


def test_it_abstains_onto_the_profitable_subset() -> None:
    """With a breakeven, abstention skips hours the edge can't pay for. The
    20 confident calls are right 90% of the time (clears a 52% hurdle); the
    80 unopinionated calls are a losing coin flip, dragging the whole set to
    50% — below the hurdle. The rule keeps the former and drops the rest."""
    probs = [0.8] * 20 + [0.52] * 80
    outcomes = [1] * 18 + [0] * 2 + [1] * 32 + [0] * 48  # 90% then 40%
    assert grade_policy(0.0, probs, outcomes).accuracy_covered < 0.52  # whole set fails
    policy = select_margin(probs, outcomes, breakeven=0.52)
    assert policy.abstains
    assert policy.coverage == pytest.approx(0.2)  # the 20 confident calls
    assert policy.accuracy_covered >= 0.52


def test_it_speaks_on_everything_when_the_whole_population_pays() -> None:
    """If the full set already clears breakeven, full coverage wins and the
    model abstains on nothing — margin 0 is a candidate, not just a
    fallback."""
    probs = [0.8] * 100
    outcomes = [1] * 70 + [0] * 30  # 70% overall, well above the hurdle
    policy = select_margin(probs, outcomes, breakeven=0.52)
    assert policy.margin == 0.0
    assert policy.coverage == 1.0


def test_it_prefers_the_loosest_profitable_margin() -> None:
    """Once a subset pays, more opportunities beats fewer. The mild group
    still clears 52%, so the loosest profitable margin keeps confident+mild
    (coverage 0.5) rather than only the surest calls (0.2). The 50 losing
    coin-flips drag the whole set to 48%, so speaking on everything fails."""
    probs = [0.9] * 20 + [0.65] * 30 + [0.52] * 50
    outcomes = [1] * 20 + ([1] * 18 + [0] * 12) + ([1] * 10 + [0] * 40)
    assert grade_policy(0.0, probs, outcomes).accuracy_covered < 0.52  # whole set fails
    policy = select_margin(probs, outcomes, breakeven=0.52)
    assert policy.coverage == pytest.approx(0.5)  # confident + mild, not just confident
    assert policy.accuracy_covered >= 0.52


def test_no_profitable_subset_means_speak_and_let_the_gate_refuse() -> None:
    """The honest failure mode. Nothing clears the hurdle, so rather than
    abstaining down to a hand-picked profitable-looking sliver, the model
    speaks on everything — and the promotion gate refuses it on accuracy."""
    probs = [0.7] * 50 + [0.55] * 50
    outcomes = [i % 2 for i in range(100)]  # ~50% everywhere, no real edge
    policy = select_margin(probs, outcomes, breakeven=0.52)
    assert policy.margin == 0.0
    assert policy.coverage == 1.0


def test_the_economic_rule_can_keep_hours_brier_would_have_dropped() -> None:
    """Why optimising profit rather than Brier matters. On `_confident_edge`
    the whole set is 66% correct — comfortably profitable at a 52% hurdle —
    so the economic rule speaks on everything. The Brier-minimiser instead
    abstains onto the confident block, dropping 60 hours that were paying.
    Different objectives, different answers; only one of them is about
    money."""
    probs, outcomes = _confident_edge()
    econ = select_margin(probs, outcomes, breakeven=0.52)
    brier = select_margin(probs, outcomes)  # legacy objective
    assert econ.coverage > brier.coverage
    assert econ.accuracy_covered >= 0.52
    assert brier.margin > econ.margin


def test_the_coverage_floor_still_binds_under_the_economic_rule() -> None:
    """A profitable but tiny sliver must not win — the same discipline the
    Brier path enforces, because a handful of lucky confident calls clears
    any hurdle."""
    probs = [0.99, 0.99] + [0.5] * 98
    outcomes = [1, 1] + [i % 2 for i in range(98)]
    policy = select_margin(probs, outcomes, breakeven=0.52)
    # Two perfect calls is 2% coverage; below the 15% floor, so refused.
    assert policy.margin == 0.0


def test_an_out_of_range_breakeven_is_rejected() -> None:
    with pytest.raises(ValidationError):
        select_margin([0.6, 0.4], [1, 0], breakeven=1.0)
    with pytest.raises(ValidationError):
        select_margin([0.6, 0.4], [1, 0], breakeven=0.0)
