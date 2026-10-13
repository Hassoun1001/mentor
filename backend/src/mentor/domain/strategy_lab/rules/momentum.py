"""Time-series momentum — trade in the direction of the last few months."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal


@dataclass(frozen=True, slots=True)
class TimeSeriesMomentum(EntryRule):
    """Long when the close is above the close ``period`` bars ago, short when below.

    The rule speaks on every bar; the plan only listens when it is flat, so
    the time stop is what sets the holding period and the rebalance rhythm.
    """

    family: ClassVar[str] = "time_series_momentum"
    period: int = 126

    def __post_init__(self) -> None:
        if self.period < 2:
            raise ValidationError("period must be >= 2", field="period")

    @property
    def lookback(self) -> int:
        return self.period + 1

    def signals(self, series: BarSeries) -> list[Signal | None]:
        out: list[Signal | None] = [None] * len(series)
        for i in range(self.period, len(series)):
            change = series.close[i] - series.close[i - self.period]
            if change > 0:
                out[i] = Signal(Direction.LONG, f"higher than {self.period} bars ago")
            elif change < 0:
                out[i] = Signal(Direction.SHORT, f"lower than {self.period} bars ago")
        return out

    def describe(self) -> str:
        return (
            f"Buy if price is higher than it was {self.period} bars ago; sell short if it "
            f"is lower."
        )
