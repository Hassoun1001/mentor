"""Loss root causes — a fixed taxonomy instead of free-text tags.

A journal that lets you type anything into "what went wrong" produces
"bad entry", "bad-entry", "entry was bad" and "rushed" — four spellings of
one habit, which then never shows up as a pattern. The whole point of
tagging losses is to count them, and you can only count a closed set.

So the taxonomy is fixed and small. Each tag names a *cause you control*,
carries the question that identifies it, and carries the fix. Two design
choices are worth defending:

- **`good_process` is a tag.** Most losses are not mistakes. A trade that
  followed the plan and lost is the cost of doing business, and lumping it
  in with rule violations teaches you to distrust a system that was
  working. Separating the two is the difference between a journal that
  improves you and one that just makes you anxious.
- **`rule_violation` is separate from everything else.** A false breakout
  is the market fooling you; trading without a stop is you fooling
  yourself. They need different responses, so they get different tags.

The breakdown ranks causes by **R bled**, not by count — five small
timing errors matter less than one oversized position, and a list sorted
by frequency would hide that.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.journal.trade import Trade, TradeStatus


class MistakeTag(StrEnum):
    """The closed set of root causes a closed trade may be tagged with."""

    GOOD_PROCESS = "good_process"
    FALSE_BREAKOUT = "false_breakout"
    NEWS_SHOCK = "news_shock"
    SPREAD_OR_SLIPPAGE = "spread_or_slippage"
    BAD_TIMING = "bad_timing"
    COUNTER_TREND = "counter_trend"
    OVERSIZED = "oversized"
    STOP_TOO_TIGHT = "stop_too_tight"
    MOVED_STOP = "moved_stop"
    NO_SETUP = "no_setup"
    REVENGE_TRADE = "revenge_trade"
    RULE_VIOLATION = "rule_violation"
    HELD_PAST_HORIZON = "held_past_horizon"


@dataclass(frozen=True, slots=True)
class MistakeDefinition:
    tag: MistakeTag
    label: str
    question: str  # the question that identifies this cause
    fix: str  # what to do differently next time
    is_process_error: bool  # False = the market beat a sound plan


_DEFINITIONS: tuple[MistakeDefinition, ...] = (
    MistakeDefinition(
        tag=MistakeTag.GOOD_PROCESS,
        label="Good process, bad outcome",
        question=(
            "Did you follow the plan exactly — right setup, right size, stop where you "
            "said it would be — and still lose?"
        ),
        fix=(
            "Nothing. This is the cost of doing business. Any edge that wins 55% of the "
            "time loses 45 trades in 100, and none of those 45 are mistakes. Changing a "
            "working system because of one loss is itself the mistake."
        ),
        is_process_error=False,
    ),
    MistakeDefinition(
        tag=MistakeTag.FALSE_BREAKOUT,
        label="False breakout",
        question=(
            "Did price break the level you were trading, pull you in, and then snap back "
            "through it in the other direction?"
        ),
        fix=(
            "Wait for a candle to close beyond the level rather than entering on the "
            "first touch, or wait for the retest. You will miss some real moves — that "
            "is the price of not being the liquidity."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.NEWS_SHOCK,
        label="News shock",
        question=(
            "Did a scheduled release or a headline move the market against you within "
            "minutes of the entry?"
        ),
        fix=(
            "Check the economic calendar before entering. If a high-impact event lands "
            "inside your holding horizon, either stand aside or halve the size — the "
            "spread widens and the stop gets jumped, not filled."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.SPREAD_OR_SLIPPAGE,
        label="Spread or slippage",
        question=(
            "Did the fill, the spread or the gap cost you a meaningful slice of the "
            "trade before it even moved?"
        ),
        fix=(
            "Avoid the session open, the rollover window and thin hours. On a 20-pip "
            "target a 3-pip spread is 15% of the trade gone at entry."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.BAD_TIMING,
        label="Right idea, wrong moment",
        question=(
            "Did the market eventually go where you thought — but only after stopping "
            "you out first?"
        ),
        fix=(
            "The read was fine; the entry was early. Wait for confirmation, or size the "
            "stop off volatility rather than off the nearest round number."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.COUNTER_TREND,
        label="Fought the trend",
        question=(
            "Were you selling into a market making higher highs, or buying one making "
            "lower lows?"
        ),
        fix=(
            "Check the higher timeframe before the entry. Picking tops and bottoms feels "
            "clever and pays badly — trade with the structure or stand aside."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.OVERSIZED,
        label="Position too large",
        question=(
            "Did this single trade risk more than your normal percentage — or did the "
            "size make you watch it tick by tick?"
        ),
        fix=(
            "Size from the stop distance and a fixed risk percent, every time. An "
            "oversized position turns a normal loss into one you need a winning streak "
            "to repair, and it makes you manage the trade out of fear."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.STOP_TOO_TIGHT,
        label="Stop too tight",
        question=(
            "Was your stop inside the market's normal noise for that hour — stopped out "
            "by a wick, not by a reversal?"
        ),
        fix=(
            "Place the stop beyond the structure and let position size shrink to keep "
            "risk constant. A tight stop with big size is the same bet as a wide stop "
            "with small size, except it loses to noise."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.MOVED_STOP,
        label="Moved the stop away",
        question="Did you widen or cancel the stop while the trade was going against you?",
        fix=(
            "This is the single most account-destroying habit in trading, because it "
            "works most of the time — right up to the trade that doesn't come back. "
            "Set it once. Move it only toward profit, never away from price."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.NO_SETUP,
        label="No real setup",
        question=(
            "Be honest: if you had to write the reason for this trade *before* taking "
            "it, would it have convinced you?"
        ),
        fix=(
            "Boredom is not a signal. A written checklist that must pass before you "
            "click is the only reliable cure — the point of the plan is to make the "
            "decision while you are calm."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.REVENGE_TRADE,
        label="Revenge trade",
        question="Did you take this one to win back what the last one lost?",
        fix=(
            "Stop for the day after two losses. The market does not know it owes you "
            "anything, and trades taken to repair a number are sized and timed by "
            "emotion rather than by the plan."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.RULE_VIOLATION,
        label="Broke your own rule",
        question=(
            "Did you break a rule you had already written down — no stop, over the daily "
            "limit, traded a symbol or session you had excluded?"
        ),
        fix=(
            "The rule was not the problem; keeping it was. Reduce size until the rules "
            "are automatic again. A system you follow 80% of the time is not your system."
        ),
        is_process_error=True,
    ),
    MistakeDefinition(
        tag=MistakeTag.HELD_PAST_HORIZON,
        label="Held past the forecast horizon",
        question=(
            "Did you keep the trade open long after the horizon it was based on had "
            "passed, hoping it would come back?"
        ),
        fix=(
            "A forecast for the next 24 bars says nothing about bar 200. When the "
            "horizon expires and neither stop nor target is hit, close it — that is "
            "what the time stop on the trade plan is for."
        ),
        is_process_error=True,
    ),
)

_BY_TAG: dict[MistakeTag, MistakeDefinition] = {d.tag: d for d in _DEFINITIONS}


def mistake_catalog() -> tuple[MistakeDefinition, ...]:
    """The full taxonomy, in teaching order."""
    return _DEFINITIONS


def definition_for(tag: MistakeTag) -> MistakeDefinition:
    return _BY_TAG[tag]


def normalise_tags(raw: Iterable[str]) -> tuple[str, ...]:
    """Validate free-form input against the taxonomy, de-duplicated.

    Accepts any case and either hyphens or underscores, so an old
    ``false-breakout`` row still resolves. Anything outside the taxonomy is
    rejected loudly rather than silently stored — a tag nobody can count is
    worse than no tag.
    """
    seen: list[str] = []
    for item in raw:
        key = item.strip().lower().replace("-", "_").replace(" ", "_")
        if not key:
            continue
        try:
            tag = MistakeTag(key)
        except ValueError as exc:
            allowed = ", ".join(t.value for t in MistakeTag)
            raise ValidationError(
                f"unknown mistake tag '{item}' — choose from: {allowed}",
                field="mistake_tags",
            ) from exc
        if tag.value not in seen:
            seen.append(tag.value)
    return tuple(seen)


@dataclass(frozen=True, slots=True)
class RootCause:
    tag: MistakeTag
    label: str
    fix: str
    is_process_error: bool
    occurrences: int
    r_lost: Decimal  # positive magnitude of R given up on trades carrying this tag


@dataclass(frozen=True, slots=True)
class RootCauseBreakdown:
    closed_losses: int
    tagged_losses: int
    untagged_losses: int
    process_error_losses: int  # losses with at least one controllable cause
    good_process_losses: int  # losses that followed the plan
    causes: tuple[RootCause, ...]  # ranked by R bled, worst first

    @property
    def worst(self) -> RootCause | None:
        return self.causes[0] if self.causes else None


def compute_root_causes(trades: Sequence[Trade]) -> RootCauseBreakdown:
    """Aggregate the tags on losing trades into a ranked list of causes.

    Only losses are counted. A tag on a winner tells you nothing about what
    to fix, and including winners would let a lucky outcome hide a bad
    habit. When a loss carries several tags, its full R is attributed to
    each — the aim is to find the habit that shows up in your worst
    trades, not to divide blame into neat fractions.
    """
    losses = [
        t
        for t in trades
        if t.status is TradeStatus.CLOSED and t.realised_r is not None and t.realised_r < 0
    ]

    counts: dict[MistakeTag, int] = {}
    bled: dict[MistakeTag, Decimal] = {}
    tagged = 0
    process_errors = 0
    good_process = 0

    for trade in losses:
        tags: list[MistakeTag] = []
        for raw in trade.mistake_tags:
            try:
                tags.append(MistakeTag(raw.strip().lower().replace("-", "_")))
            except ValueError:
                continue  # legacy free-text tag — ignored, never crashes the review
        if not tags:
            continue
        tagged += 1
        magnitude = -(trade.realised_r or Decimal("0"))
        if any(_BY_TAG[t].is_process_error for t in tags):
            process_errors += 1
        if MistakeTag.GOOD_PROCESS in tags:
            good_process += 1
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1
            bled[tag] = bled.get(tag, Decimal("0")) + magnitude

    causes = tuple(
        sorted(
            (
                RootCause(
                    tag=tag,
                    label=_BY_TAG[tag].label,
                    fix=_BY_TAG[tag].fix,
                    is_process_error=_BY_TAG[tag].is_process_error,
                    occurrences=count,
                    r_lost=bled[tag],
                )
                for tag, count in counts.items()
            ),
            key=lambda c: (c.r_lost, c.occurrences),
            reverse=True,
        )
    )

    return RootCauseBreakdown(
        closed_losses=len(losses),
        tagged_losses=tagged,
        untagged_losses=len(losses) - tagged,
        process_error_losses=process_errors,
        good_process_losses=good_process,
        causes=causes,
    )
