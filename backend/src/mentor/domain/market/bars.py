"""Price-bar value object and timeframe enum.

Timeframes are restricted to the set the plan calls out (`1m / 5m / 1h /
1d`). Adding a new one is a one-line addition; calling code is forced to
match the enum so typos like `"1H"` are impossible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.money import to_decimal


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    H1 = "1h"
    D1 = "1d"

    @property
    def seconds(self) -> int:
        return {Timeframe.M1: 60, Timeframe.M5: 300, Timeframe.H1: 3600, Timeframe.D1: 86400}[self]


@dataclass(frozen=True, slots=True)
class PriceBar:
    """One OHLCV candle.

    Invariants:
    - `ts` is UTC and aligned to the timeframe boundary (or it's a bug
      upstream — the adapter is expected to align before yielding).
    - `high >= max(open, close)` and `low <= min(open, close)`.
    """

    symbol: str
    timeframe: Timeframe
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None
    source: str

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValidationError("symbol required", field="symbol")
        object.__setattr__(self, "symbol", self.symbol.upper())
        if self.ts.tzinfo is None:
            raise ValidationError("ts must be timezone-aware", field="ts")
        object.__setattr__(self, "ts", self.ts.astimezone(UTC))
        for name, raw in (
            ("open", self.open),
            ("high", self.high),
            ("low", self.low),
            ("close", self.close),
        ):
            d = to_decimal(raw, field=name)
            if d <= 0:
                raise ValidationError(f"{name} must be positive", field=name)
            object.__setattr__(self, name, d)
        if self.volume is not None:
            v = to_decimal(self.volume, field="volume")
            if v < 0:
                raise ValidationError("volume must be >= 0", field="volume")
            object.__setattr__(self, "volume", v)

        if self.high < max(self.open, self.close):
            raise ValidationError("high < max(open, close)", field="high")
        if self.low > min(self.open, self.close):
            raise ValidationError("low > min(open, close)", field="low")
        if self.high < self.low:
            raise ValidationError("high < low", field="high")
        if not self.source:
            raise ValidationError("source required", field="source")
