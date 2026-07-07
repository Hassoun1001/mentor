"""Tests for point-in-time news-sentiment features."""

from __future__ import annotations

from datetime import UTC, datetime

from mentor.domain.forecasting.news_features import (
    NEWS_FEATURE_NAMES,
    NewsTonePoint,
    NewsToneSeries,
)


def _day(d: int) -> datetime:
    return datetime(2026, 1, d, tzinfo=UTC)


def test_empty_series_returns_neutral_zeros() -> None:
    series = NewsToneSeries([])
    feats = series.features_asof(_day(10))
    assert set(feats) == set(NEWS_FEATURE_NAMES)
    assert all(v == 0.0 for v in feats.values())


def test_features_are_point_in_time() -> None:
    # Tomorrow's very negative tone must NOT leak into today's features.
    points = [
        NewsTonePoint(day=_day(1), tone=2.0, volume=0.01),
        NewsTonePoint(day=_day(2), tone=-9.0, volume=0.02),  # the future
    ]
    series = NewsToneSeries(points)
    feats = series.features_asof(_day(1))
    # Only day 1 is visible → tone ~ 2.0 / 10
    assert feats["news_tone"] == 0.2
    assert feats["news_tone_5d"] == 0.2


def test_momentum_turns_negative_when_tone_drops() -> None:
    points = [
        NewsTonePoint(day=_day(1), tone=5.0, volume=0.0),
        NewsTonePoint(day=_day(2), tone=5.0, volume=0.0),
        NewsTonePoint(day=_day(3), tone=-5.0, volume=0.0),  # sentiment flips down
    ]
    series = NewsToneSeries(points)
    feats = series.features_asof(_day(3))
    # today (-0.5) is below the 5-day mean → negative momentum
    assert feats["news_tone_mom"] < 0


def test_features_clip_extreme_tone() -> None:
    series = NewsToneSeries([NewsTonePoint(day=_day(1), tone=100.0, volume=0.0)])
    feats = series.features_asof(_day(1))
    assert feats["news_tone"] == 3.0  # clipped to the [-3, 3] envelope
