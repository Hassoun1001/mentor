"""Curriculum domain — Phase 2.

> A structured lesson tree from market basics to backtesting and psychology,
> with progress tracking.   — Mentor product plan, §6.A

Lesson content is code-shipped (immutable, version-controlled, reviewable in
PRs). The user-mutable piece — progress — is the only thing in the database.
This makes lessons trivially reproducible: clone the repo and you have the
whole curriculum, no migration step required.
"""

from mentor.domain.curriculum.catalog import (
    CATALOG,
    Lesson,
    Module,
    get_lesson,
    list_modules,
)
from mentor.domain.curriculum.progress import LessonProgress, LessonStatus

__all__ = [
    "CATALOG",
    "Lesson",
    "LessonProgress",
    "LessonStatus",
    "Module",
    "get_lesson",
    "list_modules",
]
