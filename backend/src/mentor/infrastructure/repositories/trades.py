"""Trade persistence + ORM<->domain mapping."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.journal.trade import Trade, TradeStatus
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction
from mentor.infrastructure.models import JournalReflection as JournalORM
from mentor.infrastructure.models import Trade as TradeORM


def _to_orm(t: Trade) -> tuple[TradeORM, JournalORM]:
    orm = TradeORM(
        id=t.id,
        symbol=t.symbol,
        direction=t.direction.value,
        status=t.status.value,
        size_lots=t.size_lots,
        planned_entry=t.planned_entry,
        planned_stop=t.planned_stop,
        planned_target=t.planned_target,
        actual_entry=t.actual_entry,
        actual_exit=t.actual_exit,
        entry_ts=t.entry_ts,
        exit_ts=t.exit_ts,
        initial_risk_amount=t.initial_risk.amount,
        risk_currency=t.initial_risk.currency,
        realised_pnl=t.realised_pnl.amount if t.realised_pnl else None,
        realised_r=t.realised_r,
    )
    reflection = JournalORM(
        trade_id=t.id,
        reason=t.reason,
        mistake_tags=list(t.mistake_tags),
        emotion=t.emotion,
        notes=t.notes,
    )
    return orm, reflection


def _from_orm(orm: TradeORM) -> Trade:
    reflection = orm.reflection
    realised_pnl = (
        Money(orm.realised_pnl, orm.risk_currency) if orm.realised_pnl is not None else None
    )
    return Trade(
        id=orm.id,
        symbol=orm.symbol,
        direction=Direction(orm.direction),
        status=TradeStatus(orm.status),
        size_lots=Decimal(orm.size_lots),
        planned_entry=Decimal(orm.planned_entry),
        planned_stop=Decimal(orm.planned_stop),
        planned_target=(Decimal(orm.planned_target) if orm.planned_target is not None else None),
        initial_risk=Money(orm.initial_risk_amount, orm.risk_currency),
        reason=reflection.reason if reflection else "",
        actual_entry=Decimal(orm.actual_entry) if orm.actual_entry is not None else None,
        actual_exit=Decimal(orm.actual_exit) if orm.actual_exit is not None else None,
        entry_ts=orm.entry_ts,
        exit_ts=orm.exit_ts,
        realised_pnl=realised_pnl,
        realised_r=Decimal(orm.realised_r) if orm.realised_r is not None else None,
        mistake_tags=tuple(reflection.mistake_tags) if reflection else (),
        emotion=reflection.emotion if reflection else None,
        notes=reflection.notes if reflection else None,
    )


class TradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, trade: Trade) -> Trade:
        orm, reflection = _to_orm(trade)
        self._session.add(orm)
        await self._session.flush()
        self._session.add(reflection)
        await self._session.flush()
        await self._session.refresh(orm, attribute_names=["reflection"])
        return _from_orm(orm)

    async def get(self, trade_id: uuid.UUID) -> Trade | None:
        orm = await self._session.get(TradeORM, trade_id)
        return _from_orm(orm) if orm else None

    async def save(self, trade: Trade) -> Trade:
        """Persist mutations to an existing trade (state transition)."""
        orm = await self._session.get(TradeORM, trade.id)
        if orm is None:
            raise LookupError(f"trade {trade.id} not found")

        orm.status = trade.status.value
        orm.actual_entry = trade.actual_entry
        orm.actual_exit = trade.actual_exit
        orm.entry_ts = trade.entry_ts
        orm.exit_ts = trade.exit_ts
        orm.realised_pnl = trade.realised_pnl.amount if trade.realised_pnl else None
        orm.realised_r = trade.realised_r

        if orm.reflection is not None:
            orm.reflection.mistake_tags = list(trade.mistake_tags)
            orm.reflection.emotion = trade.emotion
            orm.reflection.notes = trade.notes

        await self._session.flush()
        return _from_orm(orm)

    async def list_recent(self, *, symbol: str | None = None, limit: int = 100) -> Sequence[Trade]:
        stmt = select(TradeORM).order_by(TradeORM.created_at.desc()).limit(limit)
        if symbol:
            stmt = stmt.where(TradeORM.symbol == symbol.upper())
        result = await self._session.execute(stmt)
        return [_from_orm(orm) for orm in result.scalars().all()]

    async def list_closed(self, *, symbol: str | None = None) -> Sequence[Trade]:
        stmt = select(TradeORM).where(TradeORM.status == TradeStatus.CLOSED.value)
        if symbol:
            stmt = stmt.where(TradeORM.symbol == symbol.upper())
        result = await self._session.execute(stmt)
        return [_from_orm(orm) for orm in result.scalars().all()]
