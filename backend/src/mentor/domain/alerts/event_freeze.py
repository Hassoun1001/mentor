"""Event-freeze evaluator.

Given the user's planned trade time and a list of upcoming
high-impact news/events (classified by the news pipeline) plus
scheduled economic releases (from the calendar adapter), determine
whether the trade falls inside a freeze window.

This is the discipline circuit-breaker. The mentor's framing in the
explainer always paired the rule with the *why*: news releases blow
through stops at multiples of the usual ATR. A high-conviction setup
that happens to coincide with a Fed statement isn't a setup — it's a
coin flip with a wider distribution.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from mentor.domain.calendar.event import EconomicEvent
from mentor.domain.news.classifier import NewsCategory
from mentor.domain.news.item import NewsItem


@dataclass(frozen=True, slots=True)
class EventFreezeWindow:
    triggered: bool
    upcoming_count: int
    blocking_reason: str | None
    soft: bool  # True = warn only, False = block
    source: str | None = None  # "news" | "calendar" | None

    @property
    def label(self) -> str:
        if not self.triggered:
            return "no high-impact event in window"
        kind = "Warning" if self.soft else "Blocked"
        return f"{kind}: {self.blocking_reason or 'high-impact event nearby'}"


def evaluate_event_freeze(
    *,
    now: datetime,
    upcoming: Sequence[NewsItem] = (),
    upcoming_events: Sequence[EconomicEvent] = (),
    min_impact: Decimal = Decimal("0.6"),
    minutes_before: int = 30,
    minutes_after: int = 30,
    block_above_impact: Decimal = Decimal("0.85"),
) -> EventFreezeWindow:
    """Inspect classified news + scheduled events in the freeze window.

    Behaviour:

    - If any item's `ts` falls in `[now - minutes_after, now + minutes_before]`
      AND its impact ≥ `min_impact`, the freeze triggers.
    - If the impact is ≥ `block_above_impact`, the freeze is **hard**
      (block). Otherwise it is **soft** (warn).
    - News in the `hype` category is ignored regardless of impact.
    """
    earliest = now - timedelta(minutes=minutes_after)
    latest = now + timedelta(minutes=minutes_before)

    candidates: list[tuple[Decimal, str, str]] = []
    # (impact, source, label)

    for item in upcoming:
        if item.classification is None:
            continue
        if item.classification.category is NewsCategory.HYPE:
            continue
        if item.classification.impact < min_impact:
            continue
        if not (earliest <= item.ts <= latest):
            continue
        label = (
            f"{item.classification.category.value} — impact "
            f'{item.classification.impact:.2f}: "{item.headline}"'
        )
        candidates.append((item.classification.impact, "news", label))

    for event in upcoming_events:
        normalised = event.impact.normalised
        if normalised < min_impact:
            continue
        if not (earliest <= event.ts <= latest):
            continue
        label = f"{event.country} {event.name} ({event.impact.name.lower()})"
        candidates.append((normalised, "calendar", label))

    if not candidates:
        return EventFreezeWindow(
            triggered=False,
            upcoming_count=0,
            blocking_reason=None,
            soft=True,
            source=None,
        )

    worst_impact, worst_source, worst_label = max(candidates, key=lambda c: c[0])
    soft = worst_impact < block_above_impact
    return EventFreezeWindow(
        triggered=True,
        upcoming_count=len(candidates),
        blocking_reason=worst_label,
        soft=soft,
        source=worst_source,
    )
