"""Donchian channel breakout — the turtle traders' entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal


@dataclass(frozen=True, slots=True)
class DonchianBreakout(EntryRule):
    """Go with a close beyond the highest high / lowest low of the prior ``channel`` bars."""

    family: ClassVar[str] = "donchian_breakout"
    channel: int = 55

    def __post_init__(self) -> None:
        if self.channel < 2:
            raise ValidationError("channel must be >= 2", field="channel")

    @property
    def lookback(self) -> int:
        return self.channel + 1

    def signals(self, series: BarSeries) -> list[Signal | None]:
        out: list[Signal | None] = [None] * len(series)
        for i in range(self.channel, len(series)):
            prior_high = max(series.high[i - self.channel : i])
            prior_low = min(series.low[i - self.channel : i])
            close = series.close[i]
            if close > prior_high:
                out[i] = Signal(Direction.LONG, f"closed above the {self.channel}-bar high")
            elif close < prior_low:
                out[i] = Signal(Direction.SHORT, f"closed below the {self.channel}-bar low")
        return out

    def describe(self) -> str:
        return (
            f"Buy when price closes above the highest high of the previous {self.channel} "
            f"bars; sell short when it closes below the lowest low."
        )
