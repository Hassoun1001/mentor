"""Macro-feature tests — point-in-time correctness + neutral fallback."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mentor.domain.forecasting.macro_features import (
    COT_EUR_SERIES_ID,
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


# ---------- COT positioning ----------


def test_cot_level_and_week_over_week_change() -> None:
    # Two weekly observations: net position eases from -0.06 to -0.05 of OI.
    points = [
        MacroPoint(COT_EUR_SERIES_ID, _day(0), -0.06),
        MacroPoint(COT_EUR_SERIES_ID, _day(7), -0.05),
    ]
    feats = MacroSeries(points).features_asof(_day(8))
    assert abs(feats["cot_net_pct_oi"] - (-0.05)) < 1e-9  # latest level
    assert abs(feats["cot_net_chg"] - 0.01) < 1e-9  # -0.05 - (-0.06)


def test_cot_is_neutral_before_its_publication_date() -> None:
    # The whole point of COT: the value is dated at *publication*, so a bar
    # before that date must not see it — the classic COT lookahead trap.
    points = [MacroPoint(COT_EUR_SERIES_ID, _day(10), -0.05)]
    feats = MacroSeries(points).features_asof(_day(9))  # day before publication
    assert feats["cot_net_pct_oi"] == 0.0
    assert feats["cot_net_chg"] == 0.0


def test_cot_visible_on_and_after_publication() -> None:
    points = [MacroPoint(COT_EUR_SERIES_ID, _day(10), -0.05)]
    on_day = MacroSeries(points).features_asof(_day(10))
    assert abs(on_day["cot_net_pct_oi"] - (-0.05)) < 1e-9


def test_cot_carries_forward_between_weekly_reports() -> None:
    # A daily bar three days after the weekly report still sees that week's
    # value (most-recent-visible), with no change until the next report.
    points = [MacroPoint(COT_EUR_SERIES_ID, _day(0), 0.08)]
    feats = MacroSeries(points).features_asof(_day(3))
    assert abs(feats["cot_net_pct_oi"] - 0.08) < 1e-9
    assert feats["cot_net_chg"] == 0.0  # only one observation -> no prior week
