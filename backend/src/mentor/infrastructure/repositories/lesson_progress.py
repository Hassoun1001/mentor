"""LessonProgress persistence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.domain.curriculum.progress import LessonProgress, LessonStatus
from mentor.infrastructure.models import LessonProgress as LessonProgressORM


def _from_orm(orm: LessonProgressORM) -> LessonProgress:
    return LessonProgress(
        lesson_slug=orm.lesson_slug,
        status=LessonStatus(orm.status),
        last_seen_at=orm.last_seen_at,
        completed_at=orm.completed_at,
    )


class LessonProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, slug: str) -> LessonProgress | None:
        orm = await self._session.get(LessonProgressORM, slug)
        return _from_orm(orm) if orm else None

    async def all(self) -> list[LessonProgress]:
        result = await self._session.execute(select(LessonProgressORM))
        return [_from_orm(o) for o in result.scalars().all()]

    async def upsert(self, *, slug: str, status: LessonStatus) -> LessonProgress:
        now = datetime.now(UTC)
        completed_at = now if status is LessonStatus.COMPLETED else None
        values = {
            "lesson_slug": slug,
            "status": status.value,
            "last_seen_at": now,
            "completed_at": completed_at,
            "updated_at": now,
        }
        stmt = (
            pg_insert(LessonProgressORM)
            .values(values)
            .on_conflict_do_update(
                index_elements=["lesson_slug"],
                set_={
                    "status": status.value,
                    "last_seen_at": now,
                    "completed_at": completed_at,
                    "updated_at": now,
                },
            )
        )
        await self._session.execute(stmt)
        orm = await self._session.get(LessonProgressORM, slug)
        assert orm is not None
        return _from_orm(orm)
