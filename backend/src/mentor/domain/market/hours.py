"""When the FX market trades.

The market closes Friday ~22:00 UTC and reopens Sunday ~22:00 UTC. That
weekly gap is normal — a quiet feed then is not an outage, and a forecast
due inside it can only be graded after the reopen.

Pure and dependency-free so both the scheduler's quality gate and the
health digest can ask the question. It used to live in the scheduler
package, and importing it from the health layer pulled the whole scheduler
in, which imported the health layer back: a circular import that broke any
tool that loaded the self-report first.
"""

from __future__ import annotations

from datetime import UTC, datetime

# FX weekly close/open (UTC hours).
_FRIDAY = 4
_SATURDAY = 5
_SUNDAY = 6
_CLOSE_OPEN_HOUR_UTC = 22


def fx_market_open(now: datetime) -> bool:
    """True when the FX market is normally trading at `now` (UTC)."""
    ts = now.astimezone(UTC)
    if ts.weekday() == _SATURDAY:
        return False
    if ts.weekday() == _FRIDAY and ts.hour >= _CLOSE_OPEN_HOUR_UTC:
        return False
    return not (ts.weekday() == _SUNDAY and ts.hour < _CLOSE_OPEN_HOUR_UTC)
