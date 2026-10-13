"""Moving-average crossover, acting only when the market is actually trending."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal


@dataclass(frozen=True, slots=True)
class MaCrossTrend(EntryRule):
    """Simple-average crossover gated by Kaufman's efficiency ratio (0 = no gate)."""

    family: ClassVar[str] = "ma_cross_trend"
    fast: int = 20
    slow: int = 100
    er_period: int = 20
    er_min: float = 0.0

    def __post_init__(self) -> None:
        if not 1 <= self.fast < self.slow:
            raise ValidationError("need 1 <= fast < slow", field="fast")
        if self.er_period < 2:
            raise ValidationError("er_period must be >= 2", field="er_period")
        if not 0 <= self.er_min < 1:
            raise ValidationError("er_min must be in [0, 1)", field="er_min")

    @property
    def lookback(self) -> int:
        # The crossover compares this bar's averages with the previous bar's.
        return max(self.slow + 1, self.er_period + 1)

    def signals(self, series: BarSeries) -> list[Signal | None]:
        fast = indicators.rolling_mean(series.close, self.fast)
        slow = indicators.rolling_mean(series.close, self.slow)
        er = indicators.efficiency_ratio(series.close, self.er_period)
        out: list[Signal | None] = [None] * len(series)
        for i in range(1, len(series)):
            f0, s0, f1, s1, e = fast[i - 1], slow[i - 1], fast[i], slow[i], er[i]
            if f0 is None or s0 is None or f1 is None or s1 is None or e is None:
                continue
            if e < self.er_min:
                continue
            if f1 > s1 and f0 <= s0:
                out[i] = Signal(Direction.LONG, f"{self.fast}/{self.slow} average crossed up")
            elif f1 < s1 and f0 >= s0:
                out[i] = Signal(Direction.SHORT, f"{self.fast}/{self.slow} average crossed down")
        return out

    def describe(self) -> str:
        gate = (
            f" — but only when the market is trending (efficiency at least {self.er_min:g} "
            f"over {self.er_period} bars)"
            if self.er_min > 0
            else ""
        )
        return (
            f"Buy when the {self.fast}-bar average crosses above the {self.slow}-bar average, "
            f"sell short when it crosses below{gate}."
        )
