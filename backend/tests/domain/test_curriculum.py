"""Curriculum catalog invariants."""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mentor.domain.curriculum import (
    CATALOG,
    GLOSSARY,
    SOURCES,
    get_lesson,
    lessons_in_part,
    list_parts,
    search_lessons,
)
from mentor.domain.curriculum.book import PARTS
from mentor.domain.curriculum.model import Lesson
from mentor.domain.curriculum.sources import SOURCE_KEYS
from mentor.domain.errors import ValidationError

# Every slug of the first edition (88 lessons, 18 modules). Reading progress is
# stored against these, so they must stay reachable for good.
FIRST_EDITION_SLUGS = (
    "market-basics/what-you-are-trading",
    "market-basics/lots-pips-leverage",
    "market-basics/spread-is-your-first-expense",
    "risk-first/why-risk-beats-prediction",
    "risk-first/the-one-percent-rule",
    "risk-first/size-from-your-stop",
    "risk-first/account-guardrails",
    "risk-first/managing-the-open-trade",
    "reading-charts/trend-and-obvious-patterns",
    "reading-charts/support-resistance",
    "reading-charts/candlesticks",
    "chart-language/direction-words",
    "chart-language/trend-structure",
    "chart-language/moves-within-a-trend",
    "chart-language/candles-vocabulary",
    "chart-language/fibonacci-and-levels",
    "chart-language/units-and-orders",
    "market-structure/direction-and-trend",
    "market-structure/price-action-moves",
    "market-structure/swings-bos-choch",
    "candles-volume/candlestick-zoo",
    "candles-volume/volume-and-profile",
    "smart-money/what-smc-is",
    "smart-money/liquidity-sweeps-stophunts",
    "smart-money/blocks-fvg-premium",
    "indicators/moving-averages",
    "indicators/rsi-and-the-overbought-trap",
    "indicators/atr-and-volatility",
    "orders-conditions/order-types-reference",
    "orders-conditions/market-conditions",
    "expectancy/the-math-of-survival",
    "expectancy/r-multiples",
    "expectancy/why-low-win-rate-can-be-profitable",
    "backtesting/lookahead-bias",
    "backtesting/overfitting",
    "backtesting/transaction-costs",
    "psychology/journaling-beats-memory",
    "psychology/tilt",
    "psychology/weekend-review",
    "psychology/process-goals",
    "psychology/learning-from-losses",
    "market-study/schools-of-analysis",
    "market-study/top-down-workflow",
    "market-study/building-an-edge",
    "market-study/what-actually-predicts",
    "market-study/probabilistic-thinking",
    "toolkit/charts-and-platforms",
    "toolkit/data-and-calendars",
    "toolkit/risk-and-journaling-tools",
    "toolkit/screening-and-automation",
    "toolkit/weekly-workflow",
    "becoming-pro/order-types",
    "becoming-pro/sessions-clock",
    "becoming-pro/costs-of-trading",
    "becoming-pro/leverage-and-margin",
    "becoming-pro/the-trading-plan",
    "becoming-pro/daily-routine",
    "becoming-pro/from-demo-to-real",
    "using-mentor/a-day-with-mentor",
    "using-mentor/reading-the-trade-ticket",
    "using-mentor/trusting-the-odds",
    "using-mentor/watching-the-loop",
    "using-mentor/close-your-own-loop",
    "using-mentor/whole-system-plain-english",
    "using-mentor/every-tab-trading",
    "using-mentor/every-tab-toolkit",
    "under-the-hood/what-we-can-predict",
    "under-the-hood/where-the-data-comes-from",
    "under-the-hood/what-the-model-sees",
    "under-the-hood/predicting-direction",
    "under-the-hood/predicting-the-range",
    "under-the-hood/trustworthy-probabilities",
    "under-the-hood/the-self-learning-loop",
    "under-the-hood/forecast-to-position-size",
    "under-the-hood/tracking-tipsters",
    "under-the-hood/the-watchdogs",
    "under-the-hood/knowing-when-to-say-nothing",
    "keeping-honest/the-cost-hurdle",
    "keeping-honest/abstaining-by-profit",
    "keeping-honest/honest-win-rates",
    "keeping-honest/new-data-sources",
    "keeping-honest/learning-from-live-mistakes",
    "keeping-honest/finished-bars",
    "keeping-honest/strategy-lab-testing",
    "keeping-honest/the-rising-bar",
    "keeping-honest/running-unattended",
    "keeping-honest/the-safety-net",
    "keeping-honest/what-it-can-and-cannot-do",
)

ALL_LESSONS = tuple(lesson for module in CATALOG for lesson in module.lessons)
BOOK_LESSONS = tuple(lesson for lesson in ALL_LESSONS if lesson.goal)


def test_no_first_edition_lesson_is_lost() -> None:
    assert len(FIRST_EDITION_SLUGS) == 88
    assert set(FIRST_EDITION_SLUGS) <= {lesson.slug for lesson in ALL_LESSONS}


