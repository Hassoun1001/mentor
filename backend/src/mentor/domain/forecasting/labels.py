"""Label construction — point-in-time safe.

The label for the row at index `i` is "did close go up over the next H
bars?" i.e. `close[i+H] > close[i]`. We only emit labels where `i+H`
exists in the series — labels at the tail are dropped.

The label is binary. We deliberately do not predict the *size* of the
move; the calibration metric is "does P(up) match realised hit rate?"
not "did we hit a price target?"
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal


def build_labels(
    closes: Sequence[Decimal], *, timestamps: Sequence[datetime], horizon_bars: int
) -> list[tuple[datetime, int]]:
    if horizon_bars < 1:
        raise ValueError("horizon_bars must be >= 1")
    if len(closes) != len(timestamps):
        raise ValueError("closes and timestamps must align")
    labels: list[tuple[datetime, int]] = []
    for i in range(len(closes) - horizon_bars):
        labels.append((timestamps[i], 1 if closes[i + horizon_bars] > closes[i] else 0))
    return labels
