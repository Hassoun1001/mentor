"""ATR-based stop helper.

> Suggests stop and target distances scaled to current volatility rather
> than guesswork.   — Mentor product plan, §6.E

The function is pure: it takes the current ATR (computed elsewhere by the
indicator service in Phase 1) and the chosen multiple, and returns a stop
distance. The mentor layer explains *why* the multiplier matters: a 1× ATR
stop sits where normal noise can hit it; 2–3× ATR is the common range.
"""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.money import to_decimal


def atr_stop_distance(
    *,
    atr: Decimal | int | str | float,
    multiplier: Decimal | int | str | float = Decimal("2"),
) -> Decimal:
    """Return the stop distance in price units (NOT pips) for an ATR-scaled stop.

    The caller converts to pips via `Instrument.pips_between`.
    """
    a = to_decimal(atr, field="atr")
    m = to_decimal(multiplier, field="multiplier")
    if a <= 0:
        raise ValidationError("atr must be positive", field="atr")
    if m <= 0:
        raise ValidationError("multiplier must be positive", field="multiplier")
    return a * m
