"""Strategy-lab persistence: trial ledger, candidates, paper positions, events.

The trial ledger has an insert and two reads, and nothing else — no update,
no delete. That absence is the feature: the multiple-testing bar is
computed from this table, and a ledger that could forget its failures
could be talked into a lower bar.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.infrastructure.models import (
    PaperPositionORM,
    StrategyCandidateORM,
    StrategyEventORM,
    StrategyTrialORM,
)


class StrategyLabRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- the trial ledger (append-only) ----

    async def record_trials(self, rows: Sequence[StrategyTrialORM]) -> int:
        """Insert trials; a configuration already in the ledger is not counted twice."""
        if not rows:
            return 0
        values = [
            {
                "id": uuid.uuid4(),
                "config_key": r.config_key,
                "candidate_key": r.candidate_key,
                "family": r.family,
                "timeframe": r.timeframe,
                "params_json": r.params_json,
                "n_trades": r.n_trades,
                "mean_r": r.mean_r,
                "sd_r": r.sd_r,
                "t_stat": r.t_stat,
                "dev_start": r.dev_start,
                "dev_end": r.dev_end,
            }
            for r in rows
        ]
        stmt = (
            pg_insert(StrategyTrialORM)
            .values(values)
            .on_conflict_do_nothing(index_elements=["config_key"])
        )
        result = cast("CursorResult[Any]", await self._session.execute(stmt))
        return result.rowcount or 0

    async def trial_count(self) -> int:
        n = await self._session.scalar(select(func.count()).select_from(StrategyTrialORM))
        return int(n or 0)

    async def trial_t_stats(self) -> list[float]:
        rows = await self._session.execute(
            select(StrategyTrialORM.t_stat).where(StrategyTrialORM.n_trades >= 2)
        )
        return [float(t) for (t,) in rows.all()]

    # ---- candidates ----

    async def list_candidates(self) -> list[StrategyCandidateORM]:
        result = await self._session.execute(
            select(StrategyCandidateORM).order_by(StrategyCandidateORM.evaluated_at.asc())
        )
        return list(result.scalars().all())

    async def add_candidate(self, row: StrategyCandidateORM) -> None:
        self._session.add(row)
        await self._session.flush()

    # ---- paper positions ----

    async def positions(
        self,
        candidate_id: uuid.UUID,
        *,
        statuses: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[PaperPositionORM]:
        """Newest signal first."""
        stmt = select(PaperPositionORM).where(PaperPositionORM.candidate_id == candidate_id)
        if statuses is not None:
            stmt = stmt.where(PaperPositionORM.status.in_(list(statuses)))
        stmt = stmt.order_by(PaperPositionORM.signal_ts.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_position(self, row: PaperPositionORM) -> None:
        self._session.add(row)
        await self._session.flush()

    # ---- history ----

    async def add_event(self, row: StrategyEventORM) -> None:
        self._session.add(row)
        await self._session.flush()

    async def events_since(self, since: datetime) -> list[StrategyEventORM]:
        result = await self._session.execute(
            select(StrategyEventORM)
            .where(StrategyEventORM.at >= since)
            .order_by(StrategyEventORM.at.desc())
        )
        return list(result.scalars().all())

    async def flush(self) -> None:
        await self._session.flush()
