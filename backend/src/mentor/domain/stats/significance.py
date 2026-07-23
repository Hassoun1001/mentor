"""Is this number real, or is it luck?

Every performance figure in this app is computed from a finite sample, and
a finite sample of a coin-flip process produces impressive-looking runs
all the time. Forty trades at 60% feels like proof. It is not: the 95%
interval around it comfortably contains 50%.

That gap — between how convincing a number feels and what it actually
supports — is where trading accounts go to die. Someone sees a good
stretch, concludes the edge is real, scales up, and meets variance from
the other side with three times the size on.

So every headline metric gets three companions:

- **A confidence interval**, so the range of truths compatible with the
  data is visible rather than collapsed to a point estimate.
- **The sample size needed** to distinguish the observed effect from
  nothing, so "keep going" has a target instead of a vibe.
- **A verdict in words**, because an interval printed next to a number
  gets read as decoration unless something says out loud what it means.

We use the **Wilson score interval** rather than the textbook normal
approximation. At the sample sizes that matter here — dozens of trades,
proportions near 0.5 — the normal approximation is badly behaved and can
even produce bounds outside [0, 1]. Wilson stays sane on small samples,
which is precisely when the question is being asked.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from mentor.domain.errors import ValidationError

# 95% two-sided. Hardcoded rather than configurable: a tunable confidence
# level is an invitation to lower the bar until the answer is agreeable.
_Z = 1.959963984540054

# Above this the "trades needed" figure stops being useful information and
# starts being discouragement — report it as "more than this" instead.
_MAX_REPORTABLE_N = 100_000

# Below this many observations, no result is called significant no matter
# what the interval does.
#
# The interval alone is not enough of a guard. Five correct calls out of
# five gives a Wilson lower bound near 57%, which excludes a coin flip and
# would be reported as a real edge — but five heads in a row happens by
# chance one time in thirty-two, and anyone watching a handful of strategies
# will see it regularly. Production hit exactly this: after collapsing
# overlapping signals to disjoint windows the sample fell to five, all
# correct, and the verdict read "the edge is real".
#
# Thirty is the conventional floor for treating a proportion this way, and
# it is far below the sample a thin edge actually needs — so a result that
# cannot clear even this is not close.
_MIN_SAMPLE_FOR_VERDICT = 30


@dataclass(frozen=True, slots=True)
class ProportionVerdict:
    """What a win rate or hit rate does and does not establish."""

    n: int
    successes: int
    observed: float
    low: float  # Wilson lower bound
    high: float  # Wilson upper bound
    baseline: float  # what "no edge" looks like (0.5 for direction)
    significant: bool  # interval excludes the baseline entirely
    n_needed: int | None  # sample size to resolve this effect, None if unknowable
    verdict: str

    @property
    def worse_than_baseline(self) -> bool:
        """Significant, but in the wrong direction. Worth saying out loud."""
        return self.significant and self.observed < self.baseline


def wilson_interval(successes: int, n: int, z: float = _Z) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Well-behaved where the normal approximation is not: small ``n``, and
    proportions near 0 or 1. Bounds are always inside [0, 1].
    """
    if n <= 0:
        raise ValidationError("n must be positive", field="n")
    if not 0 <= successes <= n:
        raise ValidationError("successes must be between 0 and n", field="successes")

    p = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    spread = (z / denom) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, centre - spread), min(1.0, centre + spread)


def trades_needed(observed: float, baseline: float = 0.5, z: float = _Z) -> int | None:
    """How many samples before an effect this size clears the noise.

    Solves the normal-approximation sample-size formula for a one-sample
    proportion test. Returns ``None`` when the observed rate equals the
    baseline — there is no effect to detect, so no sample size resolves it.

    The number is deliberately sobering. A 53% edge needs roughly a
    thousand trades; that is not pessimism, it is what a 3-point edge
    costs to prove.
    """
    effect = abs(observed - baseline)
    if effect < 1e-9:
        return None
    variance = baseline * (1 - baseline)
    n = (z * z * variance) / (effect * effect)
    return min(_MAX_REPORTABLE_N, max(1, math.ceil(n)))


