"""The building blocks of the book: parts, chapters, lessons and their sections.

Everything here is plain frozen data so the text stays reviewable in code and a
translation can be layered on by slug and field later (Arabic is the likely next
step, which is why no lesson text lives in the frontend).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from mentor.domain.curriculum.charts import Chart
from mentor.domain.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Figure:
    """A diagram shown inside a lesson.

    ``key`` names a themed SVG the frontend knows how to draw; ``caption``
    is the one-line explanation shown beneath it. Content stays code-shipped
    — the backend never sends pixels, only the key + caption.
    """

    key: str
    caption: str


@dataclass(frozen=True, slots=True)
class QuizQuestion:
    """A self-check multiple-choice question for a lesson.

    Active recall beats re-reading. ``correct_index`` points into ``options``;
    ``explanation`` is shown after the learner answers, right or wrong.
    """

    prompt: str
    options: tuple[str, ...]
    correct_index: int
    explanation: str

    def __post_init__(self) -> None:
        if len(self.options) < 2:
            raise ValidationError("a quiz question needs >= 2 options")
        if not (0 <= self.correct_index < len(self.options)):
            raise ValidationError("correct_index out of range")


class Verdict(StrEnum):
    """How well a method holds up when it is actually tested."""

    FACT = "fact"  # a definition or arithmetic: there is nothing to test
    SUPPORTED = "supported"  # repeated tested findings, still with real limits
    MIXED = "mixed"  # some tests pass, some fail, results depend on the setup
    WEAK = "weak"  # tests mostly fail, or only pass before costs
    UNTESTED = "untested"  # popular, but little or no serious testing exists


@dataclass(frozen=True, slots=True)
class Evidence:
    """The "Does it actually work?" section of a lesson."""

    verdict: Verdict
    text_md: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Lesson:
    """One lesson. ``slug`` is permanent: reading progress is keyed by it.

    Lessons written for the book fill every section. ``goal`` being empty marks
    a lesson still in its earlier-edition form, which only has ``body_md``.
    """

    slug: str
    title: str
    summary: str
    body_md: str
    est_minutes: int
    key_concepts: tuple[str, ...]
    module_id: str = ""
    order_in_module: int = 0
    figures: tuple[Figure, ...] = ()
    quiz: tuple[QuizQuestion, ...] = ()
    goal: str = ""
    charts: tuple[Chart, ...] = ()
    steps: tuple[str, ...] = ()
    example_md: str = ""
    mistakes: tuple[str, ...] = ()
    evidence: Evidence | None = None
    try_it: str = ""
    takeaways: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Module:
    """A chapter of the book. The API still calls it a module."""

    id: str
    order: int
    title: str
    summary: str
    lessons: tuple[Lesson, ...]
    part_id: str = field(default="")

    @property
    def est_minutes(self) -> int:
        return sum(lesson.est_minutes for lesson in self.lessons)


@dataclass(frozen=True, slots=True)
class Part:
    """A stage of the beginner-to-professional path."""

    id: str
    order: int
    stage: str
    title: str
    summary: str
