"""Risk-of-ruin Monte Carlo simulator.

> Monte-Carlo simulation of trade sequences to show drawdown and
> probability-of-ruin under the chosen rules.   — Mentor plan, §6.E

Given an empirical R-distribution (the user's own closed trades, or a
hypothetical mix), draw `n_trades` outcomes with replacement, scaling
each by `risk_per_trade` of equity, and aggregate across `n_runs` paths.

The output is honest about three things:

- **Probability of ruin** — fraction of paths that drew the account
  below `ruin_threshold` (default 50% of starting equity).
- **Drawdown distribution** — the p50/p95 worst peak-to-trough seen.
- **Terminal balance percentiles** — the realistic range of outcomes,
  not just the mean. A backtest's median path is what a *typical*
  trader experiences; the p5 path is what 1-in-20 traders experience.

All math in Decimal (path simulation is in float for speed; final
aggregates are in Decimal so the API never returns lossy strings).
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.errors import ValidationError


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    n_runs: int
    n_trades: int
    risk_per_trade_pct: Decimal
    starting_balance: Decimal
    ruin_threshold: Decimal
    probability_of_ruin: Decimal
    median_terminal: Decimal
    p5_terminal: Decimal
    p95_terminal: Decimal
    median_max_drawdown_pct: Decimal
    p95_max_drawdown_pct: Decimal
    expected_terminal: Decimal


def _path_max_drawdown(equity: list[float]) -> float:
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            dd = (peak - v) / peak
            max_dd = max(max_dd, dd)
    return max_dd


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    idx = max(0, min(len(sorted_values) - 1, int(q * (len(sorted_values) - 1))))
    return sorted_values[idx]


def simulate_risk_of_ruin(
    *,
    r_distribution: Sequence[Decimal],
    starting_balance: Decimal,
    risk_per_trade_fraction: Decimal,
    n_trades: int,
    n_runs: int = 5_000,
    ruin_fraction: Decimal = Decimal("0.5"),
    seed: int | None = 42,
) -> MonteCarloResult:
    """Run `n_runs` independent trade sequences and aggregate the outcomes.

    `r_distribution` is the empirical pool — typically the user's
    realised R-multiples. The function samples with replacement.
    """
    if not r_distribution:
        raise ValidationError("r_distribution must be non-empty — log some trades first")
    if risk_per_trade_fraction <= 0 or risk_per_trade_fraction > Decimal("0.20"):
        raise ValidationError(
            "risk_per_trade_fraction must be in (0, 0.20]",
            field="risk_per_trade_fraction",
        )
    if n_trades < 10:
        raise ValidationError("n_trades must be >= 10", field="n_trades")
    if n_runs < 100 or n_runs > 50_000:
        raise ValidationError("n_runs must be in [100, 50000]", field="n_runs")
    if not (Decimal("0.1") <= ruin_fraction <= Decimal("0.9")):
        raise ValidationError("ruin_fraction must be in [0.1, 0.9]", field="ruin_fraction")

    rng = random.Random(seed)  # noqa: S311 — Monte-Carlo simulation, not security-sensitive
    pool = [float(r) for r in r_distribution]
    start = float(starting_balance)
    risk_pct = float(risk_per_trade_fraction)
    ruin_threshold = start * float(ruin_fraction)

    terminal_balances: list[float] = []
    max_drawdowns: list[float] = []
    ruined = 0

    for _ in range(n_runs):
        balance = start
        equity_path = [balance]
        path_ruined = False
        for _ in range(n_trades):
            r = pool[rng.randrange(len(pool))]
            pnl = balance * risk_pct * r
            balance = max(0.0, balance + pnl)
            equity_path.append(balance)
            if balance <= ruin_threshold:
                path_ruined = True
                # No early exit — keep simulating so terminal distribution
                # isn't truncated. Real traders sometimes recover; some
                # don't. The p_ruin metric still counts this run.
        terminal_balances.append(balance)
        max_drawdowns.append(_path_max_drawdown(equity_path))
        if path_ruined:
            ruined += 1

    terminal_balances.sort()
    max_drawdowns.sort()

    p_ruin = Decimal(ruined) / Decimal(n_runs)
    p_ruin = p_ruin.quantize(Decimal("0.0001"))

    return MonteCarloResult(
        n_runs=n_runs,
        n_trades=n_trades,
        risk_per_trade_pct=risk_per_trade_fraction * Decimal("100"),
        starting_balance=starting_balance,
        ruin_threshold=Decimal(str(ruin_threshold)).quantize(Decimal("0.01")),
        probability_of_ruin=p_ruin,
        median_terminal=Decimal(str(_percentile(terminal_balances, 0.5))).quantize(Decimal("0.01")),
        p5_terminal=Decimal(str(_percentile(terminal_balances, 0.05))).quantize(Decimal("0.01")),
        p95_terminal=Decimal(str(_percentile(terminal_balances, 0.95))).quantize(Decimal("0.01")),
        median_max_drawdown_pct=Decimal(str(_percentile(max_drawdowns, 0.5) * 100)).quantize(
            Decimal("0.01")
        ),
        p95_max_drawdown_pct=Decimal(str(_percentile(max_drawdowns, 0.95) * 100)).quantize(
            Decimal("0.01")
        ),
        expected_terminal=Decimal(str(sum(terminal_balances) / len(terminal_balances))).quantize(
            Decimal("0.01")
        ),
    )
