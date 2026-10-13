"""What a trading plan is, as a value.

A professional's plan answers five questions before any money moves:
when do I get in, where am I wrong, where do I take profit, how long do I
give it, and how much do I risk. ``StrategySpec`` is those five answers
plus a sixth the lab insists on — *why might this work at all?* — written
in plain words, because an idea that cannot state its own reason is
usually a pattern found by staring at noise.

- **Entry** — an ``EntryRule``: a parameterised, pure function from bars
  to signals. It sees only the past (``indicators.py`` explains how that
  is enforced) and may name a structural stop or target, such as the far
  side of a range.
- **Exits** — ``ExitRules``: an ATR-based stop, an R-multiple target and a
  time stop. A rule's structural levels override the first two.
- **Sizing** — the existing risk engine (``calculate_position``), never a
  second formula. Results are graded in R, which is independent of size;
  sizing is what a paper position would have been on a stated account.
- **Timeframe** and **hypothesis**.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from decimal import Decimal
from typing import Any, ClassVar, cast

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.market.bars import Timeframe
from mentor.domain.money import Money, Percent
from mentor.domain.risk.position_sizing import (
    Direction,
    PositionSizing,
    RiskInputs,
    calculate_position,
)
from mentor.domain.strategy_lab.series import BarSeries

# The "1–2% rule". A plan that needs more than this per trade to be worth
# running is a plan about leverage, not about an edge.
_MAX_RISK_FRACTION = Decimal("0.02")

ParamValue = int | float | None


@dataclass(frozen=True, slots=True)
class Signal:
    """A rule's decision at a bar's close: enter at the next bar's open."""

    direction: Direction
    reason: str
    stop: float | None = None  # structural stop; None → the ATR stop from ExitRules
    target: float | None = None  # structural target; None → the R target from ExitRules


class EntryRule(ABC):
    """A parameterised entry rule. Subclasses are frozen dataclasses.

    ``signals`` must return one entry per bar, ``None`` until ``lookback``
    bars exist, and the value at bar *i* may depend only on bars
    ``i - lookback + 1 .. i``. The lab's tests check
    every registered rule for both properties, so a rule that peeks ahead
    or remembers too much fails the suite rather than flattering a result.
    """

    family: ClassVar[str]
    # Whether the rule's signals name their own stop / target levels, so the
    # plain-language plan does not describe an ATR stop the rule overrides.
    names_stop: ClassVar[bool] = False
    names_target: ClassVar[bool] = False

    @property
    @abstractmethod
    def lookback(self) -> int:
        """Bars of history (including the current one) a signal depends on."""

    @abstractmethod
    def signals(self, series: BarSeries) -> list[Signal | None]: ...

    @abstractmethod
    def describe(self) -> str:
        """The entry, in a sentence a non-trader can follow."""

    def params(self) -> dict[str, ParamValue]:
        # Every rule is a frozen dataclass; its fields are its parameters.
        return {f.name: getattr(self, f.name) for f in fields(cast("Any", self))}


@dataclass(frozen=True, slots=True)
class ExitRules:
    stop_atr: float  # stop distance in multiples of ATR
    target_r: float | None  # take profit at this multiple of the risk; None = no target
    max_bars: int  # time stop: close at the end of this many bars in the trade
    atr_period: int = 14

    def __post_init__(self) -> None:
        if self.stop_atr <= 0:
            raise ValidationError("stop_atr must be positive", field="stop_atr")
        if self.target_r is not None and self.target_r <= 0:
            raise ValidationError("target_r must be positive", field="target_r")
        if self.max_bars < 1:
            raise ValidationError("max_bars must be >= 1", field="max_bars")
        if self.atr_period < 1:
            raise ValidationError("atr_period must be >= 1", field="atr_period")

    def describe(
        self, timeframe: Timeframe, *, names_stop: bool = False, names_target: bool = False
    ) -> str:
        unit = _unit(timeframe)
        ranges = _ADJECTIVE.get(timeframe, "bar")
        stop = (
            "keep the stop where the rule puts it"
            if names_stop
            else f"put the stop {self.stop_atr:g}× the average {ranges} range away"
        )
        if names_target:
            target = "take profit where the rule aims"
        elif self.target_r is not None:
            target = f"take profit at {self.target_r:g}× the amount risked"
        else:
            target = "set no fixed profit target"
        return f"{stop}, {target}, and give up after {self.max_bars} {unit}s"


def _unit(timeframe: Timeframe) -> str:
    return {Timeframe.D1: "day", Timeframe.H1: "hour"}.get(timeframe, "bar")


_ADJECTIVE = {Timeframe.D1: "daily", Timeframe.H1: "hourly"}


@dataclass(frozen=True, slots=True)
class StrategySpec:
    rule: EntryRule
    exits: ExitRules
    timeframe: Timeframe
    hypothesis: str
    risk_fraction: Decimal = Decimal("0.01")

    def __post_init__(self) -> None:
        if not self.hypothesis.strip():
            raise ValidationError("a plan must state why it might work", field="hypothesis")
        if not (Decimal("0") < self.risk_fraction <= _MAX_RISK_FRACTION):
            raise ValidationError(
                f"risk_fraction must be in (0, {_MAX_RISK_FRACTION}]", field="risk_fraction"
            )

    @property
    def family(self) -> str:
        return self.rule.family

    @property
    def lookback(self) -> int:
        """History needed before the plan can act — entry rule or ATR, whichever is longer."""
        return max(self.rule.lookback, self.exits.atr_period + 1)

    def params(self) -> dict[str, ParamValue]:
        return {
            **self.rule.params(),
            "stop_atr": self.exits.stop_atr,
            "target_r": self.exits.target_r,
            "max_bars": self.exits.max_bars,
            "atr_period": self.exits.atr_period,
        }

    def describe(self) -> str:
        risk_pct = f"{(self.risk_fraction * 100).normalize():f}%"
        exits = self.exits.describe(
            self.timeframe, names_stop=self.rule.names_stop, names_target=self.rule.names_target
        )
        return (
            f"{self.rule.describe()} Then {exits}. "
            f"Risk {risk_pct} of the account per trade."
        )

    def size(
        self,
        *,
        account: Money,
        entry: Decimal,
        stop: Decimal,
        target: Decimal | None,
        direction: Direction,
        instrument: Instrument,
    ) -> PositionSizing:
        """Position size from the same risk engine the trade planner uses."""
        return calculate_position(
            RiskInputs(
                account_balance=account,
                risk=Percent(self.risk_fraction),
                entry=entry,
                stop=stop,
                instrument=instrument,
                direction=direction,
                target=target,
            )
        )
