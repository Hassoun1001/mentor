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
recorded. Past ``MAX_RESOLUTION_LAG`` the silence is no longer a weekend
but a data outage, and the prediction stays pending rather than being
graded against a price from an unrelated week.

**Only a finished bar grades a call.** The outcome is the close of the
bar whose period contains the horizon (or, in a closed market, the first
bar after it), so it exists one bar *after* the horizon. The resolver
used to take the nearest earlier bar whenever that one was not stored
yet, and it runs every 15 minutes: in production 2,134 of 2,229 hourly
and 105 of 106 daily outcomes (audit 2026-10-13) were graded against the
bar before the horizon — one bar short, and itself captured mid-period.
A call now stays pending until its own bar has settled; nothing already
graded is re-graded.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mentor.domain.market.bars import Timeframe
from mentor.domain.market.settlement import (
    StoredBar,
    closes_at,
    is_settled,
    was_stored_provisional,
)
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.resolver")

# How long after the horizon we will still accept the next printed price.
# A weekend is ~50h; four days absorbs that plus a public holiday. Beyond
# it, the gap is a broken feed rather than a closed market, and grading a
# 24-hour call against a price from the following week would be fiction.
MAX_RESOLUTION_LAG = timedelta(days=4)


def outcome_bar(
    bars: Sequence[StoredBar], *, horizon_at: datetime, timeframe: Timeframe, now: datetime
) -> StoredBar | None:
    """The bar a call is graded on, or None while it cannot be known yet.

    That is the first bar still open at the horizon — the one whose period
    contains it (feeds round to bar boundaries, so a 10:05 horizon is the
    10:00 bar), or in a closed market the first bar after it. Its close is
    the price you would have got. It must have settled and must not be a
    row captured mid-period; until then the call waits rather than being
    graded on whatever earlier bar happens to be stored.
    """
    candidates = [b for b in bars if closes_at(b.ts, timeframe) > horizon_at]
    if not candidates:
        return None
    first = min(candidates, key=lambda b: b.ts)
    if not is_settled(first.ts, timeframe, now):
        return None
    if was_stored_provisional(first.ts, timeframe, first.ingested_at):
        return None  # ingestion replaces it with the settled bar shortly
    return first


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
        window_start = row.horizon_at - timedelta(seconds=tf.seconds * 2)
        window_end = row.horizon_at + MAX_RESOLUTION_LAG
        bars = await prices.range(
            symbol=row.symbol,
            timeframe=tf,
            start=window_start,
            end=window_end,
        )
        chosen = outcome_bar(bars, horizon_at=row.horizon_at, timeframe=tf, now=now)
        if chosen is None:
            still_pending += 1
            continue
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
