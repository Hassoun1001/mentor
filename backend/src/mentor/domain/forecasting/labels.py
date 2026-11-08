"""Label construction — point-in-time safe.

The label for the bar stamped ``t`` is "did the market close above this
bar's close by the horizon?". The horizon is clock time: ``horizon_bars``
bars of the timeframe after ``t``. The outcome is the close of the first bar
still open at that moment — in a closed market, the first bar after the
reopen.

That is the rule the resolver grades live calls by (``outcome_bar``), so a
model learns exactly what it is later marked on. Counting bars by position
would disagree as soon as the closed-market hours are absent from the data:
24 hourly bars from a Friday morning would end on Monday, while the live
call is graded at Sunday's reopen.

The label is binary. We deliberately do not predict the *size* of the
move; the calibration metric is "does P(up) match realised hit rate?"
not "did we hit a price target?"
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal

# Same limit as the resolver's MAX_RESOLUTION_LAG: longer than a weekend
# plus a holiday, and past it the silence is a data gap, not a closed market.
_MAX_OUTCOME_LAG = timedelta(days=4)


def build_labels(
    closes: Sequence[Decimal],
    *,
    timestamps: Sequence[datetime],
    horizon_bars: int,
    bar_seconds: int,
) -> list[tuple[datetime, int]]:
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be >= 1")
    if len(closes) != len(timestamps):
        raise ValueError("closes and timestamps must align")
    bar = timedelta(seconds=bar_seconds)
    horizon = bar * horizon_bars
    labels: list[tuple[datetime, int]] = []
    j = 0
    for i, ts in enumerate(timestamps):
        horizon_at = ts + horizon
        j = max(j, i + 1)
        while j < len(timestamps) and timestamps[j] + bar <= horizon_at:
            j += 1
        if j == len(timestamps):
            break  # the outcome has not happened yet
        if timestamps[j] - horizon_at >= _MAX_OUTCOME_LAG:
            continue
        labels.append((ts, 1 if closes[j] > closes[i] else 0))
    return labels
