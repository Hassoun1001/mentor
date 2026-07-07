""""What if I'd followed him?" — a risk-based backtest of a tipster's calls.

No prediction here: every price already happened. We simulate mechanically
buying each actionable call at its mention price, sized by the same
risk-budget discipline the FX risk engine enforces — risk a fixed fraction
of *current* equity per position, with the stop as the risk ceiling — and
report the equity curve, drawdown, expectancy (R) and win rate.

Stocks trade in whole shares with dollar moves, so we size shares directly
(``shares = risk_budget / stop_distance``, rounded *down* so the loss at the
stop never exceeds the budget) rather than forcing FX pip/lot mechanics onto
equities. The principle is identical to ``calculate_position``; only the
instrument mechanics differ.

This is a track-record simulation, not advice.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TipEntry:
    """One actionable call, already priced against real history."""

    ticker: str
    mentioned_at: datetime
    entry_price: Decimal
    exit_price: Decimal  # latest close (mark-to-market)
    min_since: Decimal  # lowest close since mention (for stop-out detection)
    days_held: int


@dataclass(frozen=True, slots=True)
class FollowTrade:
    ticker: str
    mentioned_at: datetime
    entry_price: Decimal
    exit_fill: Decimal
    stop_price: Decimal
    shares: Decimal
    risk_amount: Decimal
    pnl: Decimal
    r_multiple: Decimal
    return_pct: Decimal
    days_held: int
    stopped_out: bool
    won: bool


@dataclass(frozen=True, slots=True)
class EquityPoint:
    label: str  # ticker mentioned at this step
    at: datetime
    equity: Decimal


@dataclass(frozen=True, slots=True)
class FollowBacktestResult:
    tipster: str
    starting_equity: Decimal
    ending_equity: Decimal
    risk_pct: Decimal
    stop_pct: Decimal
    apply_stop: bool
    n_trades: int
    total_return_pct: Decimal
    max_drawdown_pct: Decimal
    expectancy_r: Decimal
    win_rate: Decimal
    avg_days_held: Decimal
    equity_curve: tuple[EquityPoint, ...]
    trades: tuple[FollowTrade, ...]
    headline: str


def _q2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"))


def run_follow_backtest(
    *,
    tipster: str,
    entries: Sequence[TipEntry],
    starting_equity: Decimal = Decimal("10000"),
    risk_pct: Decimal = Decimal("0.01"),
    stop_pct: Decimal = Decimal("0.10"),
    apply_stop: bool = True,
) -> FollowBacktestResult:
    """Simulate following ``entries`` in mention order, compounding equity.

    ``risk_pct`` is the fraction of *current* equity risked per position;
    ``stop_pct`` places the stop that far below entry. With ``apply_stop``,
    a call whose price dipped to the stop is booked as a full -1R loss;
    otherwise every call is marked to its latest close.
    """
    if not (Decimal("0") < risk_pct <= Decimal("0.5")):
        raise ValueError("risk_pct must be in (0, 0.5]")
    if not (Decimal("0") < stop_pct < Decimal("1")):
        raise ValueError("stop_pct must be in (0, 1)")

    ordered = sorted(entries, key=lambda e: e.mentioned_at)
    equity = starting_equity
    peak = starting_equity
    max_dd = Decimal("0")
    trades: list[FollowTrade] = []
    curve: list[EquityPoint] = [EquityPoint(label="start", at=_earliest(ordered), equity=equity)]
    r_multiples: list[Decimal] = []
    days_total = 0
    wins = 0

    for e in ordered:
        if e.entry_price <= 0:
            continue
        risk_amount = equity * risk_pct
        stop_price = e.entry_price * (Decimal("1") - stop_pct)
        stop_distance = e.entry_price - stop_price
        shares = (risk_amount / stop_distance).to_integral_value(rounding="ROUND_DOWN")
        if shares <= 0:
            continue

        stopped = apply_stop and e.min_since <= stop_price
        exit_fill = stop_price if stopped else e.exit_price
        pnl = shares * (exit_fill - e.entry_price)
        r_multiple = pnl / risk_amount if risk_amount > 0 else Decimal("0")
        return_pct = ((exit_fill - e.entry_price) / e.entry_price * Decimal("100"))

        equity += pnl
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
        r_multiples.append(r_multiple)
        days_total += e.days_held
        won = pnl > 0
        if won:
            wins += 1

        trades.append(
            FollowTrade(
                ticker=e.ticker,
                mentioned_at=e.mentioned_at,
                entry_price=e.entry_price,
                exit_fill=_q2(exit_fill),
                stop_price=_q2(stop_price),
                shares=shares,
                risk_amount=_q2(risk_amount),
                pnl=_q2(pnl),
                r_multiple=r_multiple.quantize(Decimal("0.01")),
                return_pct=_q2(return_pct),
                days_held=e.days_held,
                stopped_out=stopped,
                won=won,
            )
        )
        curve.append(EquityPoint(label=e.ticker, at=e.mentioned_at, equity=_q2(equity)))

    n = len(trades)
    if n == 0:
        return _empty(tipster, starting_equity, risk_pct, stop_pct, apply_stop)

    total_return_pct = (equity - starting_equity) / starting_equity * Decimal("100")
    expectancy_r = sum(r_multiples, Decimal("0")) / Decimal(n)
    win_rate = Decimal(wins) / Decimal(n)
    avg_days = Decimal(days_total) / Decimal(n)
    headline = (
        f"Following {tipster} at {risk_pct * 100:.0f}% risk/trade (stop {stop_pct * 100:.0f}%): "
        f"{_q2(total_return_pct)}% total over {n} calls, max drawdown {_q2(max_dd * 100)}%, "
        f"expectancy {expectancy_r.quantize(Decimal('0.01'))}R, {int(win_rate * 100)}% winners. "
        "A mechanical simulation of past calls — not a promise about future ones, and not advice."
    )
    return FollowBacktestResult(
        tipster=tipster,
        starting_equity=starting_equity,
        ending_equity=_q2(equity),
        risk_pct=risk_pct,
        stop_pct=stop_pct,
        apply_stop=apply_stop,
        n_trades=n,
        total_return_pct=_q2(total_return_pct),
        max_drawdown_pct=_q2(max_dd * Decimal("100")),
        expectancy_r=expectancy_r.quantize(Decimal("0.01")),
        win_rate=win_rate.quantize(Decimal("0.01")),
        avg_days_held=avg_days.quantize(Decimal("0.1")),
        equity_curve=tuple(curve),
        trades=tuple(trades),
        headline=headline,
    )


def _earliest(entries: Sequence[TipEntry]) -> datetime:
    return min((e.mentioned_at for e in entries), default=datetime.min)


def _empty(
    tipster: str, equity: Decimal, risk_pct: Decimal, stop_pct: Decimal, apply_stop: bool
) -> FollowBacktestResult:
    return FollowBacktestResult(
        tipster=tipster,
        starting_equity=equity,
        ending_equity=equity,
        risk_pct=risk_pct,
        stop_pct=stop_pct,
        apply_stop=apply_stop,
        n_trades=0,
        total_return_pct=Decimal("0"),
        max_drawdown_pct=Decimal("0"),
        expectancy_r=Decimal("0"),
        win_rate=Decimal("0"),
        avg_days_held=Decimal("0"),
        equity_curve=(),
        trades=(),
        headline=f"No actionable priced calls to backtest for {tipster}.",
    )
