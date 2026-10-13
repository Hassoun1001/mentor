"""What the lab's services need from storage and from the market data.

Kept as protocols so the services are tested against an in-memory store
and fixture bars, exactly as they run against Postgres in production.
``StrategyLabRepository`` satisfies ``LabStore`` structurally.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.market.bars import Timeframe
from mentor.domain.strategy_lab.series import BarSeries
from mentor.infrastructure.models import (
    PaperPositionORM,
    PriceBar,
    StrategyCandidateORM,
    StrategyEventORM,
    StrategyTrialORM,
)
from mentor.infrastructure.repositories.price_bars import PriceBarRepository


class LabStore(Protocol):
    async def record_trials(self, rows: Sequence[StrategyTrialORM]) -> int: ...
    async def trial_count(self) -> int: ...
    async def trial_t_stats(self) -> list[float]: ...
    async def list_candidates(self) -> list[StrategyCandidateORM]: ...
    async def add_candidate(self, row: StrategyCandidateORM) -> None: ...
    async def positions(
        self,
        candidate_id: uuid.UUID,
        *,
        statuses: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[PaperPositionORM]: ...
    async def add_position(self, row: PaperPositionORM) -> None: ...
    async def add_event(self, row: StrategyEventORM) -> None: ...
    async def events_since(self, since: datetime) -> list[StrategyEventORM]: ...
    async def flush(self) -> None: ...


# (timeframe, start, now) -> the settled bars in [start, now]
BarLoader = Callable[[Timeframe, datetime, datetime], Awaitable[BarSeries]]


def settled_series(rows: Sequence[PriceBar], timeframe: Timeframe, now: datetime) -> BarSeries:
    """Bars whose period has fully elapsed by ``now``, as a lab series.

    A bar still forming has a provisional high, low and close. Signals and
    exits read only settled bars, in back-tests and live alike — the same
    rule the forecasting quality gate applies before it will predict.
    """
    cutoff = now.timestamp() - timeframe.seconds
    kept = [r for r in rows if r.ts.timestamp() <= cutoff]
    return BarSeries(
        ts=tuple(r.ts for r in kept),
        open=tuple(float(r.open) for r in kept),
        high=tuple(float(r.high) for r in kept),
        low=tuple(float(r.low) for r in kept),
        close=tuple(float(r.close) for r in kept),
    )


def sql_bar_loader(session: AsyncSession, symbol: str) -> BarLoader:
    repo = PriceBarRepository(session)

    async def load(timeframe: Timeframe, start: datetime, now: datetime) -> BarSeries:
        rows = await repo.range(symbol=symbol, timeframe=timeframe, start=start, end=now)
        return settled_series(rows, timeframe, now)

    return load
