"""PriceBar persistence."""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.settlement import BarCorrection, StoredBar
from mentor.infrastructure.models import PriceBar as PriceBarORM
from mentor.infrastructure.models import PriceBarRevisionORM


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

    Inserting never changes a stored row. The only writes that do are
    ``apply_corrections`` and ``remove``, and both log the values they
    replace to ``price_bar_revisions`` (``revert`` puts them back). Which
    rows may be corrected is decided in ``domain/market/settlement.py``.
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

    async def provisional(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[PriceBarORM]:
        """Rows written before their period closed, oldest first, in ``[start, end)``."""
        stmt = select(PriceBarORM).where(
            PriceBarORM.symbol == symbol.upper(),
            PriceBarORM.timeframe == timeframe.value,
            PriceBarORM.ingested_at < PriceBarORM.ts + timedelta(seconds=timeframe.seconds),
        )
        if start is not None:
            stmt = stmt.where(PriceBarORM.ts >= start)
        if end is not None:
            stmt = stmt.where(PriceBarORM.ts < end)
        result = await self._session.execute(stmt.order_by(PriceBarORM.ts.asc()))
        return result.scalars().all()

    async def misaligned(self, *, symbol: str, timeframe: Timeframe) -> Sequence[PriceBarORM]:
        """Rows not stamped on their timeframe's UTC boundary, oldest first."""
        stmt = (
            select(PriceBarORM)
            .where(
                PriceBarORM.symbol == symbol.upper(),
                PriceBarORM.timeframe == timeframe.value,
                func.extract("epoch", PriceBarORM.ts) % timeframe.seconds != 0,
            )
            .order_by(PriceBarORM.ts.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def apply_corrections(
        self,
        corrections: Sequence[BarCorrection],
        *,
        batch_id: str,
        reason: str,
        now: datetime,
    ) -> int:
        """Replace provisional rows with their settled bars, logging each one.

        A row is only touched while it is still exactly what was read (same
        ``ingested_at``), so a concurrent correction is never overwritten or
        logged twice. Returns the number of rows changed.

        The revision is built *before* the update: the ORM synchronises the
        session's copy of the row, so reading it afterwards would log the
        new values as the old ones and make the change irreversible.
        """
        changed = 0
        for c in corrections:
            row, bar = c.stored, c.settled
            revision = _revision(
                row,
                symbol=bar.symbol,
                timeframe=bar.timeframe.value,
                action="corrected",
                batch_id=batch_id,
                reason=reason,
                now=now,
                new=bar,
            )
            stmt = (
                update(PriceBarORM)
                .where(
                    PriceBarORM.symbol == bar.symbol,
                    PriceBarORM.timeframe == bar.timeframe.value,
                    PriceBarORM.ts == bar.ts,
                    PriceBarORM.ingested_at == row.ingested_at,
                )
                .values(
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    source=bar.source,
                    ingested_at=now,
                )
            )
            result = cast("CursorResult[Any]", await self._session.execute(stmt))
            if not result.rowcount:
                continue
            self._session.add(revision)
            changed += 1
        await self._session.flush()
        return changed

    async def remove(
        self,
        rows: Sequence[StoredBar],
        *,
        batch_id: str,
        reason: str,
        now: datetime,
    ) -> int:
        """Delete rows no settled bar can replace, logging each one first."""
        removed = 0
        for row in rows:
            revision = _revision(
                row,
                symbol=row.symbol,
                timeframe=row.timeframe,
                action="removed",
                batch_id=batch_id,
                reason=reason,
                now=now,
                new=None,
            )
            stmt = delete(PriceBarORM).where(
                PriceBarORM.symbol == row.symbol,
                PriceBarORM.timeframe == row.timeframe,
                PriceBarORM.ts == row.ts,
                PriceBarORM.ingested_at == row.ingested_at,
            )
            result = cast("CursorResult[Any]", await self._session.execute(stmt))
            if not result.rowcount:
                continue
            self._session.add(revision)
            removed += 1
        await self._session.flush()
        return removed

    async def revisions(self, *, batch_id: str) -> Sequence[PriceBarRevisionORM]:
        stmt = (
            select(PriceBarRevisionORM)
            .where(PriceBarRevisionORM.batch_id == batch_id)
            .order_by(PriceBarRevisionORM.ts.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def revert(self, *, batch_id: str, now: datetime) -> tuple[int, int]:
        """Put back every change in a batch that has not been reverted yet.

        A corrected row is restored only while it still holds the corrected
        values, so a later change is never clobbered. Returns
        ``(restored, skipped)``.
        """
        restored = skipped = 0
        for rev in await self.revisions(batch_id=batch_id):
            if rev.reverted_at is not None:
                continue
            old = {
                "open": rev.old_open,
                "high": rev.old_high,
                "low": rev.old_low,
                "close": rev.old_close,
                "volume": rev.old_volume,
                "source": rev.old_source,
                "ingested_at": rev.old_ingested_at,
            }
            stmt: Any
            if rev.action == "corrected":
                stmt = (
                    update(PriceBarORM)
                    .where(
                        PriceBarORM.symbol == rev.symbol,
                        PriceBarORM.timeframe == rev.timeframe,
                        PriceBarORM.ts == rev.ts,
                        PriceBarORM.close == rev.new_close,
                        PriceBarORM.source == rev.new_source,
                    )
                    .values(**old)
                )
            else:
                stmt = (
                    pg_insert(PriceBarORM)
                    .values(symbol=rev.symbol, timeframe=rev.timeframe, ts=rev.ts, **old)
                    .on_conflict_do_nothing(index_elements=["symbol", "timeframe", "ts"])
                )
            result = cast("CursorResult[Any]", await self._session.execute(stmt))
            if result.rowcount:
                rev.reverted_at = now
                restored += 1
            else:
                skipped += 1
        await self._session.flush()
        return restored, skipped

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


def _revision(
    row: StoredBar,
    *,
    symbol: str,
    timeframe: str,
    action: str,
    batch_id: str,
    reason: str,
    now: datetime,
    new: PriceBar | None,
) -> PriceBarRevisionORM:
    return PriceBarRevisionORM(
        id=uuid.uuid4(),
        batch_id=batch_id,
        action=action,
        reason=reason,
        symbol=symbol,
        timeframe=timeframe,
        ts=row.ts,
        old_open=row.open,
        old_high=row.high,
        old_low=row.low,
        old_close=row.close,
        old_volume=row.volume,
        old_source=row.source,
        old_ingested_at=row.ingested_at,
        new_open=new.open if new else None,
        new_high=new.high if new else None,
        new_low=new.low if new else None,
        new_close=new.close if new else None,
        new_volume=new.volume if new else None,
        new_source=new.source if new else None,
        revised_at=now,
    )
