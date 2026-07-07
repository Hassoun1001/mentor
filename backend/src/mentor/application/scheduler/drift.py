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
from statistics import fmean

# With no champion figure to compare against, anything clearly worse than
# a coin flip (Brier 0.25) is degradation by definition.
_COIN_FLIP_BRIER = 0.25


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
