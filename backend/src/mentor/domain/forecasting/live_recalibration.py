"""Live recalibration — let the champion's own live mistakes correct its confidence.

Training-time calibration (the isotonic map fitted on the calibration
slice) makes "60%" mean 60% *on the history the model was built from*.
Live trading is a different, later market. When the champion's resolved
live calls say its 60% has really been landing 53% of the time, the honest
response is to say 53% — and that is the one lesson a small live record can
teach without fitting noise.

Why confidence, and only confidence. The live record grows by roughly one
independent observation per trading day (hourly calls on a 24-bar horizon
overlap almost entirely; see `select_independent`). Thirty such days cannot
support re-deciding which features matter or re-fitting a classifier —
that would chase noise straight into the model. They *can* support one
number: how much to stretch or shrink the model's distance from 50/50.

The correction is a single **slope on the log-odds**::

    p' = sigmoid(slope * logit(p))

- ``slope < 1`` — the model has been overconfident; pull calls toward 50%.
- ``slope = 1`` — leave the model's own calibration alone.
- ``slope > 1`` — it has been underconfident; let calls stand further out.

It fixes 50% in place and never flips a lean (a 55% "up" can become 52%,
never 48%), so it corrects how sure the model says it is without
overriding what it thinks.

Honesty discipline, the same as the rest of the codebase:

- **Independent outcomes only.** Callers pass the non-overlapping subset;
  overlapping windows would count one market day two dozen times.
- **A sample floor.** Below `MIN_SAMPLE_FOR_VERDICT` independent outcomes
  no correction is fitted at all.
- **Select on one slice, grade on another.** The slope is chosen on the
  older half of the live record and graded on the newer half, in time
  order, never shuffled. A slope picked and graded on the same calls is a
  description of those calls, not a correction.
- **A minimum gain.** It ships only if it improves Brier on the held-out
  half by at least `_MIN_GAIN`. "No correction" competes on equal terms
  and wins every tie.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.forecast import Forecast, direction_from_probability
from mentor.domain.stats.significance import MIN_SAMPLE_FOR_VERDICT

# The correction must buy at least this much held-out Brier to ship. Same
# figure as the promotion margin and the abstention search, for the same
# reason: a difference smaller than this is not a difference.
_MIN_GAIN = 0.002

# Candidate slopes. Shrinking is allowed all the way to 0 (a model whose
# live record says it knows nothing should say 50%); sharpening is capped at
# 1.5, because amplifying a small sample's apparent edge is the riskier of
# the two errors.
_SLOPE_GRID: tuple[float, ...] = tuple(round(0.05 * i, 2) for i in range(0, 31))

# log-odds of 0 or 1 are infinite; clamp so the transform stays finite.
_P_EPS = 1e-4


@dataclass(frozen=True, slots=True)
class LiveRecalibration:
    """What the live record said about the champion's stated confidence.

    ``applied`` is the only field inference reads. Everything else is the
    audit trail: what was tried, on how many calls, and what it measured on
    calls the slope never saw.
    """

    applied: bool
    slope: float  # the slope the fit chose (1.0 = none); see `active_slope`
    n_independent: int
    required: int
    n_fit: int = 0
    n_holdout: int = 0
    brier_before: float | None = None  # held-out Brier of the model's own p
    brier_after: float | None = None  # held-out Brier with the slope applied
    reason: str = ""

    @property
    def active_slope(self) -> float:
        """The slope inference should use: the chosen one only if it shipped."""
        return self.slope if self.applied else 1.0

    @property
    def gain(self) -> float | None:
        """Held-out Brier improvement. Positive means the slope helped."""
        if self.brier_before is None or self.brier_after is None:
            return None
        return self.brier_before - self.brier_after

    def to_dict(self) -> dict[str, object]:
        out = asdict(self)
        out["gain"] = self.gain
        out["active_slope"] = self.active_slope
        return out


def recalibrate(p: float, slope: float) -> float:
    """Apply a log-odds slope to one probability."""
    if slope < 0:
        raise ValidationError("slope must be >= 0", field="slope")
    if slope == 1.0:
        return p
    clamped = min(1.0 - _P_EPS, max(_P_EPS, p))
    z = slope * math.log(clamped / (1.0 - clamped))
    return 1.0 / (1.0 + math.exp(-z))


def _brier(probs: Sequence[float], outcomes: Sequence[int]) -> float:
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes, strict=True)) / len(probs)


def _best_slope(probs: Sequence[float], outcomes: Sequence[int]) -> float:
    """Lowest-Brier slope on this slice; ties go to the one nearest 1.0.

    The tie-break matters on small samples, where several slopes can score
    identically: when the data cannot tell them apart, "change nothing" is
    the answer it supports.
    """
    best = 1.0
    best_score = _brier(probs, outcomes)
    for slope in _SLOPE_GRID:
        score = _brier([recalibrate(p, slope) for p in probs], outcomes)
        better = score < best_score - 1e-12
        tie_nearer = abs(score - best_score) <= 1e-12 and abs(slope - 1.0) < abs(best - 1.0)
        if better or tie_nearer:
            best, best_score = slope, score
    return best


def fit_live_recalibration(
    calls: Sequence[tuple[float, int]],
    *,
    min_samples: int = MIN_SAMPLE_FOR_VERDICT,
    min_gain: float = _MIN_GAIN,
) -> LiveRecalibration:
    """Decide whether the live record justifies correcting the champion.

    ``calls`` are ``(model's own p_up, realised outcome)`` pairs of
    *independent* resolved live calls, **oldest first**. The model's own
    probability matters: fitting on already-corrected numbers would stack
    one correction on the next.
    """
    for p, y in calls:
        if not 0.0 <= p <= 1.0:
            raise ValidationError("p_up must be in [0, 1]", field="calls")
        if y not in (0, 1):
            raise ValidationError("outcomes must be 0 or 1", field="calls")

    n = len(calls)
    if n < min_samples:
        return LiveRecalibration(
            applied=False,
            slope=1.0,
            n_independent=n,
            required=min_samples,
            reason=(
                f"Only {n} independent live outcomes so far (need {min_samples}) — "
                f"too few to say anything about the model's confidence. Keeping its own "
                f"calibration."
            ),
        )

    # Older half selects, newer half grades. Time order is the point: the
    # question is whether a slope learned from the past improves the future.
    n_fit = n // 2
    fit, holdout = calls[:n_fit], calls[n_fit:]
    fit_p, fit_y = [p for p, _ in fit], [y for _, y in fit]
    hold_p, hold_y = [p for p, _ in holdout], [y for _, y in holdout]

    slope = _best_slope(fit_p, fit_y)
    before = _brier(hold_p, hold_y)
    after = _brier([recalibrate(p, slope) for p in hold_p], hold_y)
    gain = before - after

    if slope == 1.0:
        applied = False
        reason = (
            "The model's own calibration already fits its live record best — "
            "no correction needed."
        )
    elif gain >= min_gain:
        applied = True
        reason = (
            f"Slope {slope:.2f} chosen on the older {n_fit} live outcomes cut Brier on "
            f"the newer {n - n_fit} from {before:.4f} to {after:.4f} "
            f"(gain {gain:.4f} >= {min_gain}) — applied."
        )
    else:
        applied = False
        reason = (
            f"Slope {slope:.2f} looked better on the older {n_fit} live outcomes but "
            f"moved Brier on the newer {n - n_fit} from {before:.4f} to {after:.4f} "
            f"(gain {gain:+.4f}, needed {min_gain}) — not applied. A correction that "
            f"doesn't hold up on calls it didn't see is noise."
        )

    return LiveRecalibration(
        applied=applied,
        slope=slope,
        n_independent=n,
        required=min_samples,
        n_fit=n_fit,
        n_holdout=n - n_fit,
        brier_before=before,
        brier_after=after,
        reason=reason,
    )


def apply_to_forecast(forecast: Forecast, slope: float) -> Forecast:
    """Restate a forecast's probability under a live-fitted slope.

    The lean never flips (the slope fixes 50% in place), but a weak lean can
    fall inside the neutral band once its confidence is corrected — which is
    the point: a call the live record says is a coin flip should read as one.
    Confidence is rescaled by the same factor as the distance from 50/50, so
    any regime shrink already applied to it is preserved.
    """
    if slope == 1.0:
        return forecast
    own = forecast.p_up
    corrected = Decimal(str(round(recalibrate(float(own), slope), 4)))
    own_distance = abs(own - Decimal("0.5"))
    if own_distance > 0:
        ratio = abs(corrected - Decimal("0.5")) / own_distance
        confidence = min(Decimal("1"), (forecast.confidence * ratio).quantize(Decimal("0.0001")))
    else:
        confidence = forecast.confidence
    tone = "overconfident" if slope < 1.0 else "underconfident"
    reasoning = (
        f"{forecast.reasoning} The live record says this model has been {tone}, so its "
        f"{own * 100:.0f}% is restated as {corrected * 100:.0f}%."
    )
    return replace(
        forecast,
        p_up=corrected,
        confidence=confidence,
        direction=direction_from_probability(corrected),
        reasoning=reasoning,
        p_up_model=own,
    )
