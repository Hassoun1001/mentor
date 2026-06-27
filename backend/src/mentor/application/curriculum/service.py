"""Curriculum use cases."""

from __future__ import annotations

from dataclasses import dataclass

from mentor.domain.curriculum import (
    CATALOG,
    Lesson,
    Module,
    get_lesson,
    list_modules,
)
from mentor.domain.curriculum.progress import LessonProgress, LessonStatus
from mentor.infrastructure.repositories.lesson_progress import LessonProgressRepository


@dataclass(frozen=True, slots=True)
class LessonWithProgress:
    lesson: Lesson
    progress: LessonProgress | None


@dataclass(frozen=True, slots=True)
class ModuleWithProgress:
    module: Module
    lessons: tuple[LessonWithProgress, ...]
    completed_count: int

    @property
    def total_count(self) -> int:
        return len(self.lessons)

    @property
    def is_complete(self) -> bool:
        return self.completed_count == self.total_count and self.total_count > 0


class CurriculumService:
    def __init__(self, progress_repo: LessonProgressRepository) -> None:
        self._progress = progress_repo

    async def overview(self) -> list[ModuleWithProgress]:
        progress = {p.lesson_slug: p for p in await self._progress.all()}
        out: list[ModuleWithProgress] = []
        for module in list_modules():
            with_progress = tuple(
                LessonWithProgress(lesson=lesson, progress=progress.get(lesson.slug))
                for lesson in module.lessons
            )
            completed = sum(
                1
                for lp in with_progress
                if lp.progress and lp.progress.status is LessonStatus.COMPLETED
            )
            out.append(
                ModuleWithProgress(
                    module=module,
                    lessons=with_progress,
                    completed_count=completed,
                )
            )
        return out

    async def get(self, slug: str) -> LessonWithProgress:
        lesson = get_lesson(slug)
        progress = await self._progress.get(slug)
        return LessonWithProgress(lesson=lesson, progress=progress)

    async def mark(self, slug: str, status: LessonStatus) -> LessonProgress:
        # Touching also validates the slug — raises if unknown.
        get_lesson(slug)
        return await self._progress.upsert(slug=slug, status=status)

    @staticmethod
    def total_lessons() -> int:
        return sum(len(m.lessons) for m in CATALOG)
