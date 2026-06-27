"""Curriculum catalog invariants."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from mentor.domain.curriculum import CATALOG, get_lesson
from mentor.domain.curriculum.catalog import Lesson
from mentor.domain.errors import ValidationError


def test_all_seven_plan_modules_present() -> None:
    expected = {
        "market-basics",
        "risk-first",
        "reading-charts",
        "indicators",
        "expectancy",
        "backtesting",
        "psychology",
    }
    assert {m.id for m in CATALOG} == expected


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
