"""Alerts domain — Phase 5.

> Notifications on chosen price levels and approaching high-impact events.
> Event freeze — warns before (or blocks) new trades in the window around
> a high-impact release.   — Mentor plan, §6.H

A price alert is a simple watcher. An event-freeze is the discipline
guardrail the plan calls out: even if your setup is perfect, opening a
new trade five minutes before a central-bank decision is a coin-flip.
"""

from mentor.domain.alerts.alert import Alert, AlertCondition, AlertKind, AlertStatus
from mentor.domain.alerts.evaluation import evaluate_price_alert
from mentor.domain.alerts.event_freeze import (
    EventFreezeWindow,
    evaluate_event_freeze,
)

__all__ = [
    "Alert",
    "AlertCondition",
    "AlertKind",
    "AlertStatus",
    "EventFreezeWindow",
    "evaluate_event_freeze",
    "evaluate_price_alert",
]
