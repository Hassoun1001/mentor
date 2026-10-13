"""The multiple-testing correction: more tries, higher bar; noise does not pass."""

from __future__ import annotations

import math
import random

import pytest

from mentor.domain.stats.significance import _Z
from mentor.domain.strategy_lab.deflation import (
    deflate,
    deflated_bar,
    expected_max_z,
    trade_stats,
    trial_dispersion,
)


def test_one_trial_needs_only_the_usual_95_percent() -> None:
    assert expected_max_z(1) == 0.0
    assert deflated_bar(1) == pytest.approx(_Z)


def test_the_bar_rises_with_every_trial() -> None:
    bars = [deflated_bar(n) for n in (2, 10, 74, 500, 5000)]
    assert bars == sorted(bars)
    assert expected_max_z(74) == pytest.approx(2.4, abs=0.15)
    assert expected_max_z(500) == pytest.approx(3.0, abs=0.15)


def test_dispersion_can_raise_the_bar_but_never_lower_it() -> None:
    assert trial_dispersion([0.1, 0.1, 0.1]) == 1.0
    assert trial_dispersion([]) == 1.0
    assert trial_dispersion([-3.0, 0.0, 3.0]) == pytest.approx(9.0)
    assert deflated_bar(74, 9.0) > deflated_bar(74, 1.0) == deflated_bar(74, 0.2)


def test_trade_stats_basics() -> None:
    s = trade_stats([2.0, -1.0, 2.0, -1.0])
    assert s.n == 4 and s.mean == pytest.approx(0.5)
    assert s.win_rate == pytest.approx(0.5)
    assert s.breakeven_win_rate == pytest.approx(1 / 3)
    assert s.t_stat == pytest.approx(s.sharpe * 2)


def test_non_normal_returns_only_ever_penalise() -> None:
    rng = random.Random(1)
    skewed = [5.0 if rng.random() < 0.2 else -0.8 for _ in range(200)]
    s = trade_stats(skewed)
    assert s.skew > 1
    assert s.t_adjusted <= s.sharpe * math.sqrt(s.n - 1) + 1e-12


def test_tiny_and_degenerate_samples_are_inert() -> None:
    assert trade_stats([]).t_adjusted == 0.0
    assert trade_stats([1.0]).t_adjusted == 0.0
    assert trade_stats([1.0, 1.0, 1.0]).t_adjusted == 0.0
    assert not deflate(trade_stats([1.0]), n_trials=1).passed


def test_a_losing_record_never_passes_however_strong() -> None:
    assert not deflate(trade_stats([-1.0, -0.9] * 50), n_trials=1).passed


def test_a_strong_record_passes_few_trials_and_fails_many() -> None:
    rng = random.Random(4)
    rs = [rng.gauss(0.35, 1.0) for _ in range(120)]
    s = trade_stats(rs)
    assert deflate(s, n_trials=1).passed
    assert not deflate(s, n_trials=10**6, dispersion=4.0).passed


def test_the_best_of_many_noise_strategies_rarely_passes() -> None:
    """Pick the best of 50 pure-noise 'strategies' 200 times over: the
    deflated bar must reject the winner nearly always (≤ 5%), where a
    naive 95% test would be fooled most of the time."""
    rng = random.Random(2026)
    fooled_naive = fooled_deflated = 0
    rounds, trials = 200, 50
    for _ in range(rounds):
        best = max(
            (trade_stats([rng.gauss(0.0, 1.0) for _ in range(60)]) for _ in range(trials)),
            key=lambda s: s.t_adjusted,
        )
        fooled_naive += best.t_adjusted >= _Z
        fooled_deflated += deflate(best, n_trials=trials).passed
    assert fooled_naive / rounds > 0.5
    assert fooled_deflated / rounds <= 0.05
