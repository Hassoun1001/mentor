"""Narrow-range breakout — Toby Crabel's NR4 / NR7 pattern."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal


@dataclass(frozen=True, slots=True)
class NarrowRangeBreakout(EntryRule):
    """After the narrowest bar of the last ``narrow``, follow a close beyond it.

    The stop is structural: the far side of the narrow bar.
    """

    family: ClassVar[str] = "narrow_range_breakout"
    names_stop: ClassVar[bool] = True
    narrow: int = 7

    def __post_init__(self) -> None:
        if self.narrow < 2:
            raise ValidationError("narrow must be >= 2", field="narrow")

    @property
    def lookback(self) -> int:
        return self.narrow + 1

    def signals(self, series: BarSeries) -> list[Signal | None]:
        out: list[Signal | None] = [None] * len(series)
        for i in range(self.narrow, len(series)):
            ranges = [series.high[j] - series.low[j] for j in range(i - self.narrow, i)]
            if ranges[-1] > min(ranges):
                continue
            high, low = series.high[i - 1], series.low[i - 1]
            close = series.close[i]
            if close > high:
                out[i] = Signal(
                    Direction.LONG, f"broke above an NR{self.narrow} bar", stop=low
                )
            elif close < low:
                out[i] = Signal(
                    Direction.SHORT, f"broke below an NR{self.narrow} bar", stop=high
                )
        return out

    def describe(self) -> str:
        return (
            f"When a bar has the smallest range of the last {self.narrow}, follow the next "
            f"close beyond its high or low, with the stop at its other side."
        )
