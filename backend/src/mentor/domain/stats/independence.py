"""Independent observations from overlapping forecasts.

A forecast's outcome is decided over a window of market time, and the live
loop forecasts far more often than that window is long: an hourly call on a
24-bar horizon shares 23/24 of its window with the next one. Counting every
call as a separate observation counts one market day two dozen times, which
makes every statistic built on them — drift verdicts, win rates, calibration
fits — look far more certain than the evidence allows.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime


def select_independent(
    calls: Sequence[tuple[datetime, datetime, float, int]],
) -> list[tuple[float, int]]:
    """Reduce resolved calls to a non-overlapping subset, newest first.

    Hourly predictions with a 24-bar horizon share 23/24 of their outcome
    window — treating them as independent lets the drift watch fire (or stay
    silent) on autocorrelated noise. Walking from the newest call backwards,
    a call is kept only if its outcome window ends at or before the previous
    kept call's start, so every kept observation covers disjoint market time.

    ``calls`` are ``(asof, horizon_at, p_up, outcome)`` tuples in any order;
    the result is ``(p_up, outcome)`` pairs suitable for ``assess_drift``.
    """
    ordered = sorted(calls, key=lambda c: c[0], reverse=True)
    kept: list[tuple[float, int]] = []
    window_floor: datetime | None = None
    for asof, horizon_at, p_up, outcome in ordered:
        if window_floor is None or horizon_at <= window_floor:
            kept.append((p_up, outcome))
            window_floor = asof
    return kept
