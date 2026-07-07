"""Input hygiene — refuse to predict on bars that look broken.

A model fed a corrupted window produces confident garbage. Before the
loop predicts, the recent bars are scanned (gaps via `scan_quality`) and
the prediction is *skipped* — loudly, with a reason — when the window
looks unhealthy:

- an **intraweek gap** (one that doesn't span the FX weekend close) of
  `max_gap_bars` or more inside the recent window, or
- a **stale feed**: the newest bar is much older than one timeframe step
  while the FX market is actually open.

FX-aware on purpose: the market closes Friday ~22:00 UTC and reopens
Sunday ~22:00 UTC, so a ~48-bar hourly gap every weekend is *normal* and
must not trip the gate.

Pure functions over a `DataQualityReport` — unit-testable without a DB.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mentor.application.market.quality import DataQualityReport

# FX weekly close/open (UTC hours).
_FRIDAY = 4
_SATURDAY = 5
_SUNDAY = 6
_CLOSE_OPEN_HOUR_UTC = 22


@dataclass(frozen=True, slots=True)
class QualityVerdict:
    predict_ok: bool
    reason: str


def fx_market_open(now: datetime) -> bool:
    """True when the FX market is normally trading at `now` (UTC)."""
    ts = now.astimezone(UTC)
    if ts.weekday() == _SATURDAY:
        return False
    if ts.weekday() == _FRIDAY and ts.hour >= _CLOSE_OPEN_HOUR_UTC:
        return False
    return not (ts.weekday() == _SUNDAY and ts.hour < _CLOSE_OPEN_HOUR_UTC)


def _spans_weekend(start: datetime, end: datetime) -> bool:
    """Does [start, end] cross the Friday-close → Sunday-open window?"""
    cursor = start.astimezone(UTC)
    end = end.astimezone(UTC)
    while cursor <= end:
        if not fx_market_open(cursor):
            return True
        cursor += timedelta(hours=1)
    return False


def assess_quality(
    report: DataQualityReport,
    *,
    now: datetime,
    max_gap_bars: int = 8,
    stale_after_steps: int = 6,
) -> QualityVerdict:
    """Decide whether the recent window is healthy enough to predict on."""
    if report.bars_scanned == 0:
        return QualityVerdict(predict_ok=False, reason="no bars in the recent window")

    for gap in report.gaps:
        if gap.missing_bars >= max_gap_bars and not _spans_weekend(
            gap.expected_after, gap.next_seen
        ):
            return QualityVerdict(
                predict_ok=False,
                reason=(
                    f"intraweek gap of {gap.missing_bars} bars after "
                    f"{gap.expected_after.isoformat()} — feed hole, not a weekend"
                ),
            )

    if report.last_seen_at is not None and fx_market_open(now):
        age = now - report.last_seen_at
        limit = timedelta(seconds=report.timeframe.seconds * stale_after_steps)
        # A fresh Sunday reopen legitimately follows a ~48h-old bar; only
        # flag staleness when the whole gap since the last bar was tradable.
        if age > limit and not _spans_weekend(report.last_seen_at, now):
            return QualityVerdict(
                predict_ok=False,
                reason=(
                    f"stale feed: newest bar is {age} old "
                    f"(> {stale_after_steps} steps) while the market is open"
                ),
            )

    return QualityVerdict(predict_ok=True, reason="window healthy")
