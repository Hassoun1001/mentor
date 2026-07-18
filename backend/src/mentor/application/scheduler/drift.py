"""Drift watch — learn from the system's own live predictions.

Retraining on a fixed weekly timer ignores the most direct evidence the
system produces about itself: the resolved outcomes of its *live*
predictions. When the rolling Brier of recent resolved calls degrades
past what the champion demonstrated at promotion time, the market has
likely drifted away from the training regime — waiting days for the
next scheduled retrain just accumulates bad calls.

`assess_drift` is a pure function over (p_up, outcome) pairs so the
trigger logic is unit-testable without a database. The scheduler applies
it after each resolve pass and, on a verdict, fires an immediate
retrain (rate-limited by a cooldown so a rough patch can't cause a
retrain storm).

Honest framing: this improves *responsiveness of calibration*, not
market edge. A drift retrain makes the probabilities trustworthy again
sooner; it does not make them prescient.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from statistics import fmean

# With no champion figure to compare against, anything clearly worse than
# a coin flip (Brier 0.25) is degradation by definition.
_COIN_FLIP_BRIER = 0.25


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


@dataclass(frozen=True, slots=True)
class DriftVerdict:
    retrain: bool
    live_brier: float | None
    threshold: float | None
    samples: int
    reason: str


def assess_drift(
    outcomes: Sequence[tuple[float, int]],
    *,
    champion_brier: float | None,
    min_samples: int,
    margin: float,
) -> DriftVerdict:
    """Decide whether live performance has drifted enough to retrain now.

    `outcomes` are (p_up, realised_outcome) pairs of the most recent
    resolved predictions. The trigger threshold is the champion's test
    Brier plus `margin` — or the coin-flip Brier plus `margin` when no
    champion figure exists. Below `min_samples` no verdict is given:
    small windows make Brier noisy enough to fire on pure variance.
    """
    n = len(outcomes)
    if n < min_samples:
        return DriftVerdict(
            retrain=False,
            live_brier=None,
            threshold=None,
            samples=n,
            reason=f"only {n} resolved predictions (need {min_samples}) — no verdict",
        )

    live = fmean((p - y) ** 2 for p, y in outcomes)
    base = champion_brier if champion_brier is not None else _COIN_FLIP_BRIER
    threshold = base + margin
    if live > threshold:
        return DriftVerdict(
            retrain=True,
            live_brier=live,
            threshold=threshold,
            samples=n,
            reason=(
                f"live Brier {live:.4f} over the last {n} resolved predictions exceeds "
                f"{threshold:.4f} (champion {base:.4f} + margin {margin}) — regime drift"
            ),
        )
    return DriftVerdict(
        retrain=False,
        live_brier=live,
        threshold=threshold,
        samples=n,
        reason=f"live Brier {live:.4f} within threshold {threshold:.4f} — healthy",
    )
