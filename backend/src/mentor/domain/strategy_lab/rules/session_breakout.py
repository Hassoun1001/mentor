"""London-open breakout of the quiet Asian-session range (hourly bars, UTC)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, Signal

_HOURS_IN_DAY = 24


@dataclass(frozen=True, slots=True)
class SessionBreakout(EntryRule):
    """Range = hourly bars starting 00:00 to ``range_end_hour`` UTC; trade its first break.

    Only the first hourly close beyond the range during the morning window
    counts — once either side has broken, the day's signal is spent. The
    stop is structural: the far side of the range.
    """

    family: ClassVar[str] = "session_breakout"
    names_stop: ClassVar[bool] = True
    range_end_hour: int = 7
    session_end_hour: int = 12
    min_range_bars: int = 5

    def __post_init__(self) -> None:
        if not 1 <= self.range_end_hour < self.session_end_hour <= _HOURS_IN_DAY:
            raise ValidationError(
                "need 1 <= range_end_hour < session_end_hour <= 24", field="range_end_hour"
            )
        if not 1 <= self.min_range_bars <= self.range_end_hour:
            raise ValidationError("min_range_bars out of range", field="min_range_bars")

    @property
    def lookback(self) -> int:
        return _HOURS_IN_DAY  # one UTC day of hourly bars

    def signals(self, series: BarSeries) -> list[Signal | None]:
        out: list[Signal | None] = [None] * len(series)
        for i in range(self.lookback - 1, len(series)):
            ts = series.ts[i]
            if not self.range_end_hour <= ts.hour < self.session_end_hour:
                continue
            today = [
                j
                for j in range(max(0, i - _HOURS_IN_DAY + 1), i)
                if series.ts[j].date() == ts.date()
            ]
            box = [j for j in today if series.ts[j].hour < self.range_end_hour]
            if len(box) < self.min_range_bars:
                continue
            high = max(series.high[j] for j in box)
            low = min(series.low[j] for j in box)
            earlier = [j for j in today if series.ts[j].hour >= self.range_end_hour]
            if any(not low <= series.close[j] <= high for j in earlier):
                continue  # the range already broke today
            close = series.close[i]
            if close > high:
                out[i] = Signal(Direction.LONG, "London broke above the Asian range", stop=low)
            elif close < low:
                out[i] = Signal(Direction.SHORT, "London broke below the Asian range", stop=high)
        return out

    def describe(self) -> str:
        start, end = f"{self.range_end_hour:02d}:00", f"{self.session_end_hour:02d}:00"
        return (
            f"Mark the high and low of the quiet overnight hours (00:00–{start} UTC). "
            f"Between {start} and {end}, follow the first hourly close outside that range, "
            f"with the stop at its far side."
        )
