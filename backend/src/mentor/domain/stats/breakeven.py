"""The win rate a directional call actually has to clear.

Every "is there an edge?" question in this app was measured against 50%,
the coin flip. That is the right null for *guessing*, and the wrong null
for *trading*, because a trade pays the spread whether it wins or loses.
A model that is right 51% of the time is better than a coin and still
loses money, and the gate that decides whether to believe a model could
not tell those apart.

The arithmetic. Let ``m`` be the typical absolute move over the forecast
horizon and ``c`` the round-trip friction, both as fractions of price. A
win returns ``m - c``, a loss returns ``-(m + c)``, so expectancy at win
rate ``p`` is::

    E = p(m - c) - (1 - p)(m + c) = 2pm - m - c

Setting that to zero gives the hurdle::

    p* = (m + c) / 2m = 1/2 + c / 2m

Which is 50% only when trading is free. On the measured EUR/USD bar
distribution it is **52.36%** for the 24-hour lane and **50.73%** for the
5-day lane — the hurdle shrinks as the horizon grows, because a fixed
cost is a smaller share of a bigger move.

Two honest caveats, both deliberate:

- Wins and losses are both sized at ``m``. A model whose wins are
  systematically larger than its losses faces a lower hurdle, but that
  is a magnitude edge, and assuming one you have not demonstrated is
  exactly the kind of free lunch this module exists to deny. Symmetric
  is the neutral assumption.
- ``m`` is the *mean* absolute move, not the median. The distribution is
  right-skewed (mean 0.218% vs median 0.155% at h=24), so the mean is
  the more forgiving of the two. Using it keeps the hurdle conservative
  in the direction that matters: it will not overstate the bar and
  reject a model that would in fact have paid.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from mentor.domain.errors import ValidationError

# Below this many non-overlapping windows the move distribution is not
# worth estimating from, and we say so rather than quoting a hurdle built
# on a handful of observations.
MIN_WINDOWS = 30

# If friction approaches the typical move, the hurdle approaches certainty.
# That is a real finding — the horizon is too short to trade — but
# `assess_proportion` needs a baseline strictly inside (0, 1), so cap it
# and let the note carry the message.
_MAX_BREAKEVEN = 0.95

_COIN_FLIP = 0.5


@dataclass(frozen=True, slots=True)
class BreakevenBasis:
    """The hurdle, and enough of its inputs to argue with it."""

    breakeven: float  # win rate a directional call must beat to pay
    mean_abs_move: float  # fraction of price, over one forecast horizon
    cost_per_trade: float  # fraction of price, round trip
    n_windows: int  # independent windows the move estimate rests on
    measured: bool  # False => fell back to the coin flip
    note: str

    @property
    def hurdle_pp(self) -> float:
        """Percentage points above a coin flip. The thing worth reporting."""
        return (self.breakeven - _COIN_FLIP) * 100


def breakeven_win_rate(*, mean_abs_move: float, cost_per_trade: float) -> float:
    """``1/2 + c/2m`` — the win rate at which a symmetric call breaks even."""
    if mean_abs_move <= 0:
        raise ValidationError("mean_abs_move must be positive", field="mean_abs_move")
    if cost_per_trade < 0:
        raise ValidationError("cost_per_trade must be >= 0", field="cost_per_trade")
    return min(_MAX_BREAKEVEN, _COIN_FLIP + cost_per_trade / (2 * mean_abs_move))


def mean_abs_move(closes: Sequence[float], *, horizon_bars: int) -> tuple[float, int]:
    """Average absolute fractional move over one horizon, and the sample size.

    Windows are **non-overlapping**. Overlapping windows share bars, so
    they are not independent observations of the move distribution; using
    them would inflate the apparent sample without adding information —
    the same mistake the significance layer already refuses to make when
    grading predictions.
    """
    if horizon_bars <= 0:
        raise ValidationError("horizon_bars must be positive", field="horizon_bars")

    moves = [
        abs(closes[i + horizon_bars] - closes[i]) / closes[i]
        for i in range(0, len(closes) - horizon_bars, horizon_bars)
        if closes[i] > 0
    ]
    if not moves:
        return 0.0, 0
    return sum(moves) / len(moves), len(moves)


def estimate_breakeven(
    closes: Sequence[float],
    *,
    horizon_bars: int,
    cost_per_trade_price: float,
    min_windows: int = MIN_WINDOWS,
) -> BreakevenBasis:
    """Measure the hurdle from real bars, or say plainly that you could not.

    ``cost_per_trade_price`` is round-trip friction in price units (for
    EUR/USD, 0.00012 is 1.2 pips — the spread plus two slippage legs that
    `CostModel` already charges every backtest).

    When there are too few bars the fallback is the coin flip, flagged as
    unmeasured. That is the status quo ante, so nothing silently gets
    *easier* than it was; the flag exists so a caller can show the reader
    that the economic bar is unknown rather than met.
    """
    if cost_per_trade_price < 0:
        raise ValidationError("cost must be >= 0", field="cost_per_trade_price")

    positive = [c for c in closes if c > 0]
    move, n = mean_abs_move(closes, horizon_bars=horizon_bars)

    if n < min_windows or move <= 0 or not positive:
        return BreakevenBasis(
            breakeven=_COIN_FLIP,
            mean_abs_move=move,
            cost_per_trade=0.0,
            n_windows=n,
            measured=False,
            note=(
                f"Only {n} independent {horizon_bars}-bar windows available "
                f"({min_windows} needed), so the spread-adjusted hurdle could not be "
                f"measured. Falling back to a coin flip — which understates the real "
                f"bar, because trading is not free."
            ),
        )

    cost = cost_per_trade_price / (sum(positive) / len(positive))
    hurdle = breakeven_win_rate(mean_abs_move=move, cost_per_trade=cost)

    if hurdle >= _MAX_BREAKEVEN:
        note = (
            f"Round-trip friction ({cost * 100:.4f}% of price) is comparable to the "
            f"typical {horizon_bars}-bar move ({move * 100:.4f}%). No realistic win "
            f"rate pays at this horizon — the cost, not the forecast, is the binding "
            f"constraint."
        )
    else:
        note = (
            f"Breakeven {hurdle * 100:.2f}% — a call must clear this, not 50%, to pay "
            f"for itself. Typical {horizon_bars}-bar move {move * 100:.3f}% against "
            f"{cost * 100:.4f}% round-trip friction, over {n:,} independent windows."
        )

    return BreakevenBasis(
        breakeven=hurdle,
        mean_abs_move=move,
        cost_per_trade=cost,
        n_windows=n,
        measured=True,
        note=note,
    )
