"""Macro-feature tests — point-in-time correctness + neutral fallback."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mentor.domain.forecasting.macro_features import (
    MACRO_FEATURE_NAMES,
    MacroPoint,
    MacroSeries,
)


def _day(i: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=i)


def test_empty_series_is_neutral() -> None:
    series = MacroSeries([])
    feats = series.features_asof(_day(10))
    assert feats == dict.fromkeys(MACRO_FEATURE_NAMES, 0.0)


def test_point_in_time_only_uses_past() -> None:
    # DGS2 rises 4.0 -> 4.5 over 5 days; a future spike must NOT leak in.
    points = [MacroPoint("DGS2", _day(i), 4.0 + i * 0.1) for i in range(6)]
    points.append(MacroPoint("DGS2", _day(20), 9.9))  # far future spike
    series = MacroSeries(points)
    feats = series.features_asof(_day(5))
    # 5-day change = value@day5 (4.5) - value@day0 (4.0) = 0.5
    assert abs(feats["us2y_chg_5"] - 0.5) < 1e-9


def test_spread_level_and_dxy_return_and_vix() -> None:
    points = [
        MacroPoint("T10Y2Y", _day(5), 0.35),
        *[MacroPoint("DTWEXBGS", _day(i), 100.0 + i) for i in range(6)],  # 100..105
        *[MacroPoint("VIXCLS", _day(i), 15.0 + i) for i in range(6)],  # 15..20
    ]
    feats = MacroSeries(points).features_asof(_day(5))
    assert abs(feats["us_2s10s"] - 0.35) < 1e-9
    # dxy_ret_5 = (105 - 100) / 100 = 0.05
    assert abs(feats["dxy_ret_5"] - 0.05) < 1e-9
    # vix_level = 20/100 = 0.20; vix_chg_5 = (20-15)/100 = 0.05
    assert abs(feats["vix_level"] - 0.20) < 1e-9
    assert abs(feats["vix_chg_5"] - 0.05) < 1e-9


def test_missing_series_stays_neutral_but_others_compute() -> None:
    points = [MacroPoint("T10Y2Y", _day(3), 0.5)]
    feats = MacroSeries(points).features_asof(_day(5))
    assert abs(feats["us_2s10s"] - 0.5) < 1e-9
    assert feats["us2y_chg_5"] == 0.0  # no DGS2 -> neutral
    assert feats["dxy_ret_5"] == 0.0


def test_before_any_data_is_neutral() -> None:
    points = [MacroPoint("DGS2", _day(10), 4.0)]
    feats = MacroSeries(points).features_asof(_day(5))  # as-of before the point
    assert feats == dict.fromkeys(MACRO_FEATURE_NAMES, 0.0)
