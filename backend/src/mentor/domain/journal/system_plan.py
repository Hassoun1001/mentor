"""What the system said, frozen — and what it would have done with it.

The Trade plan page is computed on demand and thrown away, so a journal
trade used to have nothing to be compared against. ``PlanSnapshot`` is the
plan exactly as it was shown when the trade was logged. It is written once
and has no update path: a later retrain, a corrected bar or a change of
heart cannot rewrite what the system said.

``play_forward`` then runs that plan over the finished bars that followed
it. It does not reimplement the exit rules. It hands the position to
``PlanBook``, the same code the strategy lab's back-test and paper trader
use, so these rules cannot drift from theirs:

- the stop wins when one bar reaches both stop and target;
- a gap through the stop fills at the open, not at the stop;
- a gap through the target is credited only the target;
- spread and slippage from the pinned ``CostModel`` are charged on both legs.

Two things are specific to a saved plan:

**Closed-market bars do not exist here.** The feed can hold bars stamped
inside the Friday 22:00 to Sunday 22:00 UTC gap. They neither count towards
the time stop nor trigger a stop or target.

**A result is final once something decides it.** A stop or target reached
on a finished bar settles the plan immediately, because nothing later can
change which came first. Only the time stop has to wait for the deadline's
own bar to finish.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from mentor.domain.backtest.costs import CostModel
from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.hours import fx_market_open
from mentor.domain.market.settlement import is_settled
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.simulator import (
    Closed,
    ExitReason,
    Friction,
    OpenTrade,
    PlanBook,
)
from mentor.domain.strategy_lab.spec import ExitRules

_PRICE_PLACES = Decimal("0.00001")
_PIP_PLACES = Decimal("0.1")
_R_PLACES = Decimal("0.0001")

# PlanBook reads only max_bars when it is given no signal; ExitRules still
# insists on a positive stop multiple, which this value satisfies.
_UNUSED_STOP_ATR = 1.0


class PlanStance(StrEnum):
    LONG = "long"
    SHORT = "short"
    STAND_ASIDE = "stand_aside"


def time_stop_deadline(asof: datetime, horizon_bars: int, timeframe: Timeframe) -> datetime:
    """When the last bar of the holding window closes, counting open-market bars only.

    ``asof`` is the bar the plan was made from, so the first bar counted is
    the one after it. A 24-bar plan made on Friday afternoon therefore runs
    into the following week instead of expiring in the weekend gap.
    """
    if horizon_bars < 1:
        raise ValidationError("horizon_bars must be >= 1", field="horizon_bars")
    period = timedelta(seconds=timeframe.seconds)
    bar_ts = asof.astimezone(UTC)
    counted = 0
    while counted < horizon_bars:
        bar_ts += period
        if fx_market_open(bar_ts):
            counted += 1
    return bar_ts + period


@dataclass(frozen=True, slots=True)
class PlanSnapshot:
    """The plan as it was shown. Levels are absent when it said stand aside."""

    symbol: str
    timeframe: Timeframe
    asof: datetime
    model_name: str
    p_up: Decimal
    confidence: Decimal
    stance: PlanStance
    horizon_bars: int
    time_stop_deadline: datetime
    entry: Decimal | None = None
    stop: Decimal | None = None
    target: Decimal | None = None
    reward_multiple: Decimal | None = None
    prediction_id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        if self.asof.tzinfo is None:
            raise ValidationError("asof must be timezone-aware", field="asof")
        if not self.model_name.strip():
            raise ValidationError("model_name is required", field="model_name")
        if not Decimal("0") <= self.p_up <= Decimal("1"):
            raise ValidationError("p_up must be between 0 and 1", field="p_up")
        if not Decimal("0") <= self.confidence <= Decimal("1"):
            raise ValidationError("confidence must be between 0 and 1", field="confidence")
        if self.horizon_bars < 1:
            raise ValidationError("horizon_bars must be >= 1", field="horizon_bars")

        levels = (self.entry, self.stop, self.target, self.reward_multiple)
        if self.stance is PlanStance.STAND_ASIDE:
            if any(level is not None for level in levels):
                raise ValidationError("a stand-aside plan has no levels", field="stance")
            return
        if self.entry is None or self.stop is None or self.target is None:
            raise ValidationError("a trade plan needs entry, stop and target", field="stance")
        if self.reward_multiple is None or self.reward_multiple <= 0:
            raise ValidationError("reward_multiple must be positive", field="reward_multiple")
        sign = 1 if self.stance is PlanStance.LONG else -1
        if sign * (self.entry - self.stop) <= 0:
            raise ValidationError("the stop is on the wrong side of the entry", field="stop")
        if sign * (self.target - self.entry) <= 0:
            raise ValidationError("the target is on the wrong side of the entry", field="target")

    @property
    def direction(self) -> Direction | None:
        if self.stance is PlanStance.STAND_ASIDE:
            return None
        return Direction(self.stance.value)


class SystemStatus(StrEnum):
    PENDING = "pending"
    FINISHED = "finished"
    NO_TRADE = "no_trade"


@dataclass(frozen=True, slots=True)
class SystemResult:
    """What the plan did. ``entry_price`` and ``exit_price`` include costs.

    ``exit_ts`` is the close of the bar that decided the result: the first
    moment a finished bar could have shown it.
    """

    status: SystemStatus
    entry_price: Decimal | None = None
    exit_price: Decimal | None = None
    exit_reason: ExitReason | None = None
    exit_ts: datetime | None = None
    pips: Decimal | None = None
    r: Decimal | None = None


def play_forward(
    plan: PlanSnapshot,
    bars: Sequence[PriceBar],
    *,
    instrument: Instrument,
    now: datetime,
    cost: CostModel | None = None,
) -> SystemResult:
    """Run a saved plan over the bars after it to find what came first.

    Bars may be passed in any order and may extend past the deadline. Bars
    that have not finished, that fall in the closed market, or that belong
    to or precede the plan's own bar are ignored.
    """
    direction = plan.direction
    if direction is None or plan.entry is None or plan.stop is None or plan.target is None:
        return SystemResult(status=SystemStatus.NO_TRADE)

    model = cost or CostModel()
    entry_fill = model.entry_fill_price(
        direction=direction, raw_price=plan.entry, instrument=instrument
    ).quantize(_PRICE_PLACES)

    period = timedelta(seconds=plan.timeframe.seconds)
    last_bar_ts = plan.time_stop_deadline - period
    tradeable = sorted(
        (
            b
            for b in bars
            if b.ts > plan.asof
            and is_settled(b.ts, plan.timeframe, now)
            and fx_market_open(b.ts)
        ),
        key=lambda b: b.ts,
    )
    window = [b for b in tradeable if b.ts <= last_bar_ts]
    pending = SystemResult(status=SystemStatus.PENDING, entry_price=entry_fill)
    if not window:
        return pending

    # The deadline's bar has finished, or a later bar proves it never will
    # (a market holiday or a hole in the feed). Until then the time stop
    # cannot fire, so it is set one bar beyond what has been seen.
    deadline_passed = tradeable[-1].ts >= last_bar_ts
    max_bars = len(window) if deadline_passed else len(window) + 1

    series = BarSeries.from_bars(window)
    exits = ExitRules(stop_atr=_UNUSED_STOP_ATR, target_r=None, max_bars=max_bars)
    friction = Friction.for_instrument(instrument, model)
    book = PlanBook(
        open=OpenTrade(
            direction=direction,
            signal_ts=plan.asof,
            entry_ts=plan.asof,
            entry_price=float(entry_fill),
            stop=float(plan.stop),
            target=float(plan.target),
            bars_held=0,
            reason="saved plan",
        )
    )
    for i in range(len(series)):
        for event in book.on_bar(series, i, signal=None, atr=None, exits=exits, friction=friction):
            if isinstance(event, Closed):
                exit_price = Decimal(str(event.trade.exit_price)).quantize(_PRICE_PLACES)
                return SystemResult(
                    status=SystemStatus.FINISHED,
                    entry_price=entry_fill,
                    exit_price=exit_price,
                    exit_reason=event.trade.exit_reason,
                    exit_ts=event.trade.exit_ts + period,
                    pips=signed_pips(direction, entry_fill, exit_price, instrument),
                    r=Decimal(str(event.trade.r)).quantize(_R_PLACES),
                )
    return pending


def signed_pips(
    direction: Direction, entry: Decimal, exit_price: Decimal, instrument: Instrument
) -> Decimal:
    """Pips made (positive) or lost (negative) going from ``entry`` to ``exit_price``."""
    sign = Decimal("1") if direction is Direction.LONG else Decimal("-1")
    return (sign * (exit_price - entry) / instrument.pip_size).quantize(_PIP_PLACES)
