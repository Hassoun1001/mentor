"""Curriculum catalog invariants."""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mentor.domain.curriculum import CATALOG, get_lesson
from mentor.domain.curriculum.catalog import Lesson
from mentor.domain.errors import ValidationError


def test_all_plan_modules_present() -> None:
    expected = {
        "market-basics",
        "risk-first",
        "reading-charts",
        "chart-language",
        "indicators",
        "expectancy",
        "backtesting",
        "psychology",
        "market-study",
        "toolkit",
        "becoming-pro",
        "using-mentor",
        "under-the-hood",
        "market-structure",
        "candles-volume",
        "smart-money",
        "orders-conditions",
        "keeping-honest",
    }
    assert {m.id for m in CATALOG} == expected


def test_every_lesson_has_a_figure() -> None:
    missing = [lesson.slug for module in CATALOG for lesson in module.lessons if not lesson.figures]
    assert missing == []


def test_system_modules_close_the_curriculum() -> None:
    # "Under the hood" explains how the mentor predicts; "keeping-honest" follows
    # it with everything that keeps those predictions honest.
    by_order = sorted(CATALOG, key=lambda m: m.order)
    assert [m.id for m in by_order[-2:]] == ["under-the-hood", "keeping-honest"]
    assert len(by_order[-2].lessons) >= 8  # covers every prediction method
    assert len(by_order[-1].lessons) >= 8


def test_keeping_honest_lessons_all_have_a_quiz_and_a_figure() -> None:
    module = next(m for m in CATALOG if m.id == "keeping-honest")
    for lesson in module.lessons:
        assert lesson.slug.startswith("keeping-honest/"), lesson.slug
        assert lesson.module_id == "keeping-honest", lesson.slug
        assert lesson.figures, f"{lesson.slug} has no figure"
        assert len(lesson.quiz) >= 2, f"{lesson.slug} needs at least two quiz questions"
        assert "What this means for you" in lesson.body_md, lesson.slug


_FIGURE_REGISTRY = (
    Path(__file__).resolve().parents[3]
    / "frontend"
    / "src"
    / "components"
    / "lessons"
    / "LessonFigure.tsx"
)


def test_every_figure_key_has_a_frontend_diagram() -> None:
    # The frontend silently renders nothing for an unknown key, so a typo would
    # ship a lesson with an empty space where its diagram should be.
    source = _FIGURE_REGISTRY.read_text(encoding="utf-8")
    registry = source.split("const FIGURES", 1)[1]
    registered = set(re.findall(r"^\s+'?([a-z0-9-]+)'?:\s+[A-Z]\w+,$", registry, re.MULTILINE))
    used = {fig.key for module in CATALOG for lesson in module.lessons for fig in lesson.figures}
    assert used - registered == set()


def test_under_the_hood_lessons_have_figures() -> None:
    module = next(m for m in CATALOG if m.id == "under-the-hood")
    for lesson in module.lessons:
        assert lesson.figures, f"{lesson.slug} has no figure"
        for fig in lesson.figures:
            assert fig.key.strip(), f"{lesson.slug} figure key empty"
            assert fig.caption.strip(), f"{lesson.slug} figure caption empty"


def test_quiz_questions_are_well_formed() -> None:
    total = 0
    for module in CATALOG:
        for lesson in module.lessons:
            for q in lesson.quiz:
                total += 1
                assert len(q.options) >= 2
                assert 0 <= q.correct_index < len(q.options)
                assert q.prompt.strip() and q.explanation.strip()
    assert total >= 6  # at least the terminology module is quizzed


def test_chart_language_lessons_all_have_a_quiz() -> None:
    module = next(m for m in CATALOG if m.id == "chart-language")
    for lesson in module.lessons:
        assert lesson.quiz, f"{lesson.slug} missing a quiz"


def test_figure_keys_are_kebab_case() -> None:
    module = next(m for m in CATALOG if m.id == "under-the-hood")
    keys = {fig.key for lesson in module.lessons for fig in lesson.figures}
    for key in keys:
        assert key == key.lower()
        assert " " not in key and "_" not in key


def test_modules_are_ordered_uniquely() -> None:
    orders = [m.order for m in CATALOG]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(orders)


def test_lesson_slugs_are_globally_unique() -> None:
    slugs = [lesson.slug for module in CATALOG for lesson in module.lessons]
    assert len(slugs) == len(set(slugs))


def test_lessons_within_module_ordered_uniquely() -> None:
    for module in CATALOG:
        orders = [lesson.order_in_module for lesson in module.lessons]
        assert orders == sorted(orders), f"module {module.id} lessons not ordered"
        assert len(set(orders)) == len(orders)


def test_every_lesson_has_concept_tags() -> None:
    empty = [
        lesson.slug for module in CATALOG for lesson in module.lessons if not lesson.key_concepts
    ]
    assert empty == []


def test_every_lesson_has_body() -> None:
    for module in CATALOG:
        for lesson in module.lessons:
            assert lesson.body_md.strip(), f"{lesson.slug} has empty body"
            assert len(lesson.body_md) > 200, f"{lesson.slug} body too short"


def test_get_lesson_round_trips() -> None:
    first = CATALOG[0].lessons[0]
    assert get_lesson(first.slug) is first


def test_get_lesson_unknown_raises() -> None:
    with pytest.raises(ValidationError):
        get_lesson("not-a-real-slug")


def test_lesson_fields_are_frozen() -> None:
    lesson = CATALOG[0].lessons[0]
    with pytest.raises(FrozenInstanceError):
        lesson.title = "edited"  # type: ignore[misc]
    assert isinstance(lesson, Lesson)
