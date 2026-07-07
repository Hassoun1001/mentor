"""PriceBar persistence."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.models import PriceBar as PriceBarORM


@dataclass(frozen=True, slots=True)
class CoverageRow:
    timeframe: str
    bars: int
    first_ts: datetime | None
    last_ts: datetime | None
    sources: dict[str, int]


class PriceBarRepository:
    """All access to the price_bars hypertable goes through here.

    Uses Postgres' `INSERT … ON CONFLICT DO NOTHING` so the ingestion
    worker can re-fetch overlapping ranges without exploding on duplicate
    keys — idempotency is a hard requirement of the ingestion design.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_many(self, bars: Iterable[PriceBar]) -> int:
        rows = [
            {
                "symbol": b.symbol,
                "timeframe": b.timeframe.value,
                "ts": b.ts,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
                "source": b.source,
            }
            for b in bars
        ]
        if not rows:
            return 0
        stmt = (
            pg_insert(PriceBarORM)
            .values(rows)
            .on_conflict_do_nothing(
                index_elements=["symbol", "timeframe", "ts"],
            )
        )
        result = cast("CursorResult[Any]", await self._session.execute(stmt))
        return result.rowcount or 0

    async def range(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> Sequence[PriceBarORM]:
        stmt = (
            select(PriceBarORM)
            .where(
                PriceBarORM.symbol == symbol.upper(),
                PriceBarORM.timeframe == timeframe.value,
                PriceBarORM.ts >= start,
                PriceBarORM.ts < end,
            )
            .order_by(PriceBarORM.ts.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def coverage(self, *, symbol: str) -> list[CoverageRow]:
        """Per-timeframe bar counts, date span, and per-source breakdown —
        the "how much data do I actually have, and where from" summary."""
        agg = select(
            PriceBarORM.timeframe,
            func.count().label("bars"),
            func.min(PriceBarORM.ts).label("first_ts"),
            func.max(PriceBarORM.ts).label("last_ts"),
        ).where(PriceBarORM.symbol == symbol.upper()).group_by(PriceBarORM.timeframe)
        agg_rows = (await self._session.execute(agg)).all()

        src = select(
            PriceBarORM.timeframe,
            PriceBarORM.source,
            func.count().label("n"),
        ).where(PriceBarORM.symbol == symbol.upper()).group_by(
            PriceBarORM.timeframe, PriceBarORM.source
        )
        by_source: dict[str, dict[str, int]] = {}
        for tf, source, n in (await self._session.execute(src)).all():
            by_source.setdefault(tf, {})[source] = int(n)

        out = [
            CoverageRow(
                timeframe=r.timeframe,
                bars=int(r.bars),
                first_ts=r.first_ts,
                last_ts=r.last_ts,
                sources=by_source.get(r.timeframe, {}),
            )
            for r in agg_rows
        ]
        # Stable ordering by typical granularity.
        order = {tf.value: i for i, tf in enumerate(Timeframe)}
        out.sort(key=lambda c: order.get(c.timeframe, 99))
        return out

    async def latest(self, *, symbol: str, timeframe: Timeframe) -> PriceBarORM | None:
        stmt = (
            select(PriceBarORM)
            .where(
                PriceBarORM.symbol == symbol.upper(),
                PriceBarORM.timeframe == timeframe.value,
            )
            .order_by(PriceBarORM.ts.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
