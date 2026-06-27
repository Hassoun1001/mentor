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
from datetime import datetime

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
        gaps=tuple(gaps),
        duplicate_count=duplicates,
        last_seen_at=previous_ts,
    )
