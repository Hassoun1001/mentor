"""Economic calendar domain.

> Scheduled high-impact events (rate decisions, CPI, jobs data) flagged
> before they hit.   — Mentor plan, §6.C

The calendar complements the news pipeline: news is reactive (a release
*just happened*), the calendar is predictive (a release *is scheduled
to happen*). Both feed the event-freeze evaluator so a trader can't
accidentally open into a Fed statement.
"""

from mentor.domain.calendar.adapter import EconomicCalendarAdapter, RawEconomicEvent
from mentor.domain.calendar.event import EconomicEvent, ImpactLevel

__all__ = [
    "EconomicCalendarAdapter",
    "EconomicEvent",
    "ImpactLevel",
    "RawEconomicEvent",
]
