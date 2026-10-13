"""Every rule family: no peeking ahead, finite memory, and the behaviour it claims."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import Timeframe
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.library import CANDIDATES
from mentor.domain.strategy_lab.rules import (
    DonchianBreakout,
    MaCrossTrend,
    NarrowRangeBreakout,
    RangeReversion,
    SessionBreakout,
    SqueezeBreakout,
    TimeSeriesMomentum,
    TrendPullback,
)
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule
from tests.domain.strategy_lab.fixtures import HOUR, bars, random_walk

_DAILY = random_walk(900, seed=3, vol=0.006)
_HOURLY = random_walk(1500, seed=5, vol=0.0015, step=HOUR, start=datetime(2025, 3, 3, tzinfo=UTC))

_ALL_RULES: list[tuple[str, EntryRule, Timeframe]] = []
for _candidate in CANDIDATES:
    _seen: set[str] = set()
    for _rule, _ in _candidate.grid:
        if repr(_rule) not in _seen:
            _seen.add(repr(_rule))
            _ALL_RULES.append((_candidate.key, _rule, _candidate.timeframe))


def _series_for(tf: Timeframe) -> BarSeries:
    return _HOURLY if tf is Timeframe.H1 else _DAILY


@pytest.mark.parametrize(
    ("key", "rule", "tf"), _ALL_RULES, ids=[f"{k}:{r!r}" for k, r, _ in _ALL_RULES]
)
def test_rule_never_looks_ahead_and_forgets_beyond_lookback(
    key: str, rule: EntryRule, tf: Timeframe
) -> None:
    series = _series_for(tf)
    full = rule.signals(series)
    assert len(full) == len(series)
    lb = rule.lookback
    assert all(s is None for s in full[: lb - 1]), "a signal before the lookback is filled"
    for i in range(lb - 1, len(series), 17):
        assert rule.signals(series.window(0, i + 1))[-1] == full[i], f"{key} peeks ahead at {i}"
        assert rule.signals(series.window(i - lb + 1, i + 1))[-1] == full[i], (
            f"{key} depends on more than its lookback at {i}"
        )


@pytest.mark.parametrize(
    ("key", "rule", "tf"), _ALL_RULES, ids=[f"{k}:{r!r}" for k, r, _ in _ALL_RULES]
)
def test_rule_speaks_on_its_fixture_and_describes_itself(
    key: str, rule: EntryRule, tf: Timeframe
) -> None:
    signals = [s for s in rule.signals(_series_for(tf)) if s is not None]
    assert signals, f"{key} never fired — its tests would prove nothing"
    assert {s.direction for s in signals} <= {Direction.LONG, Direction.SHORT}
    assert len(rule.describe()) > 40


def _closes(values: list[float]) -> BarSeries:
    return bars([(c, c + 0.001, c - 0.001, c) for c in values])


def test_donchian_breakout_direction() -> None:
    rule = DonchianBreakout(channel=3)
    up = rule.signals(_closes([1.0, 1.01, 1.0, 1.05]))
    assert up[3] is not None and up[3].direction is Direction.LONG
    down = rule.signals(_closes([1.0, 1.01, 1.0, 0.95]))
    assert down[3] is not None and down[3].direction is Direction.SHORT
    inside = rule.signals(_closes([1.0, 1.01, 1.0, 1.005]))
    assert inside[3] is None


def test_momentum_follows_the_lookback_change() -> None:
    rule = TimeSeriesMomentum(period=2)
    out = rule.signals(_closes([1.0, 1.1, 1.2, 1.1, 1.0]))
    # 1.1 against 1.1 two bars earlier is no change, so no signal.
    assert [s.direction if s else None for s in out] == [
        None,
        None,
        Direction.LONG,
        None,
        Direction.SHORT,
    ]


def test_pullback_buys_dips_only_in_uptrends() -> None:
    rule = TrendPullback(trend=5, rsi_period=2, rsi_entry=25.0)
    rising_then_dip = [1.00, 1.02, 1.04, 1.06, 1.08, 1.10, 1.12, 1.115, 1.112]
    out = rule.signals(_closes(rising_then_dip))
    assert out[-1] is not None and out[-1].direction is Direction.LONG
    falling_then_dip = [1.20, 1.18, 1.16, 1.14, 1.12, 1.10, 1.08, 1.07, 1.06]
    out = rule.signals(_closes(falling_then_dip))
    assert all(s is None or s.direction is Direction.SHORT for s in out)


def test_range_reversion_targets_the_mean_and_respects_the_trend_filter() -> None:
    choppy = [1.0, 1.01, 1.0, 1.01, 1.0, 1.01, 1.0, 1.01, 0.96]
    rule = RangeReversion(band=8, width=1.5, er_period=6, er_max=0.5)
    sig = rule.signals(_closes(choppy))[-1]
    assert sig is not None and sig.direction is Direction.LONG
    assert sig.target is not None and sig.target > choppy[-1]
    # A steady climb that accelerates: stretched above the band, but trending.
    trending = [1.0, 1.01, 1.02, 1.03, 1.025, 1.05, 1.06, 1.07, 1.12]
    assert rule.signals(_closes(trending))[-1] is None
    lax = RangeReversion(band=8, width=1.5, er_period=6, er_max=0.95)
    faded = lax.signals(_closes(trending))[-1]
    assert faded is not None and faded.direction is Direction.SHORT


def test_squeeze_needs_the_previous_bar_to_be_the_quietest() -> None:
    quiet = [1.0 + 0.02 * ((-1) ** i) * (0.9**i) for i in range(30)]
    rule = SqueezeBreakout(band=5, width=1.0, quiet=10)
    out = rule.signals(_closes([*quiet, 1.1]))
    assert out[-1] is not None and out[-1].direction is Direction.LONG


def test_session_breakout_takes_only_the_first_break_with_a_structural_stop() -> None:
    start = datetime(2025, 3, 3, tzinfo=UTC)  # Monday 00:00 UTC: a full quiet day first
    monday = [(1.10, 1.1005, 1.0995, 1.10)] * 24
    tuesday = [(1.10, 1.1010, 1.0990, 1.10)] * 7  # quiet Asian range 00:00-06:00
    tuesday += [
        (1.10, 1.1030, 1.0995, 1.1025),  # 07:00 closes above the range → long
        (1.1025, 1.1040, 1.0980, 1.0985),  # 08:00 closes below → ignored, day spent
    ]
    series = bars(monday + tuesday, start=start, step=HOUR)
    out = SessionBreakout(range_end_hour=7, session_end_hour=12, min_range_bars=5).signals(series)
    first, second = out[24 + 7], out[24 + 8]
    assert first is not None and first.direction is Direction.LONG
    assert first.stop == pytest.approx(1.0990)
    assert second is None
    assert all(s is None for s in out[:24]), "Monday's quiet session never broke"


def test_narrow_range_break_uses_the_narrow_bar_as_stop() -> None:
    rows = [(1.0, 1.02, 0.98, 1.0)] * 3 + [(1.0, 1.003, 0.998, 1.0), (1.0, 1.01, 0.999, 1.008)]
    out = NarrowRangeBreakout(narrow=4).signals(bars(rows))
    assert out[-1] is not None and out[-1].direction is Direction.LONG
    assert out[-1].stop == pytest.approx(0.998)


def test_ma_cross_and_its_filter() -> None:
    values = [1.0, 0.99, 0.98, 0.97, 0.98, 1.0, 1.03]
    plain = MaCrossTrend(fast=2, slow=4, er_period=3, er_min=0.0).signals(_closes(values))
    crosses = [s for s in plain if s is not None]
    assert crosses and crosses[0].direction is Direction.LONG
    filtered = MaCrossTrend(fast=2, slow=4, er_period=3, er_min=0.99).signals(_closes(values))
    assert len([s for s in filtered if s is not None]) <= len(crosses)


@pytest.mark.parametrize(
    "build",
    [
        lambda: DonchianBreakout(channel=1),
        lambda: TrendPullback(rsi_entry=60.0),
        lambda: RangeReversion(er_max=1.5),
        lambda: SessionBreakout(range_end_hour=12, session_end_hour=8),
        lambda: MaCrossTrend(fast=50, slow=20),
        lambda: SqueezeBreakout(width=0.0),
        lambda: NarrowRangeBreakout(narrow=1),
        lambda: TimeSeriesMomentum(period=1),
    ],
)
def test_nonsense_parameters_are_refused(build: object) -> None:
    assert callable(build)
    with pytest.raises(ValidationError):
        build()
