"""Cross-source price comparison — do two feeds agree?

> More data online / to compare it.

Pulls the same symbol+range from two independent adapters, aligns the
bars by timestamp, and reports how far their closes diverge. Two honest
feeds of a liquid pair like EUR/USD should agree to a few pips; a large
or systematic gap means one source is stale, mis-scaled, or quoting a
different fixing — which would silently poison any model trained on it.
This is the §6.B "flag it rather than silently corrupt models" rule
applied across providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import Timeframe


@dataclass(frozen=True, slots=True)
class CrossSourceReport:
    symbol: str
    timeframe: Timeframe
    source_a: str
    source_b: str
    bars_a: int
    bars_b: int
    overlapping: int
    max_abs_diff: Decimal  # largest |close_a - close_b| over the overlap
    mean_abs_diff: Decimal
    max_diff_at: datetime | None
    agree: bool  # within tolerance everywhere they overlap


async def _collect(
    adapter: MarketDataAdapter,
    *,
    symbol: str,
    timeframe: Timeframe,
    start: datetime,
    end: datetime,
) -> dict[datetime, Decimal]:
    return {
        bar.ts: bar.close
        async for bar in adapter.fetch_bars(
            symbol=symbol, timeframe=timeframe, start=start, end=end
        )
    }


async def compare_sources(
    *,
    primary: MarketDataAdapter,
    secondary: MarketDataAdapter,
    symbol: str,
    timeframe: Timeframe,
    start: datetime,
    end: datetime,
    tolerance: Decimal = Decimal("0.002"),  # ~20 pips on EUR/USD
) -> CrossSourceReport:
    a = await _collect(primary, symbol=symbol, timeframe=timeframe, start=start, end=end)
    b = await _collect(secondary, symbol=symbol, timeframe=timeframe, start=start, end=end)

    common = sorted(set(a) & set(b))
    max_diff = Decimal("0")
    max_at: datetime | None = None
    total = Decimal("0")
    for ts in common:
        diff = abs(a[ts] - b[ts])
        total += diff
        if diff > max_diff:
            max_diff = diff
            max_at = ts

    mean_diff = (total / Decimal(len(common))) if common else Decimal("0")
    return CrossSourceReport(
        symbol=symbol.upper(),
        timeframe=timeframe,
        source_a=primary.name,
        source_b=secondary.name,
        bars_a=len(a),
        bars_b=len(b),
        overlapping=len(common),
        max_abs_diff=max_diff,
        mean_abs_diff=mean_diff,
        max_diff_at=max_at,
        agree=bool(common) and max_diff <= tolerance,
    )
