"""Did this trade do what the system said it would?

Three verdicts for a closed trade linked to a saved plan:

- **MATCH** — same direction, same way out, and an R within
  ``MATCH_R_TOLERANCE`` of the system's.
- **PARTIAL** — same direction, but a different way out or a different
  result. Closing early is the usual cause.
- **NO MATCH** — the opposite direction, or a trade the plan said not to take.

``PENDING`` is not a verdict on the trade. It means the system's own version
of the same trade has not finished, so there is nothing yet to compare with.

The journal records an exit price, not why the trade ended, so the way out
is read from the facts: where the price was relative to the trade's own
stop and target, and when it happened relative to the time stop.
"""

from __future__ import annotations

import uuid
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.journal.system_plan import (
    PlanSnapshot,
    PlanStance,
    SystemResult,
    SystemStatus,
    signed_pips,
)
from mentor.domain.journal.trade import Trade, TradeStatus
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.simulator import ExitReason

# A tenth of the amount risked: about three pips on a typical 30-pip stop,
# which is the size of an ordinary difference between two fills.
MATCH_R_TOLERANCE = Decimal("0.10")

# A stop or target rarely fills on the exact price. An exit this close to the
# level, or beyond it, is treated as having been made by that level.
EXIT_AT_LEVEL_PIPS = Decimal("3")

_ZERO = Decimal("0")


class Verdict(StrEnum):
    MATCH = "match"
    PARTIAL = "partial"
    NO_MATCH = "no_match"
    PENDING = "pending"


class ActualExit(StrEnum):
    STOP = "stop"
    TARGET = "target"
    TIME = "time"
    MANUAL = "manual"


_EXIT_WORDS = {
    ActualExit.STOP: "its stop",
    ActualExit.TARGET: "its target",
    ActualExit.TIME: "the time limit",
    ActualExit.MANUAL: "a manual close",
}


def classify_actual_exit(trade: Trade, plan: PlanSnapshot, instrument: Instrument) -> ActualExit:
    """How a closed trade ended, judged against its own levels and the deadline."""
    if trade.actual_exit is None:
        raise ValidationError("the trade has no exit price yet", field="actual_exit")
    sign = Decimal("1") if trade.direction is Direction.LONG else Decimal("-1")
    slack = EXIT_AT_LEVEL_PIPS * instrument.pip_size
    if sign * (trade.actual_exit - trade.planned_stop) <= slack:
        return ActualExit.STOP
    target = trade.planned_target
    if target is not None and sign * (target - trade.actual_exit) <= slack:
        return ActualExit.TARGET
    if trade.exit_ts is not None:
        one_bar = timedelta(seconds=plan.timeframe.seconds)
        if abs(trade.exit_ts - plan.time_stop_deadline) <= one_bar:
            return ActualExit.TIME
    return ActualExit.MANUAL


@dataclass(frozen=True, slots=True)
class TradeComparison:
    """One linked trade set against the system's version of it.

    The actual fields are empty until the trade has them, and ``verdict`` is
    ``None`` until the trade is closed.

    ``entry_slippage_pips`` is positive when the fill was worse than the
    system's. ``r_difference`` is actual minus system, so positive means the
    way the trade was handled added to the result.
    """

    trade_id: uuid.UUID
    plan: PlanSnapshot
    system: SystemResult
    verdict: Verdict | None
    explanation: str
    actual_direction: Direction
    actual_entry: Decimal | None
    actual_exit: Decimal | None
    actual_exit_reason: ActualExit | None
    actual_exit_ts: datetime | None
    actual_pips: Decimal | None
    actual_r: Decimal | None
    entry_slippage_pips: Decimal | None
    r_difference: Decimal | None


def compare_trade(
    trade: Trade, plan: PlanSnapshot, system: SystemResult, instrument: Instrument
) -> TradeComparison:
    """Set one trade beside the system's version of it."""
    slippage = None
    if (
        plan.direction is trade.direction
        and trade.actual_entry is not None
        and system.entry_price is not None
    ):
        # Worse means paying more on a buy or receiving less on a sell, which
        # is the same sum as the pips "made" from the system's fill to yours.
        slippage = signed_pips(trade.direction, system.entry_price, trade.actual_entry, instrument)

    if trade.status is not TradeStatus.CLOSED or trade.actual_exit is None:
        return TradeComparison(
            trade_id=trade.id,
            plan=plan,
            system=system,
            verdict=None,
            explanation=_not_closed_text(trade, plan),
            actual_direction=trade.direction,
            actual_entry=trade.actual_entry,
            actual_exit=None,
            actual_exit_reason=None,
            actual_exit_ts=None,
            actual_pips=None,
            actual_r=None,
            entry_slippage_pips=slippage,
            r_difference=None,
        )

    if trade.actual_entry is None or trade.realised_r is None:
        raise ValidationError(f"closed trade {trade.id} is missing its fill or R", field="status")
    actual_r = trade.realised_r
    actual_exit = classify_actual_exit(trade, plan, instrument)
    system_r = _ZERO if system.status is SystemStatus.NO_TRADE else system.r
    verdict, explanation = _judge(trade, plan, system, actual_exit, actual_r)
    return TradeComparison(
        trade_id=trade.id,
        plan=plan,
        system=system,
        verdict=verdict,
        explanation=explanation,
        actual_direction=trade.direction,
        actual_entry=trade.actual_entry,
        actual_exit=trade.actual_exit,
        actual_exit_reason=actual_exit,
        actual_exit_ts=trade.exit_ts,
        actual_pips=signed_pips(
            trade.direction, trade.actual_entry, trade.actual_exit, instrument
        ),
        actual_r=actual_r,
        entry_slippage_pips=slippage,
        r_difference=None if system_r is None else actual_r - system_r,
    )


