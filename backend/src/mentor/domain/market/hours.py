"""When the FX market trades.

The market closes at 17:00 New York time on Friday and reopens at 17:00
New York time on Sunday. That is 22:00 UTC in US winter and 21:00 UTC in
US summer, so the rule is written in New York time: a fixed UTC hour is
wrong for two thirds of the year. That weekly gap is normal — a quiet feed
then is not an outage, and a forecast due inside it can only be graded
after the reopen.

Pure so both the scheduler's quality gate and the health digest can ask the
question. It used to live in the scheduler package, and importing it from
the health layer pulled the whole scheduler in, which imported the health
layer back: a circular import that broke any tool that loaded the
self-report first.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_NEW_YORK = ZoneInfo("America/New_York")
_FRIDAY = 4
_SATURDAY = 5
_SUNDAY = 6
_CLOSE_OPEN_HOUR_NY = 17
_SAMPLE_MINUTES = 5


def fx_market_open(now: datetime) -> bool:
    """True when the FX market is normally trading at `now`."""
    ts = now.astimezone(_NEW_YORK)
    if ts.weekday() == _SATURDAY:
        return False
    if ts.weekday() == _FRIDAY and ts.hour >= _CLOSE_OPEN_HOUR_NY:
        return False
    return not (ts.weekday() == _SUNDAY and ts.hour < _CLOSE_OPEN_HOUR_NY)


def market_open_minutes(start: datetime, end: datetime) -> int:
    """Minutes between two instants the market was open, to five minutes."""
    step = timedelta(minutes=_SAMPLE_MINUTES)
    minutes = 0
    cursor = start
    while cursor < end:
        if fx_market_open(cursor):
            minutes += _SAMPLE_MINUTES
        cursor += step
    return minutes
