"""Pending-prediction resolver — closes the calibration loop.

For every prediction whose horizon has elapsed (`horizon_at < now`) and
that hasn't been resolved yet, look up the realised close from the price
repository and write it back. Idempotent — runs on a schedule or on-demand.

**Closed markets.** FX stops printing on Friday evening and resumes on
Sunday night, a gap of roughly 50 hours. A 24-hour horizon opened on
Thursday or Friday therefore expires while the market is shut, and no bar
exists anywhere near it. The resolver used to search a window of two
timeframes either side and give up — which orphaned those predictions
permanently. They stayed pending forever, and because the loop predicts
hourly, that quietly deleted every late-week call from the track record.
The damage was not merely missing data: the surviving sample was biased
toward mid-week, so the measured accuracy described a subset of the week
rather than the week.

The honest realisation is the **first price the market actually printed
at or after the horizon**. If you had held that position, the weekend gap
is exactly what you would have lived through, and Sunday's open is the
price you would have got. So that is what we grade against, with the lag
recorded. Past ``_MAX_RESOLUTION_LAG`` the silence is no longer a weekend
but a data outage, and the prediction stays pending rather than being
graded against a price from an unrelated week.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.resolver")

# How long after the horizon we will still accept the next printed price.
# A weekend is ~50h; four days absorbs that plus a public holiday. Beyond
# it, the gap is a broken feed rather than a closed market, and grading a
# 24-hour call against a price from the following week would be fiction.
_MAX_RESOLUTION_LAG = timedelta(days=4)


@dataclass(frozen=True, slots=True)
class ResolverResult:
    examined: int
    resolved: int
    still_pending: int


async def resolve_pending_predictions(
    *,
    predictions: PredictionRepository,
    prices: PriceBarRepository,
    now: datetime | None = None,
) -> ResolverResult:
    now = now or datetime.now(UTC)
    pending = await predictions.unresolved_due_by(now)
    resolved = 0
    still_pending = 0

    for row in pending:
        tf = Timeframe(row.timeframe)
        # A bar stamped slightly before the horizon still counts — feeds round
        # to bar boundaries. Beyond that we look *forward* for the next price
        # the market printed, so a horizon expiring into a closed market
        # resolves at the reopen instead of hanging forever.
        window_start = row.horizon_at - timedelta(seconds=tf.seconds * 2)
        window_end = row.horizon_at + _MAX_RESOLUTION_LAG
        bars = await prices.range(
            symbol=row.symbol,
            timeframe=tf,
            start=window_start,
            end=window_end,
        )
        if not bars:
            still_pending += 1
            continue
        # The first price at or after the horizon is what you would have got.
        # Only fall back to the nearest earlier bar when nothing follows.
        at_or_after = [b for b in bars if b.ts >= row.horizon_at]
        chosen = (
            min(at_or_after, key=lambda b: b.ts)
            if at_or_after
            else max(bars, key=lambda b: b.ts)
        )
        lag_hours = (chosen.ts - row.horizon_at).total_seconds() / 3600
        if lag_hours > 3:
            log.info(
                "resolver.late_fill",
                prediction=str(row.id),
                horizon_at=row.horizon_at.isoformat(),
                filled_at=chosen.ts.isoformat(),
                lag_hours=round(lag_hours, 1),
            )
        await predictions.resolve(row.id, realised_close=chosen.close, resolved_at=now)
        resolved += 1

    result = ResolverResult(
        examined=len(pending),
        resolved=resolved,
        still_pending=len(pending) - resolved,
    )
    log.info(
        "resolver.done",
        examined=result.examined,
        resolved=result.resolved,
        still_pending=result.still_pending,
    )
    return result
