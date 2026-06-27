"""Pure-function indicators.

All indicators take a sequence of `Decimal` and return a `Decimal | None`
(when the series is too short). They never mutate input. They never
read from the future. They are the building blocks the backtester and
the live forecasting pipeline share.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar


def _to_decimal_seq(values: Sequence[Decimal]) -> Sequence[Decimal]:
    if not values:
        raise ValidationError("values must not be empty")
    return values


def sma(values: Sequence[Decimal], period: int) -> Decimal | None:
    """Simple moving average over the last `period` values."""
    if period < 1:
        raise ValidationError("period must be >= 1", field="period")
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window, Decimal("0")) / Decimal(period)


def ema(values: Sequence[Decimal], period: int) -> Decimal | None:
    """Exponential moving average. Smoothing factor = 2 / (period + 1)."""
    if period < 1:
        raise ValidationError("period must be >= 1", field="period")
    _to_decimal_seq(values)
    if len(values) < period:
        return None
    alpha = Decimal("2") / Decimal(period + 1)
    # Seed EMA with the SMA of the first `period` values for stability.
    seed = sum(values[:period], Decimal("0")) / Decimal(period)
    current = seed
    for v in values[period:]:
        current = alpha * v + (Decimal("1") - alpha) * current
    return current


def atr(bars: Sequence[PriceBar], period: int = 14) -> Decimal | None:
    """Average True Range — the noise-floor estimator behind stop sizing.

    True range at bar i:
        max(high_i - low_i, |high_i - close_{i-1}|, |low_i - close_{i-1}|)
    """
    if period < 1:
        raise ValidationError("period must be >= 1", field="period")
    if len(bars) < period + 1:
        return None
    trs: list[Decimal] = []
    for i in range(1, len(bars)):
        prev_close = bars[i - 1].close
        h = bars[i].high
        l = bars[i].low  # noqa: E741 — domain term
        tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        trs.append(tr)
    # Use the simple average of the last `period` true ranges.
    if len(trs) < period:
        return None
    return sum(trs[-period:], Decimal("0")) / Decimal(period)


def rsi(values: Sequence[Decimal], period: int = 14) -> Decimal | None:
    """Relative Strength Index — Wilder's smoothing."""
    if period < 2:
        raise ValidationError("period must be >= 2", field="period")
    if len(values) < period + 1:
        return None
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(delta if delta > 0 else Decimal("0"))
        losses.append(-delta if delta < 0 else Decimal("0"))
    avg_gain = sum(gains[:period], Decimal("0")) / Decimal(period)
    avg_loss = sum(losses[:period], Decimal("0")) / Decimal(period)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * Decimal(period - 1) + gains[i]) / Decimal(period)
        avg_loss = (avg_loss * Decimal(period - 1) + losses[i]) / Decimal(period)
    if avg_loss == 0:
        return Decimal("100")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
