"""Trend pullback — buy the dip in an uptrend, sell the rally in a downtrend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal


@dataclass(frozen=True, slots=True)
class TrendPullback(EntryRule):
    """Trend from a long simple average; entry when a short RSI is stretched against it."""

    family: ClassVar[str] = "trend_pullback"
    trend: int = 200
    rsi_period: int = 2
    rsi_entry: float = 10.0  # long below this; short above 100 - this

    def __post_init__(self) -> None:
        if self.trend < 2 or self.rsi_period < 2:
            raise ValidationError("trend and rsi_period must be >= 2", field="trend")
        if not 0 < self.rsi_entry < 50:
            raise ValidationError("rsi_entry must be in (0, 50)", field="rsi_entry")

    @property
    def lookback(self) -> int:
        return max(self.trend, self.rsi_period + 1)

    def signals(self, series: BarSeries) -> list[Signal | None]:
        trend = indicators.rolling_mean(series.close, self.trend)
        strength = indicators.rsi(series.close, self.rsi_period)
        out: list[Signal | None] = [None] * len(series)
        for i in range(len(series)):
            avg, r = trend[i], strength[i]
            if avg is None or r is None:
                continue
            close = series.close[i]
            if close > avg and r < self.rsi_entry:
                out[i] = Signal(Direction.LONG, f"pullback (RSI {r:.0f}) in an uptrend")
            elif close < avg and r > 100 - self.rsi_entry:
                out[i] = Signal(Direction.SHORT, f"rally (RSI {r:.0f}) in a downtrend")
        return out

    def describe(self) -> str:
        return (
            f"When price is above its {self.trend}-bar average (an uptrend), buy after a "
            f"short, sharp dip ({self.rsi_period}-bar RSI below {self.rsi_entry:g}); mirror "
            f"it for shorts in a downtrend."
        )
