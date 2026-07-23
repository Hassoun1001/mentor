"""Data-quality monitoring — detect gaps, duplicate ticks, stale feeds.

> Detects gaps, bad ticks, and stale feeds, and flags them rather than
> silently corrupting models.   — Mentor product plan, §6.B

Models are only as honest as the bars they were trained on. A silent
two-hour gap during a CPI release will quietly poison every backtest
that crosses it. This scanner runs over a window and returns a report
the UI can surface.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.models import PriceBar as PriceBarORM

# FX trades continuously from Sunday evening to Friday evening, so every
# weekend leaves a hole the scanner used to report as missing data. On the
# daily series that was 57 of 59 "gaps" — a page telling the user their feed
# was full of holes when it was simply the weekend. The window is padded
# either side to absorb DST shifts and broker-to-broker variation.
_MARKET_CLOSES_FRIDAY_HOUR = 20
_MARKET_OPENS_SUNDAY_HOUR = 23


def _is_market_closed(ts: datetime) -> bool:
    """True when FX is shut at this instant.

    The week runs Sunday evening to Friday evening. Padding either side of
    the exact open/close absorbs DST shifts and broker variation.
    """
    friday, saturday, sunday = 4, 5, 6
    weekday = ts.weekday()
    if weekday == saturday:
        return True
    if weekday == friday:
        return ts.hour >= _MARKET_CLOSES_FRIDAY_HOUR
    if weekday == sunday:
        return ts.hour < _MARKET_OPENS_SUNDAY_HOUR
    return False


def _is_weekend_closure(start: datetime, end: datetime, step_seconds: int) -> bool:
    """True when every bar missing between two prints falls in the shutdown.

    Checking the missing timestamps rather than the endpoints is what makes
    this work across timeframes: a daily bar is stamped at midnight, so a
    Friday-to-Monday hole has its Friday endpoint at 00:00 — nowhere near
    the Friday-evening close — while the bars actually absent are Saturday
    and Sunday.
    """
    if (end - start).days > 3:
        return False  # a real outage can also start on a Friday
    missing: list[datetime] = []
    cursor = start + timedelta(seconds=step_seconds)
    while cursor < end and len(missing) <= 200:
        missing.append(cursor)
        cursor += timedelta(seconds=step_seconds)
    return bool(missing) and all(_is_market_closed(ts) for ts in missing)


@dataclass(frozen=True, slots=True)
class GapWindow:
    expected_after: datetime
    next_seen: datetime
    missing_bars: int
    # Expected market closure rather than lost data. Reported either way so
    # the count is auditable, but only unexplained gaps should alarm anyone.
    weekend_closure: bool = False


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    symbol: str
    timeframe: Timeframe
    bars_scanned: int
    gaps: tuple[GapWindow, ...]
    duplicate_count: int  # should always be 0 thanks to PK
    last_seen_at: datetime | None
    # Bars whose period has not elapsed yet. Their OHLC is still moving, so
    # treating one as a completed bar means training on settled data and
    # predicting from an unsettled one. Production held a daily bar stamped
    # *tomorrow* — Yahoo labels the in-progress FX session by its close date
    # — and nothing noticed, because this scanner only looked for gaps and
    # duplicates.
    forming_bars: int = 0
    # Bars whose period has not even started. No labelling convention makes
    # this correct; it is bad data.
    future_bars: int = 0

    @property
    def has_unsettled_data(self) -> bool:
        return self.forming_bars > 0 or self.future_bars > 0

    @property
    def unexplained_gaps(self) -> tuple[GapWindow, ...]:
        """Gaps that a closed market does not account for — the ones that matter."""
        return tuple(g for g in self.gaps if not g.weekend_closure)


def scan_quality(
    *, symbol: str, timeframe: Timeframe, bars: Sequence[PriceBarORM]
) -> DataQualityReport:
    if not bars:
        return DataQualityReport(
            symbol=symbol,
            timeframe=timeframe,
            bars_scanned=0,
            gaps=(),
            duplicate_count=0,
            last_seen_at=None,
        )

    now = datetime.now(UTC)
    forming = 0
    future = 0
    for bar in bars:
        if bar.ts > now:
            future += 1
        elif bar.ts.timestamp() + timeframe.seconds > now.timestamp():
            forming += 1

    expected_step_seconds = timeframe.seconds
    gaps: list[GapWindow] = []
    seen: set[datetime] = set()
    duplicates = 0

    previous_ts: datetime | None = None
    for bar in bars:
        if bar.ts in seen:
            duplicates += 1
            continue
        seen.add(bar.ts)
        if previous_ts is not None:
            delta = (bar.ts - previous_ts).total_seconds()
            steps = int(delta // expected_step_seconds)
            if steps > 1:
                gaps.append(
                    GapWindow(
                        expected_after=previous_ts,
                        next_seen=bar.ts,
                        missing_bars=steps - 1,
                        weekend_closure=_is_weekend_closure(
                            previous_ts, bar.ts, expected_step_seconds
                        ),
                    )
                )
        previous_ts = bar.ts

    return DataQualityReport(
        symbol=symbol,
        timeframe=timeframe,
        bars_scanned=len(bars),
        forming_bars=forming,
        future_bars=future,
        gaps=tuple(gaps),
        duplicate_count=duplicates,
        last_seen_at=previous_ts,
    )
