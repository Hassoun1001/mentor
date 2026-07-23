"""Does the volatility forecast actually mean what it says?

The direction model has been audited to exhaustion. The volatility model
never has — and it is the one that moves money. It sets the stop distance,
which sets the position size, which sets the trailing distance and the
expected-move figure on the trade ticket. Every risk number downstream is
a function of this one estimate.

It makes two claims, and both are falsifiable:

1. **The 1-sigma claim.** ``horizon_move_pips`` converts a per-bar vol into
   a 1-sigma move over the horizon, and the docstring promises "roughly
   two-in-three of moves land inside it". Under a normal random walk that
   is 68.27%. If the true figure is 50%, every stop the app recommends is
   too tight and the user is stopped out on trades that were otherwise
   fine — while the app reassures them the sizing is sound. That is a
   worse failure than a weak direction call, because it is silent.

2. **The conformal band claim.** The band is advertised as covering ~90%.
   Worth stating precisely what it covers: the residual quantile is fitted
   on *volatility prediction errors*, so the band is an interval around the
   sigma estimate, not a prediction interval for the realised move. A user
   reading "90% band: 20 to 40 pips" will assume the move lands in that
   range nine times in ten. We measure whether it does, and report the two
   numbers separately rather than letting one stand in for the other.

Financial returns are fat-tailed, so a hit rate somewhat *above* 68% with
occasional large misses is the expected shape rather than a defect. What
would be damning is a hit rate materially below it: that means systematic
under-forecasting of risk.

Every rate is reported with a Wilson interval, because "we observed 61% on
80 samples" is not evidence of miscalibration on its own.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from mentor.domain.errors import ValidationError
from mentor.domain.stats.significance import wilson_interval

# Share of a normal distribution within +/-1 standard deviation.
NORMAL_ONE_SIGMA = 0.6827


@dataclass(frozen=True, slots=True)
class VolSample:
    """One forecast paired with what actually happened."""

    predicted_sigma_pips: float
    realised_move_pips: float  # absolute move over the horizon
    band_low_pips: float | None = None
    band_high_pips: float | None = None


@dataclass(frozen=True, slots=True)
class RateCheck:
    """An observed rate against the rate that was promised."""

    label: str
    n: int
    observed: float
    expected: float
    low: float
    high: float
    significant: bool  # the interval excludes the promised rate
    verdict: str

    @property
    def understates_risk(self) -> bool:
        """Significantly fewer moves landed inside than promised.

        The dangerous direction: stops are tighter than the app implies.
        """
        return self.significant and self.observed < self.expected


@dataclass(frozen=True, slots=True)
class VolAuditResult:
    n: int
    one_sigma: RateCheck
    band: RateCheck | None  # None when no bands were supplied
    median_ratio: float  # realised / predicted; 1.0 = unbiased
    mae_pips: float
    benchmark_mae_pips: dict[str, float]
    beats_benchmarks: bool
    verdict: str


def _rate_check(
    *, label: str, hits: int, n: int, expected: float, what: str
) -> RateCheck:
    observed = hits / n
    low, high = wilson_interval(hits, n)
    significant = low > expected or high < expected

    obs = f"{observed * 100:.0f}%"
    exp = f"{expected * 100:.0f}%"
    band = f"[{low * 100:.0f}%, {high * 100:.0f}%]"

    if not significant:
        verdict = (
            f"{what} landed inside {obs} of the time on {n:,} forecasts. The 95% "
            f"interval {band} contains the promised {exp}, so the claim holds as "
            f"far as this sample can tell."
        )
    elif observed < expected:
        verdict = (
            f"{what} landed inside only {obs} of the time on {n:,} forecasts, and "
            f"the 95% interval {band} sits entirely below the promised {exp}. The "
            f"forecast is understating how far price moves — every stop derived "
            f"from it is too tight."
        )
    else:
        verdict = (
            f"{what} landed inside {obs} of the time on {n:,} forecasts, above the "
            f"promised {exp} (95% interval {band}). The forecast is conservative: "
            f"stops are wider than strictly needed, which costs position size but "
            f"not survival."
        )

    return RateCheck(
        label=label,
        n=n,
        observed=observed,
        expected=expected,
        low=low,
        high=high,
        significant=significant,
        verdict=verdict,
    )


def audit_vol_forecasts(
    samples: Sequence[VolSample],
    *,
    benchmarks: dict[str, Sequence[float]] | None = None,
    band_coverage: float = 0.90,
) -> VolAuditResult:
    """Grade a run of volatility forecasts against what the market did.

    ``benchmarks`` maps a name to that benchmark's predicted sigma for the
    same samples, in the same order — a forecast that cannot beat "use
    yesterday's volatility" has not earned the complexity it costs.
    """
    if not samples:
        raise ValidationError("no forecasts to audit", field="samples")
    if not 0 < band_coverage < 1:
        raise ValidationError("band_coverage must be in (0, 1)", field="band_coverage")

    n = len(samples)
    usable = [s for s in samples if s.predicted_sigma_pips > 0]
    if not usable:
        raise ValidationError("every forecast predicted zero volatility", field="samples")

    one_sigma_hits = sum(
        1 for s in usable if s.realised_move_pips <= s.predicted_sigma_pips
    )
    one_sigma = _rate_check(
        label="1-sigma expected move",
        hits=one_sigma_hits,
        n=len(usable),
        expected=NORMAL_ONE_SIGMA,
        what="The realised move",
    )

    banded = [
        s
        for s in samples
        if s.band_low_pips is not None and s.band_high_pips is not None
    ]
    band: RateCheck | None = None
    if banded:
        band_hits = sum(
            1
            for s in banded
            # mypy: the comprehension above guarantees these are not None
            if s.band_low_pips is not None
            and s.band_high_pips is not None
            and s.band_low_pips <= s.realised_move_pips <= s.band_high_pips
        )
        band = _rate_check(
            label=f"conformal {int(band_coverage * 100)}% band",
            hits=band_hits,
            n=len(banded),
            expected=band_coverage,
            what="The realised move",
        )

    # Median rather than mean: one crisis bar would otherwise dominate, and
    # the question is whether the typical forecast is biased.
    ratios = sorted(s.realised_move_pips / s.predicted_sigma_pips for s in usable)
    mid = len(ratios) // 2
    median_ratio = (
        ratios[mid] if len(ratios) % 2 else (ratios[mid - 1] + ratios[mid]) / 2
    )

    mae = sum(abs(s.realised_move_pips - s.predicted_sigma_pips) for s in usable) / len(
        usable
    )

    bench_mae: dict[str, float] = {}
    for name, preds in (benchmarks or {}).items():
        if len(preds) != n:
            raise ValidationError(
                f"benchmark '{name}' has {len(preds)} predictions for {n} samples",
                field="benchmarks",
            )
        pairs = [
            (p, s.realised_move_pips)
            for p, s in zip(preds, samples, strict=True)
            if p > 0
        ]
        if pairs:
            bench_mae[name] = sum(abs(r - p) for p, r in pairs) / len(pairs)

    beats = all(mae <= v + 1e-9 for v in bench_mae.values()) if bench_mae else True

    return VolAuditResult(
        n=n,
        one_sigma=one_sigma,
        band=band,
        median_ratio=median_ratio,
        mae_pips=mae,
        benchmark_mae_pips=bench_mae,
        beats_benchmarks=beats,
        verdict=_overall_verdict(one_sigma, band, median_ratio, mae, bench_mae, beats),
    )


def _overall_verdict(
    one_sigma: RateCheck,
    band: RateCheck | None,
    median_ratio: float,
    mae: float,
    bench_mae: dict[str, float],
    beats: bool,
) -> str:
    parts: list[str] = []

    if one_sigma.understates_risk:
        parts.append(
            "The expected move is too small: price routinely travels further than "
            "the forecast says, so stops sized off it are too tight. This is the "
            "failure mode that costs money quietly."
        )
    elif one_sigma.significant:
        parts.append(
            "The expected move is conservative — price stays inside it more often "
            "than promised. Safe, but it costs position size."
        )
    else:
        parts.append("The 1-sigma expected move is holding up on this sample.")

    if band is not None and band.understates_risk:
        parts.append(
            "The advertised band is also too narrow — it covers less than it claims."
        )

    drift = abs(median_ratio - 1.0)
    if drift > 0.25:
        direction = "larger" if median_ratio > 1 else "smaller"
        parts.append(
            f"Typical realised moves are {median_ratio:.2f}x the forecast — "
            f"systematically {direction}, not random error."
        )

    if bench_mae:
        best = min(bench_mae, key=lambda k: bench_mae[k])
        if beats:
            parts.append(
                f"It beats every naive benchmark (best rival '{best}' at "
                f"{bench_mae[best]:.1f} pips MAE vs {mae:.1f})."
            )
        else:
            parts.append(
                f"It does NOT beat the naive benchmark '{best}' "
                f"({bench_mae[best]:.1f} pips MAE vs {mae:.1f}) — the extra "
                f"machinery is not earning its keep."
            )

    return " ".join(parts)


def normal_quantile_hit_rate(z: float) -> float:
    """Share of a normal distribution within +/-``z`` standard deviations.

    Used to state what a band *should* cover before measuring what it does.
    """
    return math.erf(z / math.sqrt(2.0))