def assess_proportion(
    successes: int,
    n: int,
    *,
    baseline: float = 0.5,
    label: str = "calls",
) -> ProportionVerdict:
    """Judge a success rate honestly, including when the honest answer is 'we cannot tell yet'."""
    if n < 0:
        raise ValidationError("n must be >= 0", field="n")
    if not 0 < baseline < 1:
        raise ValidationError("baseline must be in (0, 1)", field="baseline")

    if n == 0:
        return ProportionVerdict(
            n=0,
            successes=0,
            observed=0.0,
            low=0.0,
            high=1.0,
            baseline=baseline,
            significant=False,
            n_needed=None,
            verdict=f"No resolved {label} yet — nothing to measure.",
        )

    observed = successes / n
    low, high = wilson_interval(successes, n)
    needed = trades_needed(observed, baseline)
    excludes_baseline = low > baseline or high < baseline
    significant = excludes_baseline and n >= _MIN_SAMPLE_FOR_VERDICT

    if excludes_baseline and not significant:
        return ProportionVerdict(
            n=n,
            successes=successes,
            observed=observed,
            low=low,
            high=high,
            baseline=baseline,
            significant=False,
            n_needed=needed,
            verdict=(
                f"{n:,} {label}, {observed * 100:.0f}% correct. That looks decisive "
                f"and is not: a run this short goes one way or the other by luck "
                f"often enough to mean nothing. Nothing is called an edge below "
                f"{_MIN_SAMPLE_FOR_VERDICT} {label}, and a thin edge needs far more "
                f"than that."
            ),
        )

    pct = f"{observed * 100:.0f}%"
    band = f"[{low * 100:.0f}%, {high * 100:.0f}%]"
    base_pct = f"{baseline * 100:.0f}%"

    if not significant:
        shortfall = (
            ""
            if needed is None
            else f" At this rate you would need about {needed:,} {label} to tell."
        )
        verdict = (
            f"{n:,} {label}, {pct} correct. The 95% interval {band} contains "
            f"{base_pct}, so this is not yet distinguishable from a coin flip.{shortfall}"
        )
    elif observed < baseline:
        verdict = (
            f"{n:,} {label}, {pct} correct. The 95% interval {band} sits entirely "
            f"below {base_pct} — this is significantly *worse* than a coin flip, "
            f"which is a real finding and not a run of bad luck."
        )
    else:
        verdict = (
            f"{n:,} {label}, {pct} correct. The 95% interval {band} clears "
            f"{base_pct} entirely — on this sample the edge is real. Sample size "
            f"is not the same as a durable edge; markets change."
        )

    return ProportionVerdict(
        n=n,
        successes=successes,
        observed=observed,
        low=low,
        high=high,
        baseline=baseline,
        significant=significant,
        n_needed=needed,
        verdict=verdict,
    )


@dataclass(frozen=True, slots=True)
class MeanVerdict:
    """What an average R-multiple (expectancy) does and does not establish."""

    n: int
    mean: float
    stdev: float
    low: float  # 95% CI on the mean
    high: float
    significant: bool  # interval excludes zero
    n_needed: int | None
    verdict: str


def assess_expectancy(values: list[float], *, label: str = "trades") -> MeanVerdict:
    """Judge an average R honestly. Zero is the "no edge" mark.

    Uses the normal approximation on the mean, which is fine here because
    it is the *mean* that is asymptotically normal regardless of how
    lumpy the underlying R distribution is. The caveat is small n — which
    is exactly why the sample size is reported alongside.
    """
    n = len(values)
    if n < 2:
        return MeanVerdict(
            n=n,
            mean=values[0] if values else 0.0,
            stdev=0.0,
            low=0.0,
            high=0.0,
            significant=False,
            n_needed=None,
            verdict=(
                f"{n} closed {label} — far too few to say anything. "
                "Expectancy needs a sample before it means anything at all."
            ),
        )

    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    stdev = math.sqrt(var)

    if stdev < 1e-12:
        # Every trade identical — degenerate, but don't divide by zero.
        return MeanVerdict(
            n=n,
            mean=mean,
            stdev=0.0,
            low=mean,
            high=mean,
            significant=mean != 0.0,
            n_needed=None,
            verdict=(
                f"{n:,} {label}, every one returning {mean:+.2f}R. That is not a "
                "realistic sample — check the data before trusting it."
            ),
        )

    margin = _Z * stdev / math.sqrt(n)
    low, high = mean - margin, mean + margin
    significant = (low > 0 or high < 0) and n >= _MIN_SAMPLE_FOR_VERDICT

    # n such that the CI half-width is smaller than |mean|.
    needed = (
        None
        if abs(mean) < 1e-12
        else min(_MAX_REPORTABLE_N, max(2, math.ceil((_Z * stdev / abs(mean)) ** 2)))
    )

    band = f"[{low:+.2f}R, {high:+.2f}R]"
    if not significant:
        tail = "" if needed is None else f" About {needed:,} {label} would settle it."
        verdict = (
            f"{n:,} {label}, averaging {mean:+.2f}R. The 95% interval {band} "
            f"straddles zero — this could still be a system with no edge at all.{tail}"
        )
    elif mean < 0:
        verdict = (
            f"{n:,} {label}, averaging {mean:+.2f}R. The 95% interval {band} is "
            f"entirely below zero. This is a losing system on the evidence so far, "
            f"not an unlucky one."
        )
    else:
        verdict = (
            f"{n:,} {label}, averaging {mean:+.2f}R. The 95% interval {band} is "
            f"entirely above zero — a real positive expectancy on this sample."
        )

    return MeanVerdict(
        n=n,
        mean=mean,
        stdev=stdev,
        low=low,
        high=high,
        significant=significant,
        n_needed=needed,
        verdict=verdict,
    )
