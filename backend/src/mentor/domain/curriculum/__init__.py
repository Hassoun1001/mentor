"""Curriculum domain — Phase 2.

> A structured lesson tree from market basics to backtesting and psychology,
> with progress tracking.   — Mentor product plan, §6.A

Lesson content is code-shipped (immutable, version-controlled, reviewable in
PRs). The user-mutable piece — progress — is the only thing in the database.
This makes lessons trivially reproducible: clone the repo and you have the
whole curriculum, no migration step required.
"""

from mentor.domain.curriculum.atlas import ATLAS, USAGE_NOTE
from mentor.domain.curriculum.catalog import (
    CATALOG,
    SearchHit,
    get_lesson,
    lessons_in_part,
    list_modules,
    list_parts,
    search_lessons,
)
from mentor.domain.curriculum.glossary import GLOSSARY, GlossaryTerm
from mentor.domain.curriculum.model import Lesson, Module, Part
from mentor.domain.curriculum.progress import LessonProgress, LessonStatus
from mentor.domain.curriculum.sources import SOURCES, Source

__all__ = [
    "ATLAS",
    "CATALOG",
    "GLOSSARY",
    "SOURCES",
    "USAGE_NOTE",
    "GlossaryTerm",
    "Lesson",
    "LessonProgress",
    "LessonStatus",
    "Module",
    "Part",
    "SearchHit",
    "Source",
    "get_lesson",
    "lessons_in_part",
    "list_modules",
    "list_parts",
    "search_lessons",
]
