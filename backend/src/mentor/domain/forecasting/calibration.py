"""Calibration metrics — make "60%" actually mean 60%.

Calibration is the whole thesis of this product: a probability is only
useful if it matches the realised frequency. These pure helpers turn a set
of (predicted probability, binary outcome) pairs into:

- **reliability bins** — for each probability band, the mean predicted
  probability vs the empirical hit rate (the data behind a reliability
  diagram, plotted against the 45-degree line).
- **ECE (expected calibration error)** — the sample-weighted average gap
  between predicted and realised across bins. Lower is better; 0 is
  perfect calibration.

Calibration does *not* raise accuracy — it makes the numbers trustworthy,
which is exactly what an honest forecaster owes the user.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReliabilityBin:
    lower: float
    upper: float
    midpoint: float
    predicted_mean: float  # mean predicted p in this bin
    empirical_rate: float  # realised hit rate in this bin
    count: int


def reliability_bins(
    probs: Sequence[float], outcomes: Sequence[int], *, n_bins: int = 10
) -> list[ReliabilityBin]:
    """Equal-width [0,1] bins with predicted vs realised per bin.

    Empty bins are omitted (nothing to plot). ``outcomes`` are 0/1.
    """
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must align")
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")

    width = 1.0 / n_bins
    bins: list[ReliabilityBin] = []
    for b in range(n_bins):
        lo = b * width
        hi = (b + 1) * width
        # Last bin is inclusive of 1.0; others are [lo, hi).
        members = [
            (p, y)
            for p, y in zip(probs, outcomes, strict=True)
            if (lo <= p < hi) or (b == n_bins - 1 and p == 1.0)
        ]
        if not members:
            continue
        n = len(members)
        pred_mean = sum(p for p, _ in members) / n
        emp_rate = sum(y for _, y in members) / n
        bins.append(
            ReliabilityBin(
                lower=lo,
                upper=hi,
                midpoint=(lo + hi) / 2,
                predicted_mean=pred_mean,
                empirical_rate=emp_rate,
                count=n,
            )
        )
    return bins


def expected_calibration_error(
    probs: Sequence[float], outcomes: Sequence[int], *, n_bins: int = 10
) -> float:
    """Sample-weighted mean |predicted - realised| across reliability bins."""
    total = len(probs)
    if total == 0:
        return 0.0
    bins = reliability_bins(probs, outcomes, n_bins=n_bins)
    return sum(
        (b.count / total) * abs(b.predicted_mean - b.empirical_rate) for b in bins
    )