def _judge(
    trade: Trade,
    plan: PlanSnapshot,
    system: SystemResult,
    actual_exit: ActualExit,
    actual_r: Decimal,
) -> tuple[Verdict, str]:
    if plan.stance is PlanStance.STAND_ASIDE:
        return (
            Verdict.NO_MATCH,
            f"The system said to stand aside and a {trade.direction.value} trade was taken anyway.",
        )
    if plan.direction is not trade.direction:
        return (
            Verdict.NO_MATCH,
            f"The system said {plan.stance.value} and this trade went {trade.direction.value}.",
        )
    if system.status is not SystemStatus.FINISHED or system.exit_reason is None:
        return (
            Verdict.PENDING,
            "Your trade is closed, but the system's version is still running. It finishes "
            f"by {_when(plan.time_stop_deadline)} at the latest.",
        )
    if system.r is None or system.exit_ts is None:
        raise ValidationError("a finished system result needs an R and an exit time", field="r")

    gap = actual_r - system.r
    same_exit = actual_exit.value == system.exit_reason.value
    if same_exit and abs(gap) <= MATCH_R_TOLERANCE:
        return (
            Verdict.MATCH,
            f"Same direction, both ended at {_system_words(system.exit_reason)}, and your "
            f"result was within {MATCH_R_TOLERANCE}R of the system's.",
        )
    if same_exit:
        return (
            Verdict.PARTIAL,
            f"Same direction and both ended at {_system_words(system.exit_reason)}, but your "
            f"result was {abs(gap):.2f}R {'better' if gap > 0 else 'worse'} than the system's. "
            "Compare the entry and exit prices below to see where it came from.",
        )
    return (
        Verdict.PARTIAL,
        f"Same direction, but {_exit_difference(trade, system, actual_exit)} "
        f"You made {_signed_r(actual_r)}; the system made {_signed_r(system.r)}.",
    )


def _exit_difference(trade: Trade, system: SystemResult, actual_exit: ActualExit) -> str:
    system_way = _system_words(system.exit_reason)
    if actual_exit is ActualExit.MANUAL and trade.exit_ts is not None and system.exit_ts:
        hours = (system.exit_ts - trade.exit_ts).total_seconds() / 3600
        if abs(hours) < 1:
            return f"you closed by hand within an hour of the system's exit at {system_way}."
        when = "before" if hours > 0 else "after"
        return (
            f"you closed by hand about {abs(hours):.0f}h {when} the system's exit at {system_way}."
        )
    return f"yours ended at {_EXIT_WORDS[actual_exit]} and the system's at {system_way}."


def _system_words(reason: ExitReason | None) -> str:
    return _EXIT_WORDS[ActualExit(reason.value)] if reason else "no exit yet"


def _not_closed_text(trade: Trade, plan: PlanSnapshot) -> str:
    if plan.stance is PlanStance.STAND_ASIDE:
        return "The system said to stand aside. Close the trade to see the comparison."
    deadline = _when(plan.time_stop_deadline)
    if trade.status is TradeStatus.OPEN:
        return f"Trade still open. The system's time limit for this plan is {deadline}."
    return f"Not opened yet. The system's time limit for this plan is {deadline}."


def _when(moment: datetime) -> str:
    return moment.strftime("%a %d %b %H:%M UTC")


def _signed_r(value: Decimal) -> str:
    return f"{value:+.2f}R"


@dataclass(frozen=True, slots=True)
class ComparisonSummary:
    """Totals across closed linked trades.

    ``compared`` counts only trades with both results known, so the R totals
    and their difference always cover the same trades. A stand-aside plan
    counts as 0R for the system: not trading is a result.
    """

    matches: int
    partials: int
    no_matches: int
    pending: int
    unlinked: int
    compared: int
    system_r: Decimal
    actual_r: Decimal
    execution_r: Decimal
    headline: str


def summarise(
    comparisons: Sequence[TradeComparison], *, unlinked_closed: int = 0
) -> ComparisonSummary:
    """Add up the verdicts and what the differences were worth."""
    counts = Counter(c.verdict for c in comparisons if c.verdict is not None)
    both_known = [c for c in comparisons if c.r_difference is not None and c.actual_r is not None]
    actual_total = sum((c.actual_r for c in both_known if c.actual_r is not None), _ZERO)
    difference = sum((c.r_difference for c in both_known if c.r_difference is not None), _ZERO)
    system_total = actual_total - difference
    return ComparisonSummary(
        matches=counts[Verdict.MATCH],
        partials=counts[Verdict.PARTIAL],
        no_matches=counts[Verdict.NO_MATCH],
        pending=counts[Verdict.PENDING],
        unlinked=unlinked_closed,
        compared=len(both_known),
        system_r=system_total,
        actual_r=actual_total,
        execution_r=difference,
        headline=_headline(
            len(both_known), counts[Verdict.PENDING], system_total, actual_total, difference
        ),
    )


def _headline(
    compared: int, waiting: int, system: Decimal, actual: Decimal, difference: Decimal
) -> str:
    if compared == 0 and waiting > 0:
        trades = "trade is" if waiting == 1 else "trades are"
        return f"{waiting} closed {trades} waiting for the system's version to finish."
    if compared == 0:
        return "Nothing to compare yet. Log a trade from the Trade plan page and close it."
    trades = "trade" if compared == 1 else "trades"
    base = (
        f"Over {compared} compared {trades} you made {_signed_r(actual)} and the system "
        f"made {_signed_r(system)}. "
    )
    if difference > 0:
        return base + f"The way you traded them added {difference:.2f}R."
    if difference < 0:
        return base + f"The way you traded them cost {abs(difference):.2f}R."
    return base + "The way you traded them made no difference."
