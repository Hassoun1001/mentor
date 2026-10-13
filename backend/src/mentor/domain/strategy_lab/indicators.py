"""Finite-window indicators for the strategy lab.

Every function here returns one value per bar, ``None`` until enough
history exists, and computes the value at bar *i* from bars
``i - lookback + 1 .. i`` only. Two properties follow, and the tests pin
both:

- **No lookahead.** Truncating the series after bar *i* never changes the
  value at bar *i*.
- **No infinite memory.** Recomputing on just the last ``lookback`` bars
  gives the identical value. This is why there is no exponential average
  here: an EMA seeded ten years ago and one seeded last month disagree
  forever, so a live paper trader working from recent bars would trade a
  slightly different plan than the one that was back-tested. With finite
  windows they are the same plan, bit for bit.

Sums use ``math.fsum`` — exactly rounded — so a window's value does not
depend on where in a longer series the window happens to sit.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from mentor.domain.errors import ValidationError

Series = list[float | None]


def _check(period: int, minimum: int = 1) -> None:
    if period < minimum:
        raise ValidationError(f"period must be >= {minimum}", field="period")


def rolling_mean(values: Sequence[float], period: int) -> Series:
    _check(period)
    out: Series = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = math.fsum(values[i - period + 1 : i + 1]) / period
    return out


def rolling_std(values: Sequence[float], period: int) -> Series:
    """Population standard deviation over the window (the Bollinger convention)."""
    _check(period, 2)
    out: Series = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        mean = math.fsum(window) / period
        out[i] = math.sqrt(math.fsum((v - mean) ** 2 for v in window) / period)
    return out


def rolling_max(values: Sequence[float], period: int) -> Series:
    _check(period)
    out: Series = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = max(values[i - period + 1 : i + 1])
    return out


def rolling_min(values: Sequence[float], period: int) -> Series:
    _check(period)
    out: Series = [None] * len(values)
    for i in range(period - 1, len(values)):
        out[i] = min(values[i - period + 1 : i + 1])
    return out


def true_range(high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Series:
    """True range; undefined on the first bar, which has no previous close."""
    out: Series = [None] * len(close)
    for i in range(1, len(close)):
        prev = close[i - 1]
        out[i] = max(high[i] - low[i], abs(high[i] - prev), abs(low[i] - prev))
    return out


def atr(high: Sequence[float], low: Sequence[float], close: Sequence[float], period: int) -> Series:
    """Simple average of the last ``period`` true ranges. Lookback ``period + 1``."""
    _check(period)
    tr = true_range(high, low, close)
    out: Series = [None] * len(close)
    for i in range(period, len(close)):
        window = tr[i - period + 1 : i + 1]
        out[i] = math.fsum(v for v in window if v is not None) / period
    return out


def rsi(values: Sequence[float], period: int) -> Series:
    """RSI from simple averages of gains and losses (Cutler's form).

    Wilder's original smooths recursively, which gives it infinite memory —
    exactly what this module avoids. Lookback ``period + 1``.
    """
    _check(period, 2)
    out: Series = [None] * len(values)
    for i in range(period, len(values)):
        changes = [values[j] - values[j - 1] for j in range(i - period + 1, i + 1)]
        gain = math.fsum(c for c in changes if c > 0) / period
        loss = math.fsum(-c for c in changes if c < 0) / period
        if loss == 0:
            out[i] = 100.0 if gain > 0 else 50.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + gain / loss)
    return out


def efficiency_ratio(values: Sequence[float], period: int) -> Series:
    """Kaufman's efficiency ratio: net move over the path travelled, in [0, 1].

    Near 1 the market went somewhere in a straight line (trending); near 0
    it travelled a long way to end up where it started (ranging).
    Lookback ``period + 1``.
    """
    _check(period)
    out: Series = [None] * len(values)
    for i in range(period, len(values)):
        path = math.fsum(abs(values[j] - values[j - 1]) for j in range(i - period + 1, i + 1))
        out[i] = abs(values[i] - values[i - period]) / path if path > 0 else 0.0
    return out
