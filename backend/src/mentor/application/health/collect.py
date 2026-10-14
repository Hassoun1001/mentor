"""Gather the digest's inputs from the live stores.

Shared by the digest endpoint and the weekly self-report, so the two can
never disagree about whether the system is running.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from mentor.application.forecasting.economics import BREAKEVEN_LABEL, lane_breakeven
from mentor.application.forecasting.promotion import PromotionService
from mentor.application.forecasting.resolver import MAX_RESOLUTION_LAG
from mentor.application.health.digest import Digest, build_digest
from mentor.config import Settings
from mentor.domain.forecasting.forecast import Direction
from mentor.domain.market.bars import Timeframe
from mentor.domain.market.hours import fx_market_open
from mentor.domain.market.settlement import closes_at
from mentor.domain.stats.independence import select_independent
from mentor.domain.stats.significance import assess_proportion
from mentor.infrastructure.repositories import PredictionRepository, PriceBarRepository


def last_decision_at(promo: PromotionService) -> datetime | None:
    """When the lane last made a retrain decision, from its durable log."""
    history = promo.promotion_history(limit=1)
    if not history:
        return None
    raw = history[0].get("at")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


# Slack on top of the ingest and resolve cadence: a provider answering
# slowly or a job finishing late is not an outage.
_RESOLUTION_MARGIN = timedelta(minutes=30)
# A closed market lasts about 50 hours; the walk to the reopen stops well past it.
_MAX_CLOSED_HOURS = 96


def outcome_expected_by(
    horizon_at: datetime, timeframe: Timeframe, *, ingest_every: timedelta, resolve_every: timedelta
) -> datetime:
    """When a call's outcome should have been graded, if everything is running.

    The outcome is the close of the bar open at the horizon — or, in a
    closed market, of the first bar after the reopen — so it exists one bar
    after that point, is fetched at the next ingest and graded at the next
    resolve. Only after all of that is a pending call late.
    """
    ready = horizon_at
    for _ in range(_MAX_CLOSED_HOURS):
        if fx_market_open(ready):
            break
        ready += timedelta(hours=1)
    return closes_at(ready, timeframe) + ingest_every + resolve_every + _RESOLUTION_MARGIN


def _ingest_every(settings: Settings, timeframe: Timeframe) -> timedelta:
    if timeframe is Timeframe.D1:
        return timedelta(hours=settings.loop_d1_ingest_interval_hours)
    return timedelta(minutes=settings.loop_ingest_interval_minutes)


class _Pending(Protocol):
    @property
    def timeframe(self) -> str: ...
    @property
    def horizon_at(self) -> datetime: ...


def late_predictions(
    pending: Iterable[_Pending], settings: Settings, *, now: datetime
) -> tuple[int, int]:
    """``(overdue, lost)``: late but recoverable, and past the point of grading."""
    resolve_every = timedelta(minutes=settings.loop_resolve_interval_minutes)
    overdue = lost = 0
    for r in pending:
        tf = Timeframe(r.timeframe)
        if now - r.horizon_at >= MAX_RESOLUTION_LAG:
            lost += 1
        elif now > outcome_expected_by(
            r.horizon_at, tf, ingest_every=_ingest_every(settings, tf), resolve_every=resolve_every
        ):
            overdue += 1
    return overdue, lost


async def collect_digest(
    session: AsyncSession,
    settings: Settings,
    *,
    alerts_enabled: bool,
    now: datetime,
) -> Digest:
    timeframe = Timeframe(settings.loop_timeframe)

    newest = await PriceBarRepository(session).latest(
        symbol=settings.loop_symbol, timeframe=timeframe
    )

    predictions = PredictionRepository(session)
    recent = await predictions.list_recent(limit=2000)
    pending = [r for r in recent if r.realised_outcome is None]
    overdue, lost = late_predictions(pending, settings, now=now)

    # One lane only. The digest grades the record against the primary lane's
    # breakeven, and mixing in the 5-day lane's calls (a different horizon,
    # a different hurdle) graded them against a bar that isn't theirs.
    resolved = await predictions.list_resolved(limit=5000)
    independent = select_independent(
        [
            (r.asof, r.horizon_at, float(r.p_up), int(r.realised_outcome))
            for r in resolved
            if r.realised_outcome is not None
            and r.timeframe == timeframe.value
            and r.direction != Direction.NEUTRAL.value
        ]
    )
    hits = sum(
        1
        for p_up, outcome in independent
        if (p_up >= 0.5 and outcome == 1) or (p_up < 0.5 and outcome == 0)
    )
    # Graded against what a call must clear to pay for itself, not against a
    # coin flip. On the 24-bar lane that is ~51.7%, so a 51% record is "still
    # losing money", not "slightly ahead".
    basis = await lane_breakeven(session, settings=settings)
    verdict = assess_proportion(
        hits,
        len(independent),
        baseline=basis.breakeven,
        label="independent windows",
        baseline_label=BREAKEVEN_LABEL if basis.measured else "a coin flip",
    )

    return build_digest(
        window_days=7,
        # Age is measured from when the newest bar's data ends. Only settled
        # bars are stored, so its start is always at least a period old.
        newest_bar=closes_at(newest.ts, timeframe) if newest is not None else None,
        ingest_interval_minutes=settings.loop_ingest_interval_minutes,
        pending_predictions=len(pending),
        overdue_predictions=overdue,
        lost_predictions=lost,
        last_retrain=last_decision_at(PromotionService(model_store_dir=settings.model_store_dir)),
        retrain_interval_hours=settings.loop_retrain_interval_hours,
        alerts_enabled=alerts_enabled,
        independent_windows=len(independent),
        windows_needed=verdict.n_needed or 30,
        paper_verdict=verdict.verdict,
        now=now,
    )
