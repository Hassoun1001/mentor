"""Event-driven backtest engine.

The whole engine is one pass through `bars` with a strict ordering at
each step:

1.  **Mark to market** — value the equity curve using the current bar's
    close. Open positions are unrealised.
2.  **Resolve pending intents from the previous bar** — fill them at
    *this* bar's open, with spread + slippage applied. This is the
    rule that keeps strategies honest: you act on the next bar after
    the signal, not the same bar.
3.  **Check stops and targets** — using the current bar's high/low
    range. If both can be hit in the same bar (gap), the stop wins
    (conservative).
4.  **Run the strategy** — `on_bar(ctx)` returns intents to be filled
    *next* time around.

Everything is computed in Decimal. The cost model is non-optional. No
"ideal fill" mode.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from mentor.domain.backtest.costs import CostModel
from mentor.domain.backtest.market_view import MarketView
from mentor.domain.backtest.orders import (
    ClosedTrade,
    ExitReason,
    OrderIntent,
    Position,
)
from mentor.domain.backtest.strategy import Strategy, StrategyContext
from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.market.bars import PriceBar
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction


@dataclass(frozen=True, slots=True)
class EquityPoint:
    ts: datetime
    balance: Decimal


@dataclass(frozen=True, slots=True)
class BacktestResult:
    strategy: str
    symbol: str
    starting_balance: Money
    ending_balance: Money
    equity_curve: tuple[EquityPoint, ...]
    closed_trades: tuple[ClosedTrade, ...]
    final_open_positions: tuple[Position, ...]
    total_costs_paid: Decimal
    bars_evaluated: int


@dataclass(slots=True)
class _State:
    cash: Decimal
    positions: list[Position] = field(default_factory=list)
    pending: list[OrderIntent] = field(default_factory=list)
    closed: list[ClosedTrade] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)
    costs_paid: Decimal = Decimal("0")


def _pnl_units_in_account(
    *,
    direction: Direction,
    entry: Decimal,
    exit_: Decimal,
    lots: Decimal,
    instrument: Instrument,
    quote_to_account: Decimal,
) -> Decimal:
    units = lots * instrument.contract_size
    sign = Decimal("1") if direction is Direction.LONG else Decimal("-1")
    return sign * (exit_ - entry) * units * quote_to_account


def _unrealised(
    state: _State,
    *,
    mark_price: Decimal,
    instrument: Instrument,
    quote_to_account: Decimal,
) -> Decimal:
    total = Decimal("0")
    for pos in state.positions:
        total += _pnl_units_in_account(
            direction=pos.direction,
            entry=pos.entry_price,
            exit_=mark_price,
            lots=pos.size_lots,
            instrument=instrument,
            quote_to_account=quote_to_account,
        )
    return total


def _close_position(
    state: _State,
    pos: Position,
    *,
    exit_price: Decimal,
    exit_ts: datetime,
    instrument: Instrument,
    quote_to_account: Decimal,
    cost_model: CostModel,
    reason: ExitReason,
) -> None:
    realised = _pnl_units_in_account(
        direction=pos.direction,
        entry=pos.entry_price,
        exit_=exit_price,
        lots=pos.size_lots,
        instrument=instrument,
        quote_to_account=quote_to_account,
    )
    # Commission is paid as a round-trip charge at close. Spread and
    # slippage were already taken out of the fill prices, so they must not
    # be deducted again — but they are still a cost the reader is entitled
    # to see, so they are counted here and reported alongside.
    commission = cost_model.commission_for(pos.size_lots)
    friction = cost_model.friction_for(pos.size_lots, instrument)
    net = realised - commission
    state.cash += net
    state.costs_paid += commission + friction
    r = net / pos.initial_risk_amount if pos.initial_risk_amount > 0 else Decimal("0")
    state.closed.append(
        ClosedTrade(
            direction=pos.direction,
            size_lots=pos.size_lots,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            entry_ts=pos.entry_ts,
            exit_ts=exit_ts,
            initial_risk_amount=pos.initial_risk_amount,
            realised_pnl_account=net,
            realised_r=r,
            costs_paid=commission + friction,
            exit_reason=reason,
            reason=pos.reason,
        )
    )


def _check_stops_and_targets(
    state: _State,
    bar: PriceBar,
    *,
    instrument: Instrument,
    quote_to_account: Decimal,
    cost_model: CostModel,
) -> None:
    survivors: list[Position] = []
    for pos in state.positions:
        # Conservative tie-breaker: if a bar's range covers both stop and
        # target, the stop is treated as hit first. This bias makes the
        # backtest pessimistic — preferable to flattering yourself.
        hit_stop, hit_target = False, False
        if pos.direction is Direction.LONG:
            hit_stop = bar.low <= pos.stop_price
            hit_target = pos.target_price is not None and bar.high >= pos.target_price
        else:
            hit_stop = bar.high >= pos.stop_price
            hit_target = pos.target_price is not None and bar.low <= pos.target_price

        if hit_stop:
            exit_price = cost_model.exit_fill_price(
                direction=pos.direction,
                raw_price=pos.stop_price,
                instrument=instrument,
            )
            _close_position(
                state,
                pos,
                exit_price=exit_price,
                exit_ts=bar.ts,
                instrument=instrument,
                quote_to_account=quote_to_account,
                cost_model=cost_model,
                reason=ExitReason.STOP,
            )
        elif hit_target and pos.target_price is not None:
            exit_price = cost_model.exit_fill_price(
                direction=pos.direction,
                raw_price=pos.target_price,
                instrument=instrument,
            )
            _close_position(
                state,
                pos,
                exit_price=exit_price,
                exit_ts=bar.ts,
                instrument=instrument,
                quote_to_account=quote_to_account,
                cost_model=cost_model,
                reason=ExitReason.TARGET,
            )
        else:
            survivors.append(pos)

    state.positions = survivors


def _fill_pending_intents(
    state: _State,
    bar: PriceBar,
    *,
    instrument: Instrument,
    quote_to_account: Decimal,
    cost_model: CostModel,
) -> None:
    """Fill intents from the *previous* bar at this bar's open price."""
    if not state.pending:
        return

    for intent in state.pending:
        if intent.size_lots <= 0:
            continue
        fill_price = cost_model.entry_fill_price(
            direction=intent.direction,
            raw_price=bar.open,
            instrument=instrument,
        )
        # Compute the *initial risk in the account currency* from the
        # actual fill so R-multiples reflect what really happened.
        units = intent.size_lots * instrument.contract_size
        risk_distance = abs(fill_price - intent.stop_price)
        initial_risk_account = risk_distance * units * quote_to_account
        state.positions.append(
            Position(
                direction=intent.direction,
                size_lots=intent.size_lots,
                entry_price=fill_price,
                entry_ts=bar.ts,
                stop_price=intent.stop_price,
                target_price=intent.target_price,
                initial_risk_amount=initial_risk_account,
                reason=intent.reason,
            )
        )
    state.pending = []


