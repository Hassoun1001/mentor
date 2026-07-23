"""Higher-timeframe features: point-in-time safety above all else."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.forecasting.htf_features import (
    HTF_FEATURE_NAMES,
    HtfSeries,
    build_htf_by_ts,
    neutral_htf_features,
)
from mentor.domain.market.bars import PriceBar, Timeframe


def _daily(n: int = 80, *, rising: bool = True) -> list[PriceBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    out: list[PriceBar] = []
    for i in range(n):
        px = 1.10 + (0.002 * i if rising else -0.002 * i)
        p = Decimal(f"{px:.5f}")
        out.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.D1,
                ts=start + timedelta(days=i),
                open=p,
                high=p + Decimal("0.0020"),
                low=p - Decimal("0.0020"),
                close=p,
                volume=Decimal("100"),
                source="test",
            )
        )
    return out


# ---- the lookahead guarantee -------------------------------------------


def test_same_day_bar_is_invisible_until_it_closes() -> None:
    """An hourly bar mid-day must NOT see that day's unfinished daily bar."""
    bars = _daily()
    series = HtfSeries(bars)
    last = bars[-1]  # stamped 00:00 on its day, closes 24h later

    # Mid-way through the final daily bar's period: it must be excluded.
    midday = last.ts + timedelta(hours=9)
    visible_midday = series._visible(midday)
    assert last not in visible_midday
    assert len(visible_midday) == len(bars) - 1

    # Exactly at its close, it becomes visible.
    at_close = last.ts + timedelta(days=1)
    assert last in series._visible(at_close)


def test_features_do_not_change_within_the_unfinished_day() -> None:
    """Every hour inside one daily period sees identical HTF context —
    proof no intraday leak of the forming daily bar."""
    series = HtfSeries(_daily())
    day = datetime(2026, 3, 1, tzinfo=UTC)
    hourly = [day + timedelta(hours=h) for h in range(1, 24)]
    feats = [series.features_asof(ts) for ts in hourly]
    assert all(f == feats[0] for f in feats)


def test_future_bars_never_leak() -> None:
    """Truncating history after the as-of time must not change the answer."""
    bars = _daily()
    asof = datetime(2026, 2, 15, tzinfo=UTC)
    full = HtfSeries(bars).features_asof(asof)
    truncated = HtfSeries([b for b in bars if b.ts < asof]).features_asof(asof)
    assert full == truncated


# ---- feature sanity -----------------------------------------------------


def test_neutral_when_history_too_short() -> None:
    series = HtfSeries(_daily(10))
    feats = series.features_asof(datetime(2026, 6, 1, tzinfo=UTC))
    assert feats == neutral_htf_features()


def test_uptrend_reads_bullish_and_downtrend_bearish() -> None:
    asof = datetime(2026, 6, 1, tzinfo=UTC)
    up = HtfSeries(_daily(rising=True)).features_asof(asof)
    down = HtfSeries(_daily(rising=False)).features_asof(asof)
    # Price above its slow EMA and fast above slow in an uptrend; inverted down.
    assert up["htf_trend_dist"] > 0 > down["htf_trend_dist"]
    assert up["htf_ema_spread"] > 0 > down["htf_ema_spread"]
    # Momentum and range position agree with direction.
    assert up["htf_rsi"] > down["htf_rsi"]
    assert up["htf_range_pos"] > down["htf_range_pos"]


def test_all_features_present_and_finite() -> None:
    feats = HtfSeries(_daily()).features_asof(datetime(2026, 6, 1, tzinfo=UTC))
    assert set(feats) == set(HTF_FEATURE_NAMES)
    assert all(math.isfinite(v) for v in feats.values())


def test_build_by_ts_maps_every_timestamp() -> None:
    series = HtfSeries(_daily())
    stamps = [datetime(2026, 3, 1, tzinfo=UTC) + timedelta(hours=h) for h in range(5)]
    mapped = build_htf_by_ts(series, stamps)
    assert set(mapped) == set(stamps)
    assert all(set(v) == set(HTF_FEATURE_NAMES) for v in mapped.values())


def test_empty_series_is_neutral_everywhere() -> None:
    series = HtfSeries([])
    assert series.empty
    assert series.features_asof(datetime(2026, 6, 1, tzinfo=UTC)) == neutral_htf_features()