def test_lesson_map_lists_every_first_edition_lesson() -> None:
    lesson_map = Path(__file__).resolve().parents[3] / "docs" / "learn" / "LESSON_MAP.md"
    text = lesson_map.read_text(encoding="utf-8")
    missing = [slug for slug in FIRST_EDITION_SLUGS if slug not in text]
    assert missing == []


def test_book_lessons_have_every_section() -> None:
    assert BOOK_LESSONS
    for lesson in BOOK_LESSONS:
        assert lesson.goal.strip(), lesson.slug
        assert len(lesson.body_md) > 200, f"{lesson.slug} body too short"
        assert len(lesson.steps) >= 2, f"{lesson.slug} needs step-by-step guidance"
        assert lesson.example_md.strip(), f"{lesson.slug} missing worked example"
        assert lesson.mistakes, f"{lesson.slug} missing common mistakes"
        assert lesson.evidence is not None, f"{lesson.slug} missing the evidence section"
        assert lesson.evidence.text_md.strip(), lesson.slug
        assert lesson.try_it.strip(), f"{lesson.slug} missing the exercise"
        assert lesson.quiz, f"{lesson.slug} missing a quiz"
        assert lesson.takeaways, f"{lesson.slug} missing takeaways"
        assert lesson.key_concepts, f"{lesson.slug} missing concept tags"


def test_every_book_lesson_has_a_chart_or_figure() -> None:
    missing = [lesson.slug for lesson in BOOK_LESSONS if not (lesson.charts or lesson.figures)]
    assert missing == []


def test_charts_declare_honest_data_labels_and_are_well_formed() -> None:
    for lesson in BOOK_LESSONS:
        for chart in lesson.charts:
            assert chart.title.strip() and chart.caption.strip(), lesson.slug
            assert chart.data_kind in {"illustrative", "calculated", "published"}, lesson.slug
            if chart.data_kind == "published":
                assert chart.source_note.strip(), f"{lesson.slug} published chart needs a source"
            if chart.kind == "candles":
                assert chart.candles, f"{lesson.slug} has an empty candle chart"
                for open_, high, low, close in chart.candles:
                    assert high >= max(open_, close) - 1e-9, lesson.slug
                    assert low <= min(open_, close) + 1e-9, lesson.slug
            if chart.kind == "bars":
                assert chart.bars, f"{lesson.slug} has an empty bar chart"
            if chart.kind == "lines":
                assert chart.series, f"{lesson.slug} has an empty line chart"


def test_lesson_sources_exist() -> None:
    for lesson in BOOK_LESSONS:
        assert set(lesson.sources) <= SOURCE_KEYS, lesson.slug


def test_sources_and_glossary_are_populated() -> None:
    assert len(SOURCES) >= 40
    assert all(source.url.startswith("http") for source in SOURCES)
    assert len({source.key for source in SOURCES}) == len(SOURCES)
    assert len(GLOSSARY) >= 60
    terms = [term.term.lower() for term in GLOSSARY]
    assert terms == sorted(terms)


def test_no_guaranteed_profit_language() -> None:
    banned = re.compile(
        r"guaranteed profit|risk[- ]free profit|can.t lose|cannot lose|sure thing", re.I
    )
    for lesson in BOOK_LESSONS:
        for text in (lesson.body_md, lesson.example_md, lesson.try_it, *lesson.takeaways):
            assert not banned.search(text), lesson.slug


def test_every_chapter_belongs_to_a_known_part() -> None:
    part_ids = {part.id for part in list_parts()}
    for module in CATALOG:
        assert module.part_id in part_ids, module.id


def test_parts_cover_the_whole_book_in_order() -> None:
    assert [part.order for part in PARTS] == sorted(part.order for part in PARTS)
    for part in list_parts():
        assert lessons_in_part(part.id), part.id


def test_search_finds_lessons_and_ranks_titles_first() -> None:
    hits = search_lessons("spread")
    assert hits
    assert "spread" in hits[0].lesson.title.lower()
    assert search_lessons("x") == ()
    assert search_lessons("qqqzzz") == ()


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
    used = {fig.key for lesson in ALL_LESSONS for fig in lesson.figures}
    assert used - registered == set()


def test_quiz_questions_are_well_formed() -> None:
    total = 0
    for lesson in ALL_LESSONS:
        for q in lesson.quiz:
            total += 1
            assert len(q.options) >= 2
            assert 0 <= q.correct_index < len(q.options)
            assert q.prompt.strip() and q.explanation.strip()
    assert total >= 67  # the first edition had 67 questions: never fewer


def test_modules_are_ordered_uniquely() -> None:
    orders = [m.order for m in CATALOG]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(orders)


def test_lesson_slugs_are_globally_unique() -> None:
    slugs = [lesson.slug for lesson in ALL_LESSONS]
    assert len(slugs) == len(set(slugs))


def test_lessons_within_module_ordered_uniquely() -> None:
    for module in CATALOG:
        orders = [lesson.order_in_module for lesson in module.lessons]
        assert orders == sorted(orders), f"module {module.id} lessons not ordered"
        assert len(set(orders)) == len(orders)


def test_slug_fits_the_progress_column() -> None:
    assert all(len(lesson.slug) <= 128 for lesson in ALL_LESSONS)


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
