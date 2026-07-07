"""Macro-series persistence (FRED cache)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import CursorResult, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.infrastructure.adapters.macro.fred import MacroObservation
from mentor.infrastructure.models import MacroSeriesORM

# 4 bind params per row; keep chunks well under Postgres's 32767 cap.
_UPSERT_CHUNK = 5000


class MacroSeriesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, points: Iterable[MacroObservation]) -> int:
        rows = [
            {
                "series_id": p.series_id,
                "day": p.day,
                "value": Decimal(str(round(p.value, 6))),
                "source": "fred",
            }
            for p in points
        ]
        if not rows:
            return 0
        # Postgres caps a statement at 32767 bind params; 4 cols/row => chunk
        # well under that (a decade of daily series is ~13k rows across all).
        written = 0
        for start in range(0, len(rows), _UPSERT_CHUNK):
            chunk = rows[start : start + _UPSERT_CHUNK]
            stmt = pg_insert(MacroSeriesORM).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["series_id", "day"],
                set_={"value": stmt.excluded.value},
            )
            result = cast("CursorResult[Any]", await self._session.execute(stmt))
            written += result.rowcount or 0
        return written

    async def series(self) -> Sequence[MacroSeriesORM]:
        stmt = select(MacroSeriesORM).order_by(
            MacroSeriesORM.series_id.asc(), MacroSeriesORM.day.asc()
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def counts_by_series(self) -> dict[str, int]:
        rows = await self.series()
        out: dict[str, int] = {}
        for r in rows:
            out[r.series_id] = out.get(r.series_id, 0) + 1
        return out
