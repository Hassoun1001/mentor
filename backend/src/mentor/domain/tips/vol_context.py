"""Per-ticker volatility context for tracked tips.

Reuses the pure volatility math (EWMA + realized vol) on the close series
the scorer already fetches — no OHLC and no extra network calls. It answers,
for each tracked ticker, "how much does this thing normally move, and is it
calm or wild right now?" so the tips table shows objective context next to a
tipster's call (e.g. a "buy the dip" call on a name that's currently *wild*).

Stocks aren't FX, so the move is expressed as a **percentage**, not pips.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.forecasting.volatility import (
    VolRegime,
    ewma_vol,
    log_returns,
    percentile_rank,
    regime_from_percentile,
    rolling_realized_vol,
)

_MIN_CLOSES = 25


@dataclass(frozen=True, slots=True)
class TickerVolContext:
    expected_move_pct: Decimal  # 1-sigma move over the horizon, in percent
    percentile: Decimal  # vs the ticker's own recent history
    regime: VolRegime  # calm / normal / wide


def build_ticker_vol_context(
    closes: Sequence[Decimal], *, horizon_days: int = 5
) -> TickerVolContext | None:
    """EWMA volatility read from a daily close series. ``None`` if too short."""
    if len(closes) < _MIN_CLOSES or horizon_days < 1:
        return None
    rets = log_returns(closes)
    per_bar = ewma_vol(rets)
    if per_bar is None or per_bar <= 0:
        return None
    history = rolling_realized_vol(closes)
    pctl = percentile_rank(per_bar, history)
    # 1-sigma cumulative move over the horizon, as a percentage of price.
    move = per_bar * Decimal(horizon_days).sqrt() * Decimal("100")
    return TickerVolContext(
        expected_move_pct=move,
        percentile=pctl,
        regime=regime_from_percentile(pctl),
    )
