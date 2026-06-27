"""Economic-event persistence."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.calendar.adapter import RawEconomicEvent
from mentor.domain.calendar.event import EconomicEvent, ImpactLevel
from mentor.infrastructure.models import EconomicEventORM


def _to_domain(orm: EconomicEventORM) -> EconomicEvent:
    return EconomicEvent(
        id=orm.id,
        source=orm.source,
        ts=orm.ts,
        name=orm.name,
        country=orm.country,
        impact=ImpactLevel(orm.impact),
        forecast=orm.forecast,
        previous=orm.previous,
        actual=orm.actual,
    )


class EconomicEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_raw(self, items: Iterable[RawEconomicEvent]) -> int:
        rows = [
            {
                "id": uuid.uuid4(),
                "source": item.source,
                "external_id": item.external_id,
                "ts": item.ts,
                "name": item.name,
                "country": item.country,
                "impact": int(item.impact),
                "forecast": item.forecast,
                "previous": item.previous,
                "actual": item.actual,
            }
            for item in items
        ]
        if not rows:
            return 0
        stmt = (
            pg_insert(EconomicEventORM)
            .values(rows)
            .on_conflict_do_update(
                index_elements=["external_id"],
                set_={
                    "actual": pg_insert(EconomicEventORM).excluded.actual,
                    "forecast": pg_insert(EconomicEventORM).excluded.forecast,
                    "previous": pg_insert(EconomicEventORM).excluded.previous,
                    "updated_at": pg_insert(EconomicEventORM).excluded.updated_at,
                },
            )
        )
        result = cast("CursorResult[Any]", await self._session.execute(stmt))
        return result.rowcount or 0

    async def range(
        self,
        *,
        start: datetime,
        end: datetime,
        min_impact: ImpactLevel | None = None,
    ) -> list[EconomicEvent]:
        stmt = select(EconomicEventORM).where(
            and_(EconomicEventORM.ts >= start, EconomicEventORM.ts <= end)
        )
        if min_impact is not None:
            stmt = stmt.where(EconomicEventORM.impact >= int(min_impact))
        stmt = stmt.order_by(EconomicEventORM.ts.asc())
        result = await self._session.execute(stmt)
        return [_to_domain(o) for o in result.scalars().all()]
