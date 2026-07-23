"""Significance: small samples must not be allowed to look convincing."""

from __future__ import annotations

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.stats.significance import (
    assess_expectancy,
    assess_proportion,
    trades_needed,
    wilson_interval,
)

# ---------- Wilson interval ----------


def test_interval_stays_inside_zero_and_one_at_the_extremes() -> None:
    # The normal approximation would go negative here; Wilson must not.
    low, high = wilson_interval(0, 10)
    assert low == 0.0
    assert 0 < high < 1

    low, high = wilson_interval(10, 10)
    assert high == pytest.approx(1.0)
    assert 0 < low < 1


def test_the_interval_narrows_as_the_sample_grows() -> None:
    small = wilson_interval(30, 50)
    large = wilson_interval(600, 1000)
    assert (small[1] - small[0]) > (large[1] - large[0])


def test_interval_brackets_the_observed_rate() -> None:
    low, high = wilson_interval(55, 100)
    assert low < 0.55 < high


def test_bad_inputs_are_rejected() -> None:
    with pytest.raises(ValidationError):
        wilson_interval(5, 0)
    with pytest.raises(ValidationError):
        wilson_interval(11, 10)


# ---------- sample size ----------


def test_a_thin_edge_needs_a_brutal_sample() -> None:
    # 53% vs a coin flip — the honest headline number for this system.
    n = trades_needed(0.53)
    assert n is not None
    assert 1_000 <= n <= 1_200


def test_a_fat_edge_needs_far_fewer() -> None:
    thin = trades_needed(0.53)
    fat = trades_needed(0.70)
    assert thin is not None and fat is not None
    assert fat < thin / 10


def test_no_effect_means_no_sample_size_resolves_it() -> None:
    assert trades_needed(0.5) is None


def test_direction_of_the_effect_does_not_change_the_sample_needed() -> None:
    assert trades_needed(0.55) == trades_needed(0.45)


# ---------- proportion verdict ----------


def test_a_convincing_looking_small_sample_is_called_out() -> None:
    # 24 of 40 is 60% — feels like proof, establishes nothing.
    v = assess_proportion(24, 40)
    assert v.observed == 0.6
    assert not v.significant
    assert v.low < 0.5 < v.high
    assert "not yet distinguishable" in v.verdict
    assert v.n_needed is not None


def test_a_genuine_edge_on_a_real_sample_is_recognised() -> None:
    v = assess_proportion(600, 1000)
    assert v.significant
    assert v.low > 0.5
    assert "edge is real" in v.verdict


def test_significantly_worse_than_chance_is_reported_as_a_finding() -> None:
    v = assess_proportion(380, 1000)  # 38%
    assert v.significant
    assert v.worse_than_baseline
    assert "worse" in v.verdict


def test_an_empty_sample_says_so_rather_than_dividing_by_zero() -> None:
    v = assess_proportion(0, 0)
    assert v.n == 0
    assert not v.significant
    assert "nothing to measure" in v.verdict


def test_a_non_coin_flip_baseline_is_honoured() -> None:
    # 60% is a great direction call but a poor result against a 70% baseline.
    v = assess_proportion(60, 100, baseline=0.7)
    assert v.baseline == 0.7
    assert v.worse_than_baseline


def test_invalid_baseline_is_rejected() -> None:
    with pytest.raises(ValidationError):
        assess_proportion(5, 10, baseline=0.0)


# ---------- expectancy verdict ----------


def test_a_positive_average_on_a_noisy_small_sample_is_not_significant() -> None:
    values = [2.0, -1.0, -1.0, 3.0, -1.0, -1.0, 2.0, -1.0]  # +0.25R average
    v = assess_expectancy(values)
    assert v.mean == pytest.approx(0.25)
    assert not v.significant
    assert v.low < 0 < v.high
    assert "straddles zero" in v.verdict


def test_a_consistent_edge_over_many_trades_clears_zero() -> None:
    values = [1.0, -0.5] * 200  # +0.25R, low variance, large n
    v = assess_expectancy(values)
    assert v.significant
    assert v.low > 0
    assert "entirely above zero" in v.verdict


def test_a_losing_system_is_named_as_one() -> None:
    values = [-1.0, 0.5] * 200  # -0.25R
    v = assess_expectancy(values)
    assert v.significant
    assert "losing system" in v.verdict


def test_one_trade_is_refused_rather_than_extrapolated() -> None:
    v = assess_expectancy([3.0])
    assert v.n == 1
    assert not v.significant
    assert "far too few" in v.verdict


def test_no_trades_does_not_crash() -> None:
    v = assess_expectancy([])
    assert v.n == 0
    assert not v.significant


def test_identical_returns_are_flagged_as_unrealistic() -> None:
    v = assess_expectancy([1.0] * 50)
    assert v.stdev == 0.0
    assert "not a realistic sample" in v.verdict


# ---------- the small-sample floor ----------


def test_a_perfect_short_run_is_not_called_an_edge() -> None:
    """Regression: five correct out of five gives a Wilson lower bound near
    57%, which excludes a coin flip — so it was reported as a real edge. Five
    heads in a row happens by chance one time in thirty-two. Production hit
    exactly this once overlapping signals were collapsed to five disjoint
    windows."""
    v = assess_proportion(5, 5, label="windows")
    assert v.low > 0.5  # the interval really does exclude a coin flip
    assert not v.significant  # and it is still refused
    assert "looks decisive and is not" in v.verdict


def test_the_floor_does_not_suppress_a_real_result() -> None:
    v = assess_proportion(600, 1000)
    assert v.significant


def test_expectancy_honours_the_same_floor() -> None:
    values = [1.0, -0.5] * 5  # only 10 trades, tight spread
    v = assess_expectancy(values)
    assert not v.significant
