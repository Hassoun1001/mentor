"""Lab indicators: correct values, and no lookahead or infinite memory — bit for bit."""

from __future__ import annotations

import math

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.strategy_lab import indicators
from tests.domain.strategy_lab.fixtures import random_walk


def test_rolling_mean_and_warmup() -> None:
    assert indicators.rolling_mean([1.0, 2.0, 3.0, 4.0], 2) == [None, 1.5, 2.5, 3.5]


def test_rolling_std_is_population() -> None:
    out = indicators.rolling_std([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0], 8)
    assert out[-1] == pytest.approx(2.0)
    assert out[:-1] == [None] * 7


def test_rolling_extremes() -> None:
    assert indicators.rolling_max([1.0, 3.0, 2.0, 0.5], 2) == [None, 3.0, 3.0, 2.0]
    assert indicators.rolling_min([1.0, 3.0, 2.0, 0.5], 2) == [None, 1.0, 2.0, 0.5]


def test_atr_uses_previous_close_and_needs_period_plus_one() -> None:
    high = [10.0, 11.0, 12.0]
    low = [9.0, 10.0, 8.0]
    close = [9.5, 10.5, 11.0]
    # TR[1] = max(1, |11-9.5|, |10-9.5|) = 1.5 ; TR[2] = max(4, |12-10.5|, |8-10.5|) = 4
    assert indicators.atr(high, low, close, 2) == [None, None, pytest.approx(2.75)]


def test_rsi_extremes_and_midpoint() -> None:
    assert indicators.rsi([1.0, 2.0, 3.0, 4.0], 3)[-1] == 100.0
    assert indicators.rsi([4.0, 3.0, 2.0, 1.0], 3)[-1] == pytest.approx(0.0)
    assert indicators.rsi([1.0, 1.0, 1.0, 1.0], 3)[-1] == 50.0
    # equal gains and losses → 50
    assert indicators.rsi([1.0, 2.0, 1.0], 2)[-1] == pytest.approx(50.0)


def test_efficiency_ratio_trend_vs_range() -> None:
    assert indicators.efficiency_ratio([1.0, 2.0, 3.0, 4.0], 3)[-1] == pytest.approx(1.0)
    assert indicators.efficiency_ratio([1.0, 2.0, 1.0, 2.0, 1.0], 4)[-1] == pytest.approx(0.0)


@pytest.mark.parametrize("bad", [0, -1])
def test_periods_are_validated(bad: int) -> None:
    with pytest.raises(ValidationError):
        indicators.rolling_mean([1.0], bad)


_SERIES = random_walk(400, seed=11)


@pytest.mark.parametrize(
    ("name", "compute", "lookback"),
    [
        ("mean", lambda s: indicators.rolling_mean(s.close, 20), 20),
        ("std", lambda s: indicators.rolling_std(s.close, 20), 20),
        ("max", lambda s: indicators.rolling_max(s.high, 20), 20),
        ("min", lambda s: indicators.rolling_min(s.low, 20), 20),
        ("atr", lambda s: indicators.atr(s.high, s.low, s.close, 14), 15),
        ("rsi", lambda s: indicators.rsi(s.close, 14), 15),
        ("er", lambda s: indicators.efficiency_ratio(s.close, 10), 11),
    ],
)
def test_finite_window_and_no_lookahead(name: str, compute: object, lookback: int) -> None:
    """The value at bar i is identical computed from (a) the whole series,
    (b) the series cut off at i, and (c) only the last ``lookback`` bars."""
    assert callable(compute)
    full = compute(_SERIES)
    for i in range(lookback - 1, len(_SERIES), 37):
        prefix = compute(_SERIES.window(0, i + 1))
        tail = compute(_SERIES.window(i - lookback + 1, i + 1))
        assert prefix[-1] == full[i], name
        assert tail[-1] == full[i], name
        assert full[i] is not None and math.isfinite(full[i])
    assert all(v is None for v in full[: lookback - 1])
