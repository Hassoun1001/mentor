"""Trade management — the rules for *after* you're in the trade.

Entry, stop and target answer "what do I place?". They say nothing about
the harder question every real trader faces an hour later: *when do I move
the stop, when do I take something off, and when do I give up waiting?*
Left undecided, those become emotional decisions made while money is
moving — which is where plans die.

So the plan pre-commits to four rules, all derived from the same
volatility forecast that set the stop (never from round numbers):

- **Break-even trigger** — once price has moved ~1R in your favour, move
  the stop to entry. The trade can no longer lose. The cost is being
  stopped out of some winners by noise, which is why the trigger sits at
  a full R rather than a few pips.
- **Trailing stop** — after break-even, trail by ~1 sigma of expected
  move so routine noise doesn't clip you but a genuine reversal does.
- **Partial close** — bank a fraction at ~1R, leave the rest to run to
  target. Converts some paper profit into realised profit and makes
  holding the remainder psychologically far easier.
- **Time stop** — if neither stop nor target is hit by the horizon the
  forecast was made for, the idea has expired. Close it. A prediction
  about the next 24 bars says nothing about bar 200.

Everything here is advice for a human to execute; nothing auto-trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.risk.position_sizing import Direction

# Move to break-even after this multiple of the risk (R) is banked.
_BREAK_EVEN_R = Decimal("1.0")
# Trail by this multiple of the 1-sigma expected move once trailing starts.
_TRAIL_SIGMA_MULT = Decimal("1.0")
# Fraction of the position to close at the partial-take level.
_PARTIAL_FRACTION = Decimal("0.5")
# Partial take at this multiple of R.
_PARTIAL_R = Decimal("1.0")


@dataclass(frozen=True, slots=True)
class TradeManagementPlan:
    """Pre-committed rules for managing an open position."""

    break_even_price: Decimal
    break_even_pips: Decimal  # move from entry that triggers it
    trail_distance_pips: Decimal
    partial_close_price: Decimal
    partial_close_fraction: Decimal
    time_stop_bars: int
    rules: tuple[str, ...]


def build_trade_management(
    *,
    direction: Direction,
    entry: Decimal,
    stop: Decimal,
    pip_size: Decimal,
    expected_move_pips: Decimal,
    horizon_bars: int,
    timeframe_label: str = "bars",
) -> TradeManagementPlan:
    """Derive the post-entry rules from the trade's own risk and volatility.

    ``expected_move_pips`` is the 1-sigma move over the horizon — the same
    number that set the stop — so the trail adapts to the regime instead of
    being a fixed pip guess.
    """
    if pip_size <= 0:
        raise ValidationError("pip_size must be positive", field="pip_size")
    if horizon_bars < 1:
        raise ValidationError("horizon_bars must be >= 1", field="horizon_bars")

    risk_pips = abs(entry - stop) / pip_size
    if risk_pips <= 0:
        raise ValidationError("entry and stop must differ", field="stop")

    is_long = direction is Direction.LONG
    sign = Decimal("1") if is_long else Decimal("-1")

    be_pips = (risk_pips * _BREAK_EVEN_R).quantize(Decimal("0.1"))
    be_price = entry + sign * be_pips * pip_size

    partial_pips = (risk_pips * _PARTIAL_R).quantize(Decimal("0.1"))
    partial_price = entry + sign * partial_pips * pip_size

    trail_pips = (expected_move_pips * _TRAIL_SIGMA_MULT).quantize(Decimal("0.1"))
    if trail_pips <= 0:
        trail_pips = risk_pips.quantize(Decimal("0.1"))

    rules = (
        f"Move the stop to break-even ({be_price.quantize(pip_size)}) once price reaches "
        f"{be_pips} pips in your favour — after that the trade cannot lose.",
        f"Then trail the stop {trail_pips} pips behind price (one sigma of today's "
        f"expected move), so normal noise doesn't clip you but a real reversal does.",
        f"Optionally close {int(_PARTIAL_FRACTION * 100)}% at "
        f"{partial_price.quantize(pip_size)} (+{partial_pips} pips ≈ 1R) and let the "
        f"rest run to target.",
        f"Time stop: if neither stop nor target is hit within {horizon_bars} "
        f"{timeframe_label}, close it — the forecast it was based on has expired.",
        "Never move the stop away from price to avoid being stopped out. That single "
        "habit destroys more accounts than any bad entry.",
    )

    return TradeManagementPlan(
        break_even_price=be_price.quantize(pip_size),
        break_even_pips=be_pips,
        trail_distance_pips=trail_pips,
        partial_close_price=partial_price.quantize(pip_size),
        partial_close_fraction=_PARTIAL_FRACTION,
        time_stop_bars=horizon_bars,
        rules=rules,
    )
