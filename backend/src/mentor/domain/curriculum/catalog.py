"""The book: every part, chapter and lesson the Learn section serves.

Modules and lessons are defined as immutable Python objects so the content is
reviewed in code, the build is deterministic, and seeding the database is a
no-op. A chapter is added in ``mentor.domain.curriculum.book``.

Lesson slugs are permanent. Progress is stored against them, so a lesson can
move to a different chapter but its slug never changes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final

from mentor.domain.curriculum.book import BOOK_MODULES, PARTS
from mentor.domain.curriculum.legacy import LEGACY_MODULES
from mentor.domain.curriculum.model import Lesson, Module, Part
from mentor.domain.errors import ValidationError

EARLIER_EDITION_PART: Final[Part] = Part(
    id="earlier-edition",
    order=99,
    stage="Being rewritten",
    title="Earlier edition",
    summary=(
        "Lessons from the first version of Learn that have not yet been rewritten for the "
        "book. Your progress on them is safe."
    ),
)


def _assemble() -> tuple[Module, ...]:
    """Number the chapters in reading order and append anything not yet rewritten."""
    book_slugs = {lesson.slug for module in BOOK_MODULES for lesson in module.lessons}
    placed = [
        replace(
            module,
            order=number,
            lessons=tuple(
                replace(lesson, module_id=module.id, order_in_module=position)
                for position, lesson in enumerate(module.lessons, start=1)
            ),
        )
        for number, module in enumerate(BOOK_MODULES, start=1)
    ]
    for module in LEGACY_MODULES:
        waiting = tuple(lesson for lesson in module.lessons if lesson.slug not in book_slugs)
        if waiting:
            placed.append(
                replace(
                    module,
                    order=len(placed) + 1,
                    part_id=EARLIER_EDITION_PART.id,
                    lessons=waiting,
                )
            )
    return tuple(placed)


CATALOG: Final[tuple[Module, ...]] = _assemble()

_BY_SLUG: Final[dict[str, Lesson]] = {
    lesson.slug: lesson for module in CATALOG for lesson in module.lessons
}


def list_modules() -> tuple[Module, ...]:
    return CATALOG


def list_parts() -> tuple[Part, ...]:
    used = {module.part_id for module in CATALOG}
    return tuple(part for part in (*PARTS, EARLIER_EDITION_PART) if part.id in used)


def get_lesson(slug: str) -> Lesson:
    try:
        return _BY_SLUG[slug]
    except KeyError as exc:
        raise ValidationError(f"unknown lesson slug: {slug}") from exc


def lessons_in_part(part_id: str) -> tuple[Lesson, ...]:
    return tuple(
        lesson for module in CATALOG if module.part_id == part_id for lesson in module.lessons
    )


@dataclass(frozen=True, slots=True)
class SearchHit:
    lesson: Lesson
    snippet: str


def _searchable(lesson: Lesson) -> str:
    evidence = lesson.evidence.text_md if lesson.evidence else ""
    return " ".join(
        (
            lesson.title,
            lesson.summary,
            lesson.goal,
            lesson.body_md,
            " ".join(lesson.steps),
            lesson.example_md,
            " ".join(lesson.mistakes),
            evidence,
            " ".join(lesson.key_concepts),
        )
    )


def _snippet(text: str, term: str, *, radius: int = 70) -> str:
    flat = " ".join(text.split())
    at = flat.lower().find(term)
    if at < 0:
        return flat[: radius * 2]
    begin = max(at - radius, 0)
    end = min(at + len(term) + radius, len(flat))
    return ("…" if begin else "") + flat[begin:end] + ("…" if end < len(flat) else "")


def search_lessons(query: str, *, limit: int = 30) -> tuple[SearchHit, ...]:
    """Lessons containing every word of ``query``. Title matches rank first."""
    terms = [term for term in query.lower().split() if len(term) > 1]
    if not terms:
        return ()
    scored: list[tuple[int, int, SearchHit]] = []
    for index, lesson in enumerate(_BY_SLUG.values()):
        text = _searchable(lesson)
        lowered = text.lower()
        if not all(term in lowered for term in terms):
            continue
        title = lesson.title.lower()
        title_hits = sum(1 for term in terms if term in title)
        snippet = _snippet(text, terms[0])
        scored.append((-title_hits, index, SearchHit(lesson=lesson, snippet=snippet)))
    scored.sort(key=lambda item: (item[0], item[1]))
    return tuple(item[2] for item in scored[:limit])
