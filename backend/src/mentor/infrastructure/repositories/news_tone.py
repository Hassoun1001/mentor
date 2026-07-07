"""Daily news-tone persistence (GDELT cache)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import CursorResult, and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.infrastructure.adapters.news.gdelt import DailyTone
from mentor.infrastructure.models import DailyNewsToneORM


class NewsToneRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, *, query_key: str, points: Iterable[DailyTone]) -> int:
        rows = [
            {
                "query_key": query_key,
                "day": p.day,
                "tone": Decimal(str(round(p.tone, 4))),
                "volume": Decimal(str(round(p.volume, 6))),
                "article_count": 0,
                "source": "gdelt",
            }
            for p in points
        ]
        if not rows:
            return 0
        stmt = pg_insert(DailyNewsToneORM).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["query_key", "day"],
            set_={"tone": stmt.excluded.tone, "volume": stmt.excluded.volume},
        )
        result = cast("CursorResult[Any]", await self._session.execute(stmt))
        return result.rowcount or 0

    async def series(self, *, query_key: str) -> Sequence[DailyNewsToneORM]:
        stmt = (
            select(DailyNewsToneORM)
            .where(DailyNewsToneORM.query_key == query_key)
            .order_by(DailyNewsToneORM.day.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def range(
        self, *, query_key: str, start: datetime, end: datetime
    ) -> Sequence[DailyNewsToneORM]:
        stmt = (
            select(DailyNewsToneORM)
            .where(
                and_(
                    DailyNewsToneORM.query_key == query_key,
                    DailyNewsToneORM.day >= start,
                    DailyNewsToneORM.day <= end,
                )
            )
            .order_by(DailyNewsToneORM.day.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count(self, *, query_key: str) -> int:
        rows = await self.series(query_key=query_key)
        return len(rows)
