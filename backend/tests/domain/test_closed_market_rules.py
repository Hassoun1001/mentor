"""Closed-market rules: what is stored, what a label means, when FRED is visible."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from mentor.application.forecasting.resolver import MAX_RESOLUTION_LAG
from mentor.domain.forecasting import labels as labels_module
from mentor.domain.forecasting.labels import build_labels
from mentor.domain.forecasting.macro_features import MacroPoint, MacroSeries, _fred_visible_from
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.hours import fx_market_open
from mentor.domain.market.settlement import in_market_hours, screen

_HOUR = 3600


def _bar(ts: datetime, tf: Timeframe = Timeframe.H1) -> PriceBar:
    p = Decimal("1.1")
    return PriceBar(
        symbol="EURUSD",
        timeframe=tf,
        ts=ts,
        open=p,
        high=p,
        low=p,
        close=p,
        volume=None,
        source="test",
    )


def test_friday_close_follows_new_york_in_summer_and_winter() -> None:
    assert fx_market_open(datetime(2026, 10, 30, 20, 59, tzinfo=UTC)) is True
    assert fx_market_open(datetime(2026, 10, 30, 21, 0, tzinfo=UTC)) is False  # EDT
    assert fx_market_open(datetime(2026, 11, 6, 21, 59, tzinfo=UTC)) is True
    assert fx_market_open(datetime(2026, 11, 6, 22, 0, tzinfo=UTC)) is False  # EST


def test_sunday_open_follows_new_york_in_summer_and_winter() -> None:
    assert fx_market_open(datetime(2026, 10, 25, 20, 59, tzinfo=UTC)) is False
    assert fx_market_open(datetime(2026, 10, 25, 21, 0, tzinfo=UTC)) is True  # EDT
    assert fx_market_open(datetime(2026, 11, 8, 21, 59, tzinfo=UTC)) is False
    assert fx_market_open(datetime(2026, 11, 8, 22, 0, tzinfo=UTC)) is True  # EST


def test_a_daily_bar_is_judged_by_its_day() -> None:
    assert in_market_hours(datetime(2026, 11, 6, tzinfo=UTC), Timeframe.D1) is True
    assert in_market_hours(datetime(2026, 11, 7, tzinfo=UTC), Timeframe.D1) is False
    assert in_market_hours(datetime(2026, 11, 8, tzinfo=UTC), Timeframe.D1) is False


def test_screen_never_keeps_a_closed_market_bar() -> None:
    open_bar = _bar(datetime(2026, 11, 6, 12, tzinfo=UTC))
    saturday = _bar(datetime(2026, 11, 7, 12, tzinfo=UTC))
    daily_sat = _bar(datetime(2026, 11, 7, tzinfo=UTC), Timeframe.D1)
    result = screen([open_bar, saturday, daily_sat], now=datetime(2026, 11, 9, tzinfo=UTC))
    assert result.settled == (open_bar,)
    assert result.closed == 2


def test_label_limit_matches_the_resolver() -> None:
    assert labels_module._MAX_OUTCOME_LAG == MAX_RESOLUTION_LAG


def test_label_on_regular_hours_is_the_bar_at_the_horizon() -> None:
    start = datetime(2026, 11, 2, tzinfo=UTC)
    ts = [start + timedelta(hours=i) for i in range(4)]
    closes = [Decimal(x) for x in ("1.0", "2.0", "0.5", "3.0")]
    assert build_labels(closes, timestamps=ts, horizon_bars=2, bar_seconds=_HOUR) == [
        (ts[0], 0),
        (ts[1], 1),
    ]


def test_label_across_the_weekend_uses_the_first_bar_after_the_reopen() -> None:
    friday = datetime(2026, 11, 6, 12, tzinfo=UTC)
    reopen = datetime(2026, 11, 8, 22, tzinfo=UTC)
    monday = datetime(2026, 11, 9, 12, tzinfo=UTC)
    closes = [Decimal("1.1"), Decimal("1.2"), Decimal("1.0")]
    labels = build_labels(
        closes, timestamps=[friday, reopen, monday], horizon_bars=24, bar_seconds=_HOUR
    )
    assert labels[0] == (friday, 1)  # graded on the reopen, not 24 bars later


def test_label_is_dropped_when_the_outcome_has_not_happened() -> None:
    start = datetime(2026, 11, 2, tzinfo=UTC)
    ts = [start, start + timedelta(hours=1)]
    closes = [Decimal(1), Decimal(2)]
    assert build_labels(closes, timestamps=ts, horizon_bars=5, bar_seconds=_HOUR) == []


def test_label_is_dropped_past_the_lag_limit() -> None:
    a = datetime(2026, 11, 2, tzinfo=UTC)
    b = a + timedelta(days=9)
    closes = [Decimal(1), Decimal(2)]
    assert build_labels(closes, timestamps=[a, b], horizon_bars=1, bar_seconds=_HOUR) == []


def test_daily_fred_row_is_visible_the_day_after_its_release() -> None:
    assert _fred_visible_from("DGS2", date(2026, 11, 4)) == date(2026, 11, 6)  # Wed
    assert _fred_visible_from("DGS2", date(2026, 11, 6)) == date(2026, 11, 10)  # Fri, posted Mon


def test_dollar_index_waits_for_the_weekly_release() -> None:
    assert _fred_visible_from("DTWEXBGS", date(2026, 11, 2)) == date(2026, 11, 10)  # Mon
    assert _fred_visible_from("DTWEXBGS", date(2026, 11, 6)) == date(2026, 11, 10)  # Fri


def test_a_bar_cannot_see_that_days_yield() -> None:
    day = datetime(2026, 11, 4, tzinfo=UTC)
    points = [
        MacroPoint("VIXCLS", day - timedelta(days=2), 20.0),
        MacroPoint("VIXCLS", day, 40.0),
    ]
    series = MacroSeries(points)
    assert series.features_asof(day.replace(hour=8))["vix_level"] == 0.2
    assert series.features_asof(day + timedelta(days=2))["vix_level"] == 0.4
