"""Pending-prediction resolver — closes the calibration loop.

For every prediction whose horizon has elapsed (`horizon_at < now`) and
that hasn't been resolved yet, look up the realised close from the
price repository and write it back. Idempotent — runs on a schedule or
on-demand.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.resolver")


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
        # Look up the realised close — accept anything within one timeframe
        # of horizon_at (markets that round to a bar boundary).
        window_start = row.horizon_at - timedelta(seconds=tf.seconds * 2)
        window_end = row.horizon_at + timedelta(seconds=tf.seconds * 2)
        bars = await prices.range(
            symbol=row.symbol,
            timeframe=tf,
            start=window_start,
            end=window_end,
        )
        if not bars:
            still_pending += 1
            continue
        # Pick the bar closest to horizon_at (greedy nearest).
        closest = min(bars, key=lambda b: abs((b.ts - row.horizon_at).total_seconds()))
        await predictions.resolve(row.id, realised_close=closest.close, resolved_at=now)
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
