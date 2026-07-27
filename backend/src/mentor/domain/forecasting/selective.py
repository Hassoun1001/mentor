"""Selective prediction — the model is allowed to say "no opinion".

Every hour the loop runs, it currently produces a direction. Most hours,
EUR/USD direction over the next 24 bars is genuinely close to a coin flip,
and forcing an opinion on those hours drags the average score toward 0.25
no matter how good the features are. That is exactly what the champion
keeps showing: strong features, mediocre aggregate Brier.

The fix is not more features. It is **abstention**. If the model only
speaks when its probability is far enough from 50/50, two things happen:

- the score on the hours it *does* act can be meaningfully better than the
  score across all hours, because the hopeless hours are excluded;
- the hours it skips become visible, which is itself information — a
  system that abstains 80% of the time is telling you something true.

The policy is one number: a **margin** on ``|p_up - 0.5|``. Act at or
above it, stand aside below it.

Two disciplines make this honest rather than a way to manufacture a good
number:

- **Coverage floor.** Without one, the optimiser drives the margin up
  until three lucky samples remain and reports a spectacular Brier. A
  policy must act on at least ``MIN_COVERAGE`` of hours to be considered.
- **Select on one slice, grade on another.** The margin is chosen on the
  calibration slice and reported on the test slice, which the chosen
  margin never saw. A margin picked and graded on the same data is a
  description of that data, not a prediction rule.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from mentor.domain.errors import ValidationError

# A policy acting on less than this share of hours is not evaluated — the
# remaining sample is too small for its score to mean anything.
MIN_COVERAGE = 0.15

# Candidate margins on |p_up - 0.5|. 0.0 is always included so "never
# abstain" competes on equal terms and wins when abstention doesn't help.
_MARGIN_GRID: tuple[float, ...] = tuple(round(0.01 * i, 4) for i in range(0, 26))

# Abstention must buy at least this much Brier on the selection slice.
# Without it the search happily pays a 75% cut in coverage for a 0.0001
# improvement that is pure noise — and noise does not survive to the test
# window. Same order of magnitude as the promotion margin, for the same
# reason: a difference smaller than this is not a difference.
_MIN_GAIN = 0.002


@dataclass(frozen=True, slots=True)
class SelectivePolicy:
    """How the model behaves once it is allowed to decline.

    ``margin`` of 0.0 means it never abstains — coverage is 1.0 and the
    covered metrics equal the all-hours metrics.
    """

    margin: float
    coverage: float
    n_covered: int
    n_total: int
    brier_covered: float
    accuracy_covered: float
    brier_all: float

    @property
    def abstains(self) -> bool:
        return self.margin > 0.0

    @property
    def brier_gain(self) -> float:
        """How much better the covered hours score than all hours.

        Positive means abstention helped. Reported rather than assumed —
        on many windows it is zero or negative, and that is a real answer.
        """
        return self.brier_all - self.brier_covered


def _validate(probs: Sequence[float], outcomes: Sequence[int]) -> None:
    if len(probs) != len(outcomes):
        raise ValidationError(
            "probs and outcomes must be the same length", field="outcomes"
        )
    if not probs:
        raise ValidationError("no samples to grade", field="probs")


def grade_policy(
    margin: float, probs: Sequence[float], outcomes: Sequence[int]
) -> SelectivePolicy:
    """Apply a fixed margin to a slice and measure what it would have done.

    This is the honest half: the margin comes from elsewhere (the
    calibration slice), so the numbers here describe how the rule behaves
    on data it did not choose itself.
    """
    _validate(probs, outcomes)
    if margin < 0:
        raise ValidationError("margin must be >= 0", field="margin")

    n_total = len(probs)
    brier_all = sum((p - y) ** 2 for p, y in zip(probs, outcomes, strict=True)) / n_total

    covered = [
        (p, y) for p, y in zip(probs, outcomes, strict=True) if abs(p - 0.5) >= margin
    ]
    if not covered:
        # A margin nothing clears is a policy that never trades. Report it
        # as such rather than dividing by zero.
        return SelectivePolicy(
            margin=margin,
            coverage=0.0,
            n_covered=0,
            n_total=n_total,
            brier_covered=1.0,
            accuracy_covered=0.0,
            brier_all=brier_all,
        )

    n = len(covered)
    brier = sum((p - y) ** 2 for p, y in covered) / n
    hits = sum(1 for p, y in covered if (p >= 0.5) == (y == 1))
    return SelectivePolicy(
        margin=margin,
        coverage=n / n_total,
        n_covered=n,
        n_total=n_total,
        brier_covered=brier,
        accuracy_covered=hits / n,
        brier_all=brier_all,
    )


def select_margin(
    probs: Sequence[float],
    outcomes: Sequence[int],
    *,
    min_coverage: float = MIN_COVERAGE,
    breakeven: float | None = None,
) -> SelectivePolicy:
    """Choose the abstention margin on this slice.

    Two selection criteria, because "when should the model stay quiet?" has
    a calibration answer and an economic one, and they are not the same
    question.

    **Economic (``breakeven`` supplied).** Abstention exists to skip hours
    the edge cannot pay for. So the rule is: among margins that keep
    coverage above the floor *and* whose covered hits clear the
    spread-adjusted breakeven, act on as many hours as possible — the
    loosest profitable margin, because once a subset pays, more
    opportunities is more money. If no confident subset clears breakeven,
    return the never-abstain policy: speaking on everything and letting the
    promotion gate refuse it is honest, whereas abstaining down to a
    hand-picked profitable-looking sliver is how you manufacture an edge
    that isn't there.

    This is the same correction the promotion gate got — grade against what
    a trade costs, not against a coin flip — pushed one layer earlier, into
    *which hours the model speaks on at all*. Minimising Brier can leave a
    genuinely profitable pocket of hours unselected, because Brier and
    profitability do not perfectly agree; optimising the metric that
    actually pays fixes that.

    **Calibration (``breakeven`` is None — legacy, or hurdle unmeasurable).**
    Minimises Brier over the covered hours, subject to the coverage floor
    and a **minimum improvement** over speaking every hour. That min-gain
    rule is what stops the search being a noise machine: on live EUR/USD
    data an unconstrained search once discarded three-quarters of all hours
    to buy a ~0.0001 Brier improvement that reversed on the test window.

    Either way the margin is chosen here (on the calibration slice) and
    graded elsewhere (on test), so the covered score is a claim about
    future hours, not a description of past ones.

    Returns the never-abstain policy when nothing qualifies.
    """
    _validate(probs, outcomes)
    if not 0 < min_coverage <= 1:
        raise ValidationError("min_coverage must be in (0, 1]", field="min_coverage")
    if breakeven is not None and not 0 < breakeven < 1:
        raise ValidationError("breakeven must be in (0, 1)", field="breakeven")

    speak_always = grade_policy(0.0, probs, outcomes)

    if breakeven is not None:
        return _select_economic(probs, outcomes, min_coverage, breakeven, speak_always)

    required = speak_always.brier_all - _MIN_GAIN
    best: SelectivePolicy | None = None
    for margin in _MARGIN_GRID:
        if margin == 0.0:
            continue  # the incumbent, handled below
        policy = grade_policy(margin, probs, outcomes)
        if policy.coverage < min_coverage:
            continue  # too few hours left for the score to mean anything
        if policy.brier_covered > required:
            continue  # not a big enough win to justify going quiet
        if best is None or policy.brier_covered < best.brier_covered - 1e-9:
            best = policy
    return best if best is not None else speak_always


def _select_economic(
    probs: Sequence[float],
    outcomes: Sequence[int],
    min_coverage: float,
    breakeven: float,
    speak_always: SelectivePolicy,
) -> SelectivePolicy:
    """Loosest margin whose covered hits clear breakeven; else never-abstain.

    Margin 0.0 is a candidate too: if the whole population already pays,
    full coverage wins and the model abstains on nothing.
    """
    best: SelectivePolicy | None = None
    for margin in _MARGIN_GRID:
        policy = grade_policy(margin, probs, outcomes)
        if policy.coverage < min_coverage:
            continue
        if policy.accuracy_covered < breakeven:
            continue  # this subset does not pay for its own spread
        # More coverage beats less (more chances at a positive edge); a
        # tie on coverage breaks toward the better-calibrated subset.
        better_coverage = policy.coverage > best.coverage + 1e-9 if best else True
        tie_break = (
            best is not None
            and abs(policy.coverage - best.coverage) <= 1e-9
            and policy.brier_covered < best.brier_covered - 1e-9
        )
        if best is None or better_coverage or tie_break:
            best = policy
    return best if best is not None else speak_always
