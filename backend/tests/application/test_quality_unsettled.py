"""Bars the market has not finished printing must be visible, not silent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from mentor.application.market.quality import scan_quality
from mentor.domain.market.bars import Timeframe


def _bar(ts: datetime) -> SimpleNamespace:
    p = Decimal("1.1000")
    return SimpleNamespace(ts=ts, open=p, high=p, low=p, close=p, volume=None, source="yahoo")


def test_a_bar_stamped_in_the_future_is_counted() -> None:
    """Regression: production held a daily bar dated *tomorrow* — Yahoo names
    the in-progress FX session by its close date — and the health page had no
    way to show it. That bar is the newest, so it is what every forecast reads
    as 'now', and its OHLC is still moving."""
    now = datetime.now(UTC)
    report = scan_quality(
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        bars=[
            _bar(now - timedelta(days=2)),
            _bar(now - timedelta(days=1)),
            _bar(now + timedelta(hours=10)),  # tomorrow's session
        ],
    )
    assert report.future_bars == 1
    assert report.has_unsettled_data


def test_the_current_period_is_reported_as_forming_not_future() -> None:
    """An hourly bar opened this hour is legitimate but incomplete — a
    different state from a bar that has not started."""
    now = datetime.now(UTC)
    report = scan_quality(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        bars=[_bar(now - timedelta(hours=3)), _bar(now - timedelta(minutes=10))],
    )
    assert report.future_bars == 0
    assert report.forming_bars == 1
    assert report.has_unsettled_data


def test_settled_history_is_clean() -> None:
    now = datetime.now(UTC)
    report = scan_quality(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        bars=[_bar(now - timedelta(hours=h)) for h in (5, 4, 3, 2)],
    )
    assert report.future_bars == 0
    assert report.forming_bars == 0
    assert not report.has_unsettled_data


def test_gap_detection_still_works() -> None:
    now = datetime.now(UTC)
    report = scan_quality(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        bars=[_bar(now - timedelta(hours=10)), _bar(now - timedelta(hours=5))],
    )
    assert len(report.gaps) == 1
    assert report.gaps[0].missing_bars == 4
