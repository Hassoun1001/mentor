"""Curriculum catalog invariants."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

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
        "under-the-hood",
    }
    assert {m.id for m in CATALOG} == expected


def test_every_lesson_has_a_figure() -> None:
    missing = [
        lesson.slug for module in CATALOG for lesson in module.lessons if not lesson.figures
    ]
    assert missing == []


def test_under_the_hood_module_is_last() -> None:
    last = max(CATALOG, key=lambda m: m.order)
    assert last.id == "under-the-hood"
    assert len(last.lessons) >= 8  # covers every prediction method


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
