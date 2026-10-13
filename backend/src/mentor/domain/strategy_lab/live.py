"""Paper trading verdicts: when has a plan proven itself live, and when not?

Passing the back-test gate earns a plan the right to be *watched*, nothing
more. It then paper-trades the live market — every signal, fill and exit
recorded as it happens — and is only called **recommended** when that
forward record clears the same kind of bar the history did:

- at least ``MIN_SAMPLE_FOR_VERDICT`` (30) independent paper trades;
- an average R whose 95% interval is above zero after costs (zero R is the
  breakeven: costs are inside every R);
- a t-statistic above the deflated bar for the number of live *looks* ever
  taken across all paper strategies.

**Looks are rationed.** Re-testing a growing record after every trade and
stopping at the first pass is a reliable way to "find" an edge in noise.
So promotion is only considered at checkpoints — every
``_LIVE_CHECKPOINT`` independent trades — and every look, by any
strategy, counts toward the live multiple-testing correction.

**Demotion is quick, re-promotion is not.** A recommended plan loses the
label when a checkpoint no longer clears the bar, or when its trades
since promotion (at least a checkpoint's worth) average zero R or worse.
It keeps paper trading and can earn the label back at a later checkpoint.
A plan whose live record is significantly *negative* is retired outright.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from mentor.domain.stats.significance import MIN_SAMPLE_FOR_VERDICT, MeanVerdict, assess_expectancy
from mentor.domain.strategy_lab.deflation import DeflatedVerdict, TradeStats, deflate, trade_stats

# Promotion is looked at every this many independent paper trades. Pinned.
_LIVE_CHECKPOINT = MIN_SAMPLE_FOR_VERDICT


class LabStatus(StrEnum):
    REJECTED = "rejected"  # failed the back-test gate; never trades
    PAPER = "paper"  # passed the gate; paper trading, not yet proven live
    RECOMMENDED = "recommended"  # proven live at the corrected bar
    DEMOTED = "demoted"  # lost "recommended"; still paper trading
    RETIRED = "retired"  # significantly losing live; stopped

    @property
    def trades(self) -> bool:
        return self in (LabStatus.PAPER, LabStatus.RECOMMENDED, LabStatus.DEMOTED)


class LiveAction(StrEnum):
    NONE = "none"
    PROMOTE = "promote"
    DEMOTE = "demote"
    RETIRE = "retire"


@dataclass(frozen=True, slots=True)
class LiveDecision:
    action: LiveAction
    status: LabStatus  # after the decision
    looks_taken: int  # this strategy's checkpoint looks, after the decision
    looked: bool  # whether this call spent a look
    reason: str
    stats: TradeStats
    expectancy: MeanVerdict
    deflated: DeflatedVerdict | None


def checkpoints_reached(n_independent: int) -> int:
    return n_independent // _LIVE_CHECKPOINT


def next_checkpoint(looks_taken: int) -> int:
    """The independent-trade count at which promotion is next considered."""
    return (looks_taken + 1) * _LIVE_CHECKPOINT


def judge_live(  # noqa: PLR0911 — one return per verdict reads clearer than nesting
    *,
    status: LabStatus,
    rs: Sequence[float],
    since_promotion: Sequence[float],
    looks_taken: int,
    live_looks_ever: int,
) -> LiveDecision:
    """Decide what a paper strategy's record now earns.

    ``rs`` are the R-multiples of its independent closed paper trades in
    time order; ``since_promotion`` the subset after its latest promotion.
    ``live_looks_ever`` counts every checkpoint look already taken by any
    strategy, this one included.
    """
    stats = trade_stats(rs)
    expectancy = assess_expectancy(list(rs), label="paper trades")

    def decide(
        action: LiveAction,
        new_status: LabStatus,
        reason: str,
        *,
        looks: int = looks_taken,
        deflated: DeflatedVerdict | None = None,
    ) -> LiveDecision:
        return LiveDecision(
            action=action,
            status=new_status,
            looks_taken=looks,
            looked=looks != looks_taken,
            reason=reason,
            stats=stats,
            expectancy=expectancy,
            deflated=deflated,
        )

    if not status.trades:
        return decide(LiveAction.NONE, status, "Not paper trading.")

    if expectancy.significant and expectancy.mean < 0:
        return decide(
            LiveAction.RETIRE,
            LabStatus.RETIRED,
            f"Retired: {stats.n} paper trades averaging {stats.mean:+.2f}R — a losing plan "
            f"on the live evidence, not an unlucky one.",
        )

    if (
        status is LabStatus.RECOMMENDED
        and len(since_promotion) >= _LIVE_CHECKPOINT
        and math.fsum(since_promotion) <= 0
    ):
        return decide(
            LiveAction.DEMOTE,
            LabStatus.DEMOTED,
            f"Demoted: its {len(since_promotion)} trades since promotion averaged "
            f"{math.fsum(since_promotion) / len(since_promotion):+.2f}R.",
        )

    due = checkpoints_reached(len(rs))
    if due <= looks_taken:
        return decide(
            LiveAction.NONE,
            status,
            f"{stats.n} independent paper trades; next check at {next_checkpoint(looks_taken)}.",
        )

    deflated = deflate(stats, n_trials=live_looks_ever + (due - looks_taken))
    clears = expectancy.significant and expectancy.mean > 0 and deflated.passed
    summary = (
        f"{stats.n} paper trades averaging {stats.mean:+.2f}R, scoring "
        f"{deflated.t_adjusted:.2f} against a bar of {deflated.bar:.2f}"
    )
    if clears and status is not LabStatus.RECOMMENDED:
        return decide(
            LiveAction.PROMOTE,
            LabStatus.RECOMMENDED,
            f"Recommended: {summary}.",
            looks=due,
            deflated=deflated,
        )
    if not clears and status is LabStatus.RECOMMENDED:
        return decide(
            LiveAction.DEMOTE,
            LabStatus.DEMOTED,
            f"Demoted at its checkpoint: {summary}.",
            looks=due,
            deflated=deflated,
        )
    verdict = "still clears the bar" if clears else "not proven yet"
    return decide(
        LiveAction.NONE, status, f"Checked: {summary} — {verdict}.", looks=due, deflated=deflated
    )
