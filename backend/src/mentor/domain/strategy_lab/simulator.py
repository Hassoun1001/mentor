"""One plan, one position, bar by bar — shared by back-test and paper trading.

``PlanBook`` holds the only state a plan has between bars: an order waiting
to be filled and a position that is open. ``on_bar`` advances it by one
settled bar. The back-test calls it over years of history; the live paper
trader rebuilds the book from the database and calls the *same method* on
each new bar. There is no second implementation that could drift, so a
paper record is the back-tested plan meeting the future, not a cousin of it.

The order of events inside a bar matches ``domain/backtest/engine.py``:

1. **Fill** last bar's signal at this bar's open, worse by half the spread
   plus slippage. If the market opened beyond the stop or the target the
   plan is void and the order is cancelled — a trader does not chase.
2. **Exits** against this bar's range. When the range covers both stop and
   target the stop wins. A gap through the stop fills at the open, not at
   the stop; a gap through the target is credited only the target.
   Then the time stop, at this bar's close.
3. **New signal** at this bar's close, only when flat: one position at a
   time, so trades never overlap in market time.

Costs are the pinned ``CostModel``, charged on both legs. A stop closer
than the risk engine's minimum sensible distance is refused, because the
spread alone would decide that trade.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from mentor.domain.backtest.costs import CostModel
from mentor.domain.instruments import Instrument
from mentor.domain.risk.position_sizing import _MIN_SENSIBLE_STOP_PIPS, Direction
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.series import BarSeries
from mentor.domain.strategy_lab.spec import ExitRules, Signal, StrategySpec


class ExitReason(StrEnum):
    STOP = "stop"
    TARGET = "target"
    TIME = "time"


@dataclass(frozen=True, slots=True)
class Friction:
    """Per-side cost and minimum stop, in price units, for one instrument."""

    per_side: float  # half the spread plus one slippage leg
    min_stop: float

    @classmethod
    def for_instrument(cls, instrument: Instrument, cost: CostModel | None = None) -> Friction:
        model = cost or CostModel()
        pip = float(instrument.pip_size)
        return cls(
            per_side=float(model.spread_pips / 2 + model.slippage_pips) * pip,
            min_stop=float(_MIN_SENSIBLE_STOP_PIPS) * pip,
        )


@dataclass(frozen=True, slots=True)
class PendingEntry:
    direction: Direction
    signal_ts: datetime
    stop: float
    target: float | None
    reason: str


@dataclass(frozen=True, slots=True)
class OpenTrade:
    direction: Direction
    signal_ts: datetime
    entry_ts: datetime
    entry_price: float  # the fill, costs included
    stop: float
    target: float | None
    bars_held: int
    reason: str

    @property
    def risk(self) -> float:
        return abs(self.entry_price - self.stop)


@dataclass(frozen=True, slots=True)
class PlanTrade:
    """A finished trade. ``r`` is net of every cost."""

    direction: Direction
    signal_ts: datetime
    entry_ts: datetime
    exit_ts: datetime
    entry_price: float
    exit_price: float
    stop: float
    target: float | None
    r: float
    exit_reason: ExitReason
    bars_held: int
    reason: str


@dataclass(frozen=True, slots=True)
class Signalled:
    pending: PendingEntry


@dataclass(frozen=True, slots=True)
class Filled:
    trade: OpenTrade


@dataclass(frozen=True, slots=True)
class Cancelled:
    pending: PendingEntry
    ts: datetime
    why: str


@dataclass(frozen=True, slots=True)
class Closed:
    trade: PlanTrade


BookEvent = Signalled | Filled | Cancelled | Closed


def _sign(direction: Direction) -> float:
    return 1.0 if direction is Direction.LONG else -1.0


@dataclass(slots=True)
class PlanBook:
    pending: PendingEntry | None = None
    open: OpenTrade | None = None

    def on_bar(
        self,
        series: BarSeries,
        i: int,
        *,
        signal: Signal | None,
        atr: float | None,
        exits: ExitRules,
        friction: Friction,
    ) -> list[BookEvent]:
        events: list[BookEvent] = []
        self._fill(series, i, friction, events)
        self._exit(series, i, exits, friction, events)
        self._consider(series, i, signal, atr, exits, friction, events)
        return events

    # ---- the three steps ----

    def _fill(
        self, series: BarSeries, i: int, friction: Friction, events: list[BookEvent]
    ) -> None:
        pending = self.pending
        if pending is None:
            return
        self.pending = None
        sign = _sign(pending.direction)
        fill = series.open[i] + sign * friction.per_side
        risk = sign * (fill - pending.stop)
        why: str | None = None
        if risk <= 0:
            why = "the market opened beyond the stop"
        elif risk < friction.min_stop:
            why = "the fill landed too close to the stop to size honestly"
        elif pending.target is not None and sign * (pending.target - fill) <= 0:
            why = "the market opened beyond the target"
        if why is not None:
            events.append(Cancelled(pending=pending, ts=series.ts[i], why=why))
            return
        self.open = OpenTrade(
            direction=pending.direction,
            signal_ts=pending.signal_ts,
            entry_ts=series.ts[i],
            entry_price=fill,
            stop=pending.stop,
            target=pending.target,
            bars_held=0,
            reason=pending.reason,
        )
        events.append(Filled(trade=self.open))

    def _exit(
        self,
        series: BarSeries,
        i: int,
        exits: ExitRules,
        friction: Friction,
        events: list[BookEvent],
    ) -> None:
        trade = self.open
        if trade is None:
            return
        trade = replace(trade, bars_held=trade.bars_held + 1)
        long = trade.direction is Direction.LONG
        bar_open, high, low = series.open[i], series.high[i], series.low[i]

        raw: float | None = None
        reason: ExitReason | None = None
        if (low <= trade.stop) if long else (high >= trade.stop):
            raw = min(trade.stop, bar_open) if long else max(trade.stop, bar_open)
            reason = ExitReason.STOP
        elif trade.target is not None and (
            (high >= trade.target) if long else (low <= trade.target)
        ):
            raw, reason = trade.target, ExitReason.TARGET
        elif trade.bars_held >= exits.max_bars:
            raw, reason = series.close[i], ExitReason.TIME

        if raw is None or reason is None:
            self.open = trade
            return
        sign = _sign(trade.direction)
        exit_price = raw - sign * friction.per_side
        self.open = None
        events.append(
            Closed(
                trade=PlanTrade(
                    direction=trade.direction,
                    signal_ts=trade.signal_ts,
                    entry_ts=trade.entry_ts,
                    exit_ts=series.ts[i],
                    entry_price=trade.entry_price,
                    exit_price=exit_price,
                    stop=trade.stop,
                    target=trade.target,
                    r=sign * (exit_price - trade.entry_price) / trade.risk,
                    exit_reason=reason,
                    bars_held=trade.bars_held,
                    reason=trade.reason,
                )
            )
        )

    def _consider(
        self,
        series: BarSeries,
        i: int,
        signal: Signal | None,
        atr: float | None,
        exits: ExitRules,
        friction: Friction,
        events: list[BookEvent],
    ) -> None:
        if signal is None or self.open is not None or self.pending is not None:
            return
        if atr is None or atr <= 0:
            return
        close = series.close[i]
        sign = _sign(signal.direction)
        stop = signal.stop if signal.stop is not None else close - sign * exits.stop_atr * atr
        distance = sign * (close - stop)
        if distance < friction.min_stop:
            return  # wrong side of the market, or inside the spread
        target = signal.target
        if target is None and exits.target_r is not None:
            target = close + sign * exits.target_r * distance
        if target is not None and sign * (target - close) <= 0:
            return
        self.pending = PendingEntry(
            direction=signal.direction,
            signal_ts=series.ts[i],
            stop=stop,
            target=target,
            reason=signal.reason,
        )
        events.append(Signalled(pending=self.pending))


@dataclass(frozen=True, slots=True)
class SimulationResult:
    trades: tuple[PlanTrade, ...]  # closed trades only; an unfinished trade has no outcome
    open_trade: OpenTrade | None
    cancelled: int


def simulate(spec: StrategySpec, series: BarSeries, friction: Friction) -> SimulationResult:
    """Run one plan over a whole series."""
    signals = spec.rule.signals(series)
    atrs = indicators.atr(series.high, series.low, series.close, spec.exits.atr_period)
    book = PlanBook()
    trades: list[PlanTrade] = []
    cancelled = 0
    for i in range(len(series)):
        for event in book.on_bar(
            series, i, signal=signals[i], atr=atrs[i], exits=spec.exits, friction=friction
        ):
            if isinstance(event, Closed):
                trades.append(event.trade)
            elif isinstance(event, Cancelled):
                cancelled += 1
    return SimulationResult(trades=tuple(trades), open_trade=book.open, cancelled=cancelled)
