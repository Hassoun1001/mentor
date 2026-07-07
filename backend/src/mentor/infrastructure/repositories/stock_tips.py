"""Stock-tip persistence."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.infrastructure.models import StockTipORM


class StockTipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        tipster: str,
        ticker: str,
        category: str,
        action: str,
        conviction: str,
        note: str,
        raw_message: str,
        mentioned_at: datetime,
        mention_price: Decimal | None,
    ) -> uuid.UUID:
        tip_id = uuid.uuid4()
        self._session.add(
            StockTipORM(
                id=tip_id,
                tipster=tipster,
                ticker=ticker.upper(),
                category=category,
                action=action,
                conviction=conviction,
                note=note,
                raw_message=raw_message,
                mentioned_at=mentioned_at,
                mention_price=mention_price,
            )
        )
        await self._session.flush()
        return tip_id

    async def list_all(
        self, *, tipster: str | None = None, limit: int = 500
    ) -> Sequence[StockTipORM]:
        stmt = select(StockTipORM).order_by(StockTipORM.mentioned_at.desc()).limit(limit)
        if tipster:
            stmt = stmt.where(StockTipORM.tipster == tipster)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def tipsters(self) -> list[str]:
        stmt = select(StockTipORM.tipster).distinct()
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]
