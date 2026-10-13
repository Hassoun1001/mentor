"""A compact, read-only bar series for the strategy lab.

The lab simulates every parameter set of every candidate over years of
bars, so it works on plain floats rather than the ``Decimal`` the trade
journal and the classic backtester use. That is safe here because nothing
in the lab is money: every result is an R-multiple, a ratio of two price
distances, and costs are charged in price units before the ratio is taken.

The series is built once from domain ``PriceBar`` objects and never
mutated. ``window`` returns a new series over a slice, which is how the
live paper trader computes signals from recent history only — the reason
every lab indicator has a finite lookback (see ``indicators.py``).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar


@dataclass(frozen=True, slots=True)
class BarSeries:
    ts: tuple[datetime, ...]
    open: tuple[float, ...]
    high: tuple[float, ...]
    low: tuple[float, ...]
    close: tuple[float, ...]

    def __post_init__(self) -> None:
        n = len(self.ts)
        if any(len(col) != n for col in (self.open, self.high, self.low, self.close)):
            raise ValidationError("bar series columns must have equal length")
        if any(self.ts[i] >= self.ts[i + 1] for i in range(n - 1)):
            raise ValidationError("bar series must be strictly chronological")

    @classmethod
    def from_bars(cls, bars: Sequence[PriceBar]) -> BarSeries:
        return cls(
            ts=tuple(b.ts for b in bars),
            open=tuple(float(b.open) for b in bars),
            high=tuple(float(b.high) for b in bars),
            low=tuple(float(b.low) for b in bars),
            close=tuple(float(b.close) for b in bars),
        )

    def __len__(self) -> int:
        return len(self.ts)

    def window(self, start: int, end: int | None = None) -> BarSeries:
        """The bars ``[start, end)`` as their own series."""
        stop = len(self) if end is None else end
        return BarSeries(
            ts=self.ts[start:stop],
            open=self.open[start:stop],
            high=self.high[start:stop],
            low=self.low[start:stop],
            close=self.close[start:stop],
        )

    def index_at_or_after(self, when: datetime) -> int:
        """First index whose bar starts at or after ``when`` (``len`` if none)."""
        lo, hi = 0, len(self.ts)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.ts[mid] < when:
                lo = mid + 1
            else:
                hi = mid
        return lo
