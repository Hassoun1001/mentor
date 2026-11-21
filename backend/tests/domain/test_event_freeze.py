"""Event-freeze evaluator tests.

The freeze is the discipline circuit-breaker the new-trade form consults
before a trade is planned. It had no direct tests: these pin the window
edges, the impact floor, the hard/soft split, the hype exclusion and which
of several nearby events is reported.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.alerts import evaluate_event_freeze
from mentor.domain.calendar.event import EconomicEvent, ImpactLevel
from mentor.domain.news.classifier import NewsCategory, NewsClassification
from mentor.domain.news.item import NewsItem

NOW = datetime(2026, 11, 18, 13, 30, tzinfo=UTC)


def _news(
    *,
    minutes: int,
    impact: str,
    category: NewsCategory = NewsCategory.MACRO,
    headline: str = "ECB signals a pause",
    classified: bool = True,
) -> NewsItem:
    classification = (
        NewsClassification(
            category=category,
            impact=Decimal(impact),
            confidence=Decimal("0.8"),
            rationale="test",
        )
        if classified
        else None
    )
    return NewsItem(
        id=uuid.uuid4(),
        source="test",
        url="https://example.invalid/item",
        ts=NOW + timedelta(minutes=minutes),
        headline=headline,
        summary=None,
        classification=classification,
    )


def _event(*, minutes: int, impact: ImpactLevel, name: str = "Nonfarm Payrolls") -> EconomicEvent:
    return EconomicEvent(
        id=uuid.uuid4(),
        source="test",
        ts=NOW + timedelta(minutes=minutes),
        name=name,
        country="US",
        impact=impact,
        forecast=None,
        previous=None,
        actual=None,
    )


def test_nothing_nearby_does_not_trigger() -> None:
    window = evaluate_event_freeze(now=NOW)
    assert not window.triggered
    assert window.upcoming_count == 0
    assert window.blocking_reason is None
    assert window.source is None
    assert window.label == "no high-impact event in window"


def test_window_edges_are_inclusive_and_outside_is_ignored() -> None:
    inside = [_news(minutes=30, impact="0.7"), _news(minutes=-30, impact="0.7")]
    outside = [_news(minutes=31, impact="0.95"), _news(minutes=-31, impact="0.95")]

    assert evaluate_event_freeze(now=NOW, upcoming=inside).upcoming_count == 2
    assert not evaluate_event_freeze(now=NOW, upcoming=outside).triggered


def test_custom_window_widths_are_respected() -> None:
    later = [_news(minutes=45, impact="0.7")]
    assert not evaluate_event_freeze(now=NOW, upcoming=later).triggered
    assert evaluate_event_freeze(now=NOW, upcoming=later, minutes_before=60).triggered
    earlier = [_news(minutes=-45, impact="0.7")]
    assert not evaluate_event_freeze(now=NOW, upcoming=earlier, minutes_before=60).triggered
    assert evaluate_event_freeze(now=NOW, upcoming=earlier, minutes_after=60).triggered


def test_news_below_impact_floor_or_unclassified_is_ignored() -> None:
    items = [
        _news(minutes=5, impact="0.59"),
        _news(minutes=5, impact="0.99", classified=False),
    ]
    assert not evaluate_event_freeze(now=NOW, upcoming=items).triggered
    # The floor itself counts.
    assert evaluate_event_freeze(now=NOW, upcoming=[_news(minutes=5, impact="0.6")]).triggered


def test_hype_is_ignored_regardless_of_impact() -> None:
    hype = [_news(minutes=0, impact="1", category=NewsCategory.HYPE)]
    assert not evaluate_event_freeze(now=NOW, upcoming=hype).triggered


def test_impact_below_block_threshold_is_a_soft_warning() -> None:
    window = evaluate_event_freeze(now=NOW, upcoming=[_news(minutes=10, impact="0.84")])
    assert window.triggered
    assert window.soft
    assert window.source == "news"
    assert window.label.startswith("Warning: macro — impact 0.84")
    assert '"ECB signals a pause"' in window.label


def test_impact_at_block_threshold_is_a_hard_block() -> None:
    window = evaluate_event_freeze(now=NOW, upcoming=[_news(minutes=10, impact="0.85")])
    assert window.triggered
    assert not window.soft
    assert window.label.startswith("Blocked: ")


def test_high_impact_calendar_release_blocks() -> None:
    window = evaluate_event_freeze(
        now=NOW, upcoming_events=[_event(minutes=15, impact=ImpactLevel.HIGH)]
    )
    assert window.triggered
    assert not window.soft  # HIGH normalises to 0.9, above the 0.85 block line
    assert window.source == "calendar"
    assert window.blocking_reason == "US Nonfarm Payrolls (high)"
    later = [_event(minutes=31, impact=ImpactLevel.HIGH)]
    assert not evaluate_event_freeze(now=NOW, upcoming_events=later).triggered


def test_medium_calendar_release_is_below_default_floor() -> None:
    # MEDIUM normalises to 0.55, under the default 0.6 floor; a caller that
    # lowers the floor sees it as a soft warning.
    events = [_event(minutes=15, impact=ImpactLevel.MEDIUM)]
    assert not evaluate_event_freeze(now=NOW, upcoming_events=events).triggered
    window = evaluate_event_freeze(now=NOW, upcoming_events=events, min_impact=Decimal("0.5"))
    assert window.triggered
    assert window.soft


def test_worst_item_is_reported_and_all_are_counted() -> None:
    window = evaluate_event_freeze(
        now=NOW,
        upcoming=[_news(minutes=-10, impact="0.7"), _news(minutes=20, impact="0.95")],
        upcoming_events=[_event(minutes=5, impact=ImpactLevel.HIGH, name="CPI")],
    )
    assert window.triggered
    assert window.upcoming_count == 3
    assert window.source == "news"  # 0.95 beats the calendar's 0.9
    assert "impact 0.95" in (window.blocking_reason or "")
    assert not window.soft
