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
