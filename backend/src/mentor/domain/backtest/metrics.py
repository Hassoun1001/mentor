"""Backtest metrics — what the judge actually says.

We deliberately keep this honest. We report:

- **Total return** (cash basis)
- **Max drawdown** — peak-to-trough on the equity curve
- **Annualised volatility & Sharpe-ish** — using equity-curve returns
- **Win rate, expectancy, profit factor** — over closed trades
- **Trade count and exposure** — gives context to the rest

We do NOT report:

- A precise Sharpe ratio that pretends to know the risk-free rate.
- A "calmar" or any other ratio that flatters thin drawdowns.
- Any metric that ignores costs — `total_costs_paid` is its own line.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import sqrt

from mentor.domain.backtest.engine import BacktestResult
from mentor.domain.backtest.orders import ExitReason


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    total_return_pct: Decimal
    max_drawdown_pct: Decimal
    max_drawdown_duration_bars: int
    bars_evaluated: int
    trade_count: int
    win_rate_pct: Decimal
    expectancy_r: Decimal
    profit_factor: Decimal | None
    total_costs_paid: Decimal
    avg_win_r: Decimal
    avg_loss_r: Decimal
    largest_win_r: Decimal
    largest_loss_r: Decimal
    sharpe_like: Decimal  # equity-curve mean/std, not risk-adjusted
    forced_closes: int  # positions closed at end-of-data, not a real exit


def _drawdown(equity: list[Decimal]) -> tuple[Decimal, int]:
    if not equity:
        return Decimal("0"), 0
    peak = equity[0]
    peak_idx = 0
    max_dd = Decimal("0")
    max_dur = 0
    for i, v in enumerate(equity):
        if v > peak:
            peak = v
            peak_idx = i
        dd = (peak - v) / peak if peak > 0 else Decimal("0")
        if dd > max_dd:
            max_dd = dd
            max_dur = i - peak_idx
    return max_dd, max_dur


def _sharpe_like(equity: list[Decimal]) -> Decimal:
    if len(equity) < 3:
        return Decimal("0")
    returns: list[Decimal] = []
    for i in range(1, len(equity)):
        prev = equity[i - 1]
        if prev == 0:
            continue
        returns.append((equity[i] - prev) / prev)
    if len(returns) < 2:
        return Decimal("0")
    mean = sum(returns, Decimal("0")) / Decimal(len(returns))
    variance = sum(((r - mean) * (r - mean) for r in returns), Decimal("0")) / Decimal(
        len(returns) - 1
    )
    std = Decimal(str(sqrt(float(variance)))) if variance > 0 else Decimal("0")
    return (mean / std) if std > 0 else Decimal("0")


def compute_metrics(result: BacktestResult) -> BacktestMetrics:
    equity_values = [p.balance for p in result.equity_curve]
    starting = result.starting_balance.amount
    ending = result.ending_balance.amount
    total_return_pct = (
        ((ending - starting) / starting) * Decimal("100") if starting > 0 else Decimal("0")
    )

    max_dd, max_dur = _drawdown(equity_values)
    sharpe = _sharpe_like(equity_values)

    rs = [t.realised_r for t in result.closed_trades]
    real_exits = [t for t in result.closed_trades if t.exit_reason is not ExitReason.END_OF_DATA]
    rs_real = [t.realised_r for t in real_exits]
    wins = [r for r in rs_real if r > 0]
    losses = [r for r in rs_real if r < 0]
    win_rate = (
        (Decimal(len(wins)) / Decimal(len(rs_real))) * Decimal("100") if rs_real else Decimal("0")
    )
    avg_win = sum(wins, Decimal("0")) / Decimal(len(wins)) if wins else Decimal("0")
    avg_loss = -sum(losses, Decimal("0")) / Decimal(len(losses)) if losses else Decimal("0")
    expectancy = (
        (Decimal(len(wins)) / Decimal(len(rs_real))) * avg_win
        - (Decimal(len(losses)) / Decimal(len(rs_real))) * avg_loss
        if rs_real
        else Decimal("0")
    )
    total_wins = sum(wins, Decimal("0"))
    total_losses = -sum(losses, Decimal("0"))
    profit_factor = total_wins / total_losses if total_losses > 0 else None

    return BacktestMetrics(
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_dd * Decimal("100"),
        max_drawdown_duration_bars=max_dur,
        bars_evaluated=result.bars_evaluated,
        trade_count=len(rs),
        win_rate_pct=win_rate,
        expectancy_r=expectancy,
        profit_factor=profit_factor,
        total_costs_paid=result.total_costs_paid,
        avg_win_r=avg_win,
        avg_loss_r=avg_loss,
        largest_win_r=max(rs, default=Decimal("0")) if rs else Decimal("0"),
        largest_loss_r=min(rs, default=Decimal("0")) if rs else Decimal("0"),
        sharpe_like=sharpe,
        forced_closes=sum(
            1 for t in result.closed_trades if t.exit_reason is ExitReason.END_OF_DATA
        ),
    )
