"""Deterministic bar fixtures for the strategy-lab tests.

Seeded random walks, so every run sees identical bars, plus a helper to
build hand-written bars for mechanics tests where every price matters.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from mentor.domain.strategy_lab.series import BarSeries

DAY = timedelta(days=1)
HOUR = timedelta(hours=1)


def random_walk(
    n: int,
    *,
    seed: int = 7,
    start: datetime = datetime(2015, 1, 1, tzinfo=UTC),
    step: timedelta = DAY,
    vol: float = 0.005,
    price: float = 1.10,
) -> BarSeries:
    """A driftless random walk: no rule should find an edge in it."""
    rng = random.Random(seed)
    ts, o, h, lo, c = [], [], [], [], []
    for i in range(n):
        open_ = price * (1 + rng.gauss(0, vol / 10))
        close = open_ * (1 + rng.gauss(0, vol))
        high = max(open_, close) * (1 + abs(rng.gauss(0, vol / 2)))
        low = min(open_, close) * (1 - abs(rng.gauss(0, vol / 2)))
        ts.append(start + i * step)
        o.append(open_)
        h.append(high)
        lo.append(low)
        c.append(close)
        price = close
    return BarSeries(ts=tuple(ts), open=tuple(o), high=tuple(h), low=tuple(lo), close=tuple(c))


def bars(
    rows: Sequence[tuple[float, float, float, float]],
    *,
    start: datetime = datetime(2025, 1, 6, tzinfo=UTC),
    step: timedelta = DAY,
) -> BarSeries:
    """Hand-written (open, high, low, close) rows."""
    return BarSeries(
        ts=tuple(start + i * step for i in range(len(rows))),
        open=tuple(r[0] for r in rows),
        high=tuple(r[1] for r in rows),
        low=tuple(r[2] for r in rows),
        close=tuple(r[3] for r in rows),
    )

