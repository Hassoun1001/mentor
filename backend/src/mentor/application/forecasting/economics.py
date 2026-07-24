"""What each lane has to beat before a call is worth making.

The significance layer can test a hit rate against any baseline; this is
where the baseline comes from. It measures the lane's own move
distribution from the bars actually stored and charges the same
round-trip friction the backtester charges, so "is there an edge?" and
"would it have paid?" stop being different questions answered by
different parts of the app.

The two lanes land in very different places, which is the point:

- **1h / 24-bar horizon** — 0.218% typical move, hurdle **52.36%**
- **1d / 5-bar horizon** — 0.727% typical move, hurdle **50.73%**

A fixed cost is a smaller share of a bigger move, so the longer lane is
more than three times easier to clear (2.36pp of hurdle against 0.73pp).
Grading both against 50% hid that entirely.

Both figures are measured, not assumed — recompute them rather than
trusting these comments if the cost model or the horizons change.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from mentor.config import Settings
from mentor.domain.backtest.costs import CostModel
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import Timeframe
from mentor.domain.stats.breakeven import BreakevenBasis, estimate_breakeven
from mentor.infrastructure.repositories.price_bars import PriceBarRepository

_D1_TIMEFRAME = "1d"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

# Wording for `assess_proportion(baseline_label=...)`. The default there is
# "a coin flip", which is exactly the claim we are replacing.
BREAKEVEN_LABEL = "the spread-adjusted breakeven"


def horizon_for(timeframe: str, settings: Settings) -> int:
    """Forecast horizon in bars for a lane's timeframe."""
    if timeframe == _D1_TIMEFRAME:
        return settings.loop_d1_horizon_bars
    return settings.loop_horizon_bars


def round_trip_cost_price(symbol: str, cost_model: CostModel | None = None) -> float:
    """Round-trip friction in price units.

    Deliberately the same arithmetic as ``CostModel.friction_for``: a round
    trip pays ``spread + 2 x slippage`` pips, because entry and exit are
    each worsened by half the spread plus a slippage leg. Sharing the
    number is the whole point — a hurdle computed from a different cost
    than the backtester charges would just be a second opinion.
    """
    model = cost_model or CostModel()
    pips = model.spread_pips + 2 * model.slippage_pips
    return float(pips * get_instrument(symbol).pip_size)


async def lane_breakeven(
    session: AsyncSession,
    *,
    settings: Settings,
    timeframe: str | None = None,
) -> BreakevenBasis:
    """Measure the win rate this lane's calls must clear to pay for themselves.

    ``timeframe=None`` means the caller is looking at the primary lane
    (or at both at once, where the primary lane's hurdle is the honest
    default — it is the stricter of the two).
    """
    tf = timeframe or settings.loop_timeframe
    symbol = settings.loop_symbol

    rows = await PriceBarRepository(session).range(
        symbol=symbol,
        timeframe=Timeframe(tf),
        start=_EPOCH,
        end=datetime.now(UTC) + timedelta(days=1),
    )
    return estimate_breakeven(
        [float(r.close) for r in rows],
        horizon_bars=horizon_for(tf, settings),
        cost_per_trade_price=round_trip_cost_price(symbol),
    )
