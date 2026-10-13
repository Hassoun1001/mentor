"""Mean reversion inside ranges, with a trend filter that stands aside in trends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal


@dataclass(frozen=True, slots=True)
class RangeReversion(EntryRule):
    """Fade a close outside the Bollinger band, aiming back at the average.

    Only when Kaufman's efficiency ratio says the market is ranging. The
    target is structural — the average itself — so the payoff shrinks as
    the band narrows, which is the honest shape of this trade.
    """

    family: ClassVar[str] = "range_reversion"
    names_target: ClassVar[bool] = True
    band: int = 24
    width: float = 2.0
    er_period: int = 24
    er_max: float = 0.3

    def __post_init__(self) -> None:
        if self.band < 2 or self.er_period < 2:
            raise ValidationError("band and er_period must be >= 2", field="band")
        if self.width <= 0:
            raise ValidationError("width must be positive", field="width")
        if not 0 < self.er_max < 1:
            raise ValidationError("er_max must be in (0, 1)", field="er_max")

    @property
    def lookback(self) -> int:
        return max(self.band, self.er_period + 1)

    def signals(self, series: BarSeries) -> list[Signal | None]:
        mean = indicators.rolling_mean(series.close, self.band)
        std = indicators.rolling_std(series.close, self.band)
        er = indicators.efficiency_ratio(series.close, self.er_period)
        out: list[Signal | None] = [None] * len(series)
        for i in range(len(series)):
            m, s, e = mean[i], std[i], er[i]
            if m is None or s is None or e is None or s <= 0 or e >= self.er_max:
                continue
            close = series.close[i]
            if close < m - self.width * s:
                out[i] = Signal(Direction.LONG, "stretched below the range average", target=m)
            elif close > m + self.width * s:
                out[i] = Signal(Direction.SHORT, "stretched above the range average", target=m)
        return out

    def describe(self) -> str:
        return (
            f"Only when the market is going sideways (efficiency below {self.er_max:g} over "
            f"{self.er_period} bars): when price closes more than {self.width:g} standard "
            f"deviations from its {self.band}-bar average, bet on a return to the average."
        )
