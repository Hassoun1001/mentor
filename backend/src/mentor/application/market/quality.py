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
from datetime import UTC, datetime

from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.models import PriceBar as PriceBarORM


@dataclass(frozen=True, slots=True)
class GapWindow:
    expected_after: datetime
    next_seen: datetime
    missing_bars: int


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
