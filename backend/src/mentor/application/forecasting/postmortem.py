"""Post-mortem — why the system's predictions hit or missed.

Honest framing (Principle 05): this is a *calibration and feature-
attribution* analysis, not a search for a market-beating signal. It
answers "where is the model overconfident, and which conditions go with
its misses" — the questions that make a forecaster humble and well-
calibrated. It does not, and cannot, manufacture an edge on an efficient
market.

A directional prediction is a **hit** when its lean matched the realised
move (long + up, or short + not-up). Neutral predictions take no
directional stance and are reported separately.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import fmean

from mentor.domain.forecasting.calibration import expected_calibration_error
from mentor.domain.forecasting.forecast import Direction
from mentor.infrastructure.models import PredictionORM


@dataclass(frozen=True, slots=True)
class FeatureContrast:
    feature: str
    mean_on_hits: float
    mean_on_misses: float
    gap: float  # mean_on_misses - mean_on_hits


@dataclass(frozen=True, slots=True)
class CalibrationBucket:
    bucket: str
    stated_midpoint: float
    realised_hit_rate: float
    samples: int


@dataclass(frozen=True, slots=True)
class PostMortem:
    sample_size: int
    directional: int
    neutral: int
    hits: int
    misses: int
    directional_accuracy: float
    avg_confidence_on_hits: float
    avg_confidence_on_misses: float
    brier_score: float
    ece: float  # expected calibration error of P(up) over all resolved predictions
    feature_contrasts: tuple[FeatureContrast, ...]
    calibration: tuple[CalibrationBucket, ...]
    headline: str


def _is_hit(direction: str, outcome: int) -> bool | None:
    if direction == Direction.LONG.value:
        return outcome == 1
    if direction == Direction.SHORT.value:
        return outcome == 0
    return None  # neutral — no directional stance


def compute_post_mortem(rows: Sequence[PredictionORM]) -> PostMortem:
    resolved = [r for r in rows if r.realised_outcome is not None]
    if not resolved:
        return PostMortem(
            sample_size=0,
            directional=0,
            neutral=0,
            hits=0,
            misses=0,
            directional_accuracy=0.0,
            avg_confidence_on_hits=0.0,
            avg_confidence_on_misses=0.0,
            brier_score=0.0,
            ece=0.0,
            feature_contrasts=(),
            calibration=(),
            headline=(
                "No resolved predictions yet — run a replay or wait for the loop "
                "to resolve some."
            ),
        )

    hit_feats: list[dict[str, float]] = []
    miss_feats: list[dict[str, float]] = []
    hit_conf: list[float] = []
    miss_conf: list[float] = []
    neutral = 0
    brier_terms: list[float] = []

    for r in resolved:
        outcome = int(r.realised_outcome or 0)
        # Brier: (p_up - actual_up)^2, lower is better. 0.25 == always 0.5.
        brier_terms.append((float(r.p_up) - outcome) ** 2)
        verdict = _is_hit(r.direction, outcome)
        if verdict is None:
            neutral += 1
            continue
        try:
            feats = {k: float(v) for k, v in json.loads(r.features_json).items()}
        except (ValueError, TypeError):
            feats = {}
        if verdict:
            hit_feats.append(feats)
            hit_conf.append(float(r.confidence))
        else:
            miss_feats.append(feats)
            miss_conf.append(float(r.confidence))

    hits = len(hit_feats)
    misses = len(miss_feats)
    directional = hits + misses
    accuracy = hits / directional if directional else 0.0

    all_features = sorted({k for d in (*hit_feats, *miss_feats) for k in d})
    contrasts: list[FeatureContrast] = []
    for name in all_features:
        hv = [d[name] for d in hit_feats if name in d]
        mv = [d[name] for d in miss_feats if name in d]
        if not hv or not mv:
            continue
        mean_hit = fmean(hv)
        mean_miss = fmean(mv)
        contrasts.append(
            FeatureContrast(
                feature=name,
                mean_on_hits=mean_hit,
                mean_on_misses=mean_miss,
                gap=mean_miss - mean_hit,
            )
        )
    # Surface the features whose hit/miss means diverge most.
    contrasts.sort(key=lambda c: abs(c.gap), reverse=True)

    # Calibration buckets (10% wide) over all resolved predictions.
    buckets: dict[int, list[int]] = {}
    for r in resolved:
        lo = int(float(r.p_up) * 10) * 10
        buckets.setdefault(lo, []).append(int(r.realised_outcome or 0))
    calibration = tuple(
        CalibrationBucket(
            bucket=f"{lo}-{lo + 10}%",
            stated_midpoint=(lo + 5) / 100,
            realised_hit_rate=fmean(vals) if vals else 0.0,
            samples=len(vals),
        )
        for lo, vals in sorted(buckets.items())
    )

    brier = fmean(brier_terms) if brier_terms else 0.0
    ece = expected_calibration_error(
        [float(r.p_up) for r in resolved],
        [int(r.realised_outcome or 0) for r in resolved],
    )
    headline = (
        f"Across {directional} directional calls the system was right "
        f"{accuracy * 100:.0f}% of the time (Brier {brier:.3f}; 0.25 is a coin flip). "
        + (
            "Confidence was higher on hits than misses — mild positive calibration."
            if fmean(hit_conf or [0]) > fmean(miss_conf or [0])
            else (
                "Confidence was NOT higher on hits — the model is poorly calibrated "
                "and its certainty can't be trusted."
            )
        )
    )

    return PostMortem(
        sample_size=len(resolved),
        directional=directional,
        neutral=neutral,
        hits=hits,
        misses=misses,
        directional_accuracy=accuracy,
        avg_confidence_on_hits=fmean(hit_conf) if hit_conf else 0.0,
        avg_confidence_on_misses=fmean(miss_conf) if miss_conf else 0.0,
        brier_score=brier,
        ece=ece,
        feature_contrasts=tuple(contrasts[:6]),
        calibration=calibration,
        headline=headline,
    )
