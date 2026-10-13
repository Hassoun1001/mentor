"""A market with a planted, causal edge — and a rule that can see it.

Every twelfth bar is a sharp down bar, and the three bars after it rise —
seven times in ten. The other three times they fall, so the edge is real
but noisy, the way a real one would be.

``Marker`` buys after a sharp down bar. On this market it should pass the
gate by a wide margin; on a driftless random walk it must not. Together
they show the gate can say yes as well as no.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import ClassVar

from mentor.domain.market.bars import Timeframe
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.library import CandidateDefinition
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import EntryRule, ExitRules, Signal


@dataclass(frozen=True, slots=True)
class Marker(EntryRule):
    family: ClassVar[str] = "test_marker"
    drop: float = 0.0035

    @property
    def lookback(self) -> int:
        return 1

    def signals(self, series: BarSeries) -> list[Signal | None]:
        return [
            Signal(Direction.LONG, "sharp down bar")
            if series.close[i] < series.open[i] * (1 - self.drop)
            else None
            for i in range(len(series))
        ]

    def describe(self) -> str:
        return "Buy the open after any bar that falls sharply from its open to its close."


def planted_market(
    n: int = 4200,
    *,
    seed: int = 17,
    start: datetime = datetime(2015, 1, 1, tzinfo=UTC),
    step: timedelta = timedelta(days=1),
    edge: bool = True,
) -> BarSeries:
    rng = random.Random(seed)
    price = 1.10
    ts, o, h, lo, c = [], [], [], [], []
    works = True
    for i in range(n):
        open_ = price
        phase = i % 12
        if edge and phase == 0:
            close = open_ * (1 - 0.005)
            works = rng.random() < 0.7
        elif edge and phase in (1, 2, 3):
            # A failed setup drifts down, gently enough not to look like a new marker.
            close = open_ * (1 + (0.006 if works else -0.0025))
        else:
            close = open_ * (1 + rng.gauss(0, 0.001))
        high = max(open_, close) * (1 + 0.0003)
        low = min(open_, close) * (1 - 0.0003)
        ts.append(start + i * step)
        o.append(open_)
        h.append(high)
        lo.append(low)
        c.append(close)
        price = close
    return BarSeries(ts=tuple(ts), open=tuple(o), high=tuple(h), low=tuple(lo), close=tuple(c))


def marker_candidate(
    key: str = "test_marker_d1", timeframe: Timeframe = Timeframe.D1
) -> CandidateDefinition:
    return CandidateDefinition(
        key=key,
        title="Planted-edge marker",
        timeframe=timeframe,
        hypothesis="The test market rises after every sharp down bar, by construction.",
        grid=tuple(
            (Marker(drop=d), ExitRules(stop_atr=1.0, target_r=1.0, max_bars=5))
            for d in (0.0035, 0.004)
        ),
        added=date(2026, 10, 13),
        added_by="tests",
    )
