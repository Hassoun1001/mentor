"""Volatility squeeze breakout — trade the first break out of an unusually quiet spell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal


@dataclass(frozen=True, slots=True)
class SqueezeBreakout(EntryRule):
    """Bands at their narrowest in ``quiet`` bars, then a close outside them."""

    family: ClassVar[str] = "squeeze_breakout"
    band: int = 20
    width: float = 2.0
    quiet: int = 120

    def __post_init__(self) -> None:
        if self.band < 2 or self.quiet < 2:
            raise ValidationError("band and quiet must be >= 2", field="band")
        if self.width <= 0:
            raise ValidationError("width must be positive", field="width")

    @property
    def lookback(self) -> int:
        # The squeeze test reads `quiet` bandwidths ending at the previous bar,
        # and each bandwidth needs `band` closes.
        return self.band + self.quiet

    def signals(self, series: BarSeries) -> list[Signal | None]:
        mean = indicators.rolling_mean(series.close, self.band)
        std = indicators.rolling_std(series.close, self.band)
        width: list[float | None] = [
            (s / m) if m is not None and s is not None and m > 0 else None
            for m, s in zip(mean, std, strict=True)
        ]
        out: list[Signal | None] = [None] * len(series)
        for i in range(self.lookback - 1, len(series)):
            spell = width[i - self.quiet : i]
            m, s = mean[i], std[i]
            if m is None or s is None or any(v is None for v in spell):
                continue
            quietest = min(v for v in spell if v is not None)
            if width[i - 1] != quietest:
                continue  # the previous bar was not the quietest of the spell
            close = series.close[i]
            if close > m + self.width * s:
                out[i] = Signal(Direction.LONG, "broke upward out of a squeeze")
            elif close < m - self.width * s:
                out[i] = Signal(Direction.SHORT, "broke downward out of a squeeze")
        return out

    def describe(self) -> str:
        return (
            f"When the {self.band}-bar Bollinger bands are the narrowest they have been in "
            f"{self.quiet} bars, follow the first close outside them."
        )