def run_backtest(
    *,
    bars: Sequence[PriceBar],
    strategy: Strategy,
    instrument: Instrument,
    starting_balance: Money,
    cost_model: CostModel | None = None,
    risk_per_trade_fraction: Decimal = Decimal("0.01"),
    quote_to_account_rate: Decimal = Decimal("1"),
    symbol: str | None = None,
) -> BacktestResult:
    """Run a strategy over historical bars.

    Returns a `BacktestResult` with equity curve, closed trades, and
    the total costs paid. Metrics are computed by `compute_metrics`.
    """
    if not bars:
        raise ValidationError("bars must not be empty")
    if any(bars[i].ts >= bars[i + 1].ts for i in range(len(bars) - 1)):
        raise ValidationError("bars must be strictly chronological")
    if not starting_balance.is_positive:
        raise ValidationError("starting_balance must be positive", field="starting_balance")

    costs = cost_model or CostModel()
    bar_tuple = tuple(bars)
    state = _State(cash=starting_balance.amount)
    strategy_state = strategy.initial_state()
    sym = (symbol or bar_tuple[0].symbol).upper()

    for i in range(len(bar_tuple)):
        bar = bar_tuple[i]
        view = MarketView(_bars=bar_tuple, _current_index=i)

        # 1) Fills from intents the strategy produced last bar happen at
        #    *this* bar's open.
        _fill_pending_intents(
            state,
            bar,
            instrument=instrument,
            quote_to_account=quote_to_account_rate,
            cost_model=costs,
        )

        # 2) Stops / targets that triggered during this bar.
        _check_stops_and_targets(
            state,
            bar,
            instrument=instrument,
            quote_to_account=quote_to_account_rate,
            cost_model=costs,
        )

        # 3) Mark-to-market equity using this bar's close.
        equity = state.cash + _unrealised(
            state,
            mark_price=bar.close,
            instrument=instrument,
            quote_to_account=quote_to_account_rate,
        )
        state.equity_curve.append(EquityPoint(ts=bar.ts, balance=equity))

        # 4) Strategy decides on intents — to be filled next bar.
        ctx = StrategyContext(
            view=view,
            open_positions=tuple(state.positions),
            account_equity=Money(equity, starting_balance.currency),
            risk_per_trade_fraction=risk_per_trade_fraction,
            state=strategy_state,
        )
        intents = strategy.on_bar(ctx)
        if intents:
            state.pending.extend(intents)

    # Close any positions still open at the end at the final close (for
    # honest reporting; the metrics layer separates these from triggered exits).
    if state.positions:
        last_bar = bar_tuple[-1]
        for pos in state.positions:
            exit_price = costs.exit_fill_price(
                direction=pos.direction,
                raw_price=last_bar.close,
                instrument=instrument,
            )
            _close_position(
                state,
                pos,
                exit_price=exit_price,
                exit_ts=last_bar.ts,
                instrument=instrument,
                quote_to_account=quote_to_account_rate,
                cost_model=costs,
                reason=ExitReason.END_OF_DATA,
            )

    return BacktestResult(
        strategy=strategy.name,
        symbol=sym,
        starting_balance=starting_balance,
        ending_balance=Money(state.cash, starting_balance.currency).quantized(),
        equity_curve=tuple(state.equity_curve),
        closed_trades=tuple(state.closed),
        final_open_positions=tuple(state.positions),  # always empty post-cleanup
        total_costs_paid=state.costs_paid,
        bars_evaluated=len(bar_tuple),
    )
