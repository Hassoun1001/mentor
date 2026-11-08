"""Saved Trade plans. Add and read only: there is deliberately no update."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.journal.system_plan import PlanSnapshot, PlanStance
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.models import TradePlanSnapshotORM


def _from_orm(orm: TradePlanSnapshotORM) -> PlanSnapshot:
    return PlanSnapshot(
        symbol=orm.symbol,
        timeframe=Timeframe(orm.timeframe),
        asof=orm.asof,
        model_name=orm.model_name,
        p_up=orm.p_up,
        confidence=orm.confidence,
        stance=PlanStance(orm.stance),
        horizon_bars=orm.horizon_bars,
        time_stop_deadline=orm.time_stop_deadline,
        entry=orm.entry,
        stop=orm.stop,
        target=orm.target,
        reward_multiple=orm.reward_multiple,
        prediction_id=orm.prediction_id,
    )


class PlanSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, trade_id: uuid.UUID, snapshot: PlanSnapshot) -> None:
        self._session.add(
            TradePlanSnapshotORM(
                trade_id=trade_id,
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe.value,
                asof=snapshot.asof,
                model_name=snapshot.model_name,
                p_up=snapshot.p_up,
                confidence=snapshot.confidence,
                stance=snapshot.stance.value,
                entry=snapshot.entry,
                stop=snapshot.stop,
                target=snapshot.target,
                reward_multiple=snapshot.reward_multiple,
                horizon_bars=snapshot.horizon_bars,
                time_stop_deadline=snapshot.time_stop_deadline,
                prediction_id=snapshot.prediction_id,
            )
        )
        await self._session.flush()

    async def for_trades(self, trade_ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, PlanSnapshot]:
        if not trade_ids:
            return {}
        stmt = select(TradePlanSnapshotORM).where(TradePlanSnapshotORM.trade_id.in_(trade_ids))
        rows = (await self._session.execute(stmt)).scalars().all()
        return {row.trade_id: _from_orm(row) for row in rows}
