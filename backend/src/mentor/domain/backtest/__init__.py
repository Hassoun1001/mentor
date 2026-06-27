"""Backtest engine — Phase 3.

> The backtester is the judge of everything. No signal reaches the
> dashboard until it has passed this process.   — Mentor product plan, §13

Three failure modes the engine is designed to eliminate:

- **Lookahead bias** — at every simulated step only past data is visible.
  `MarketView` exposes no method that reaches a future bar.
- **Overfitting** — `WalkForwardRunner` slides train/test windows through
  history; the test slice is never seen during the design or tuning.
- **Ignoring costs** — `CostModel` applies spread, commission, and
  slippage on every fill. No "frictionless" mode exists.
"""

from mentor.domain.backtest.costs import CostModel
from mentor.domain.backtest.engine import BacktestResult, run_backtest
from mentor.domain.backtest.market_view import MarketView
from mentor.domain.backtest.metrics import BacktestMetrics, compute_metrics
from mentor.domain.backtest.orders import (
    ClosedTrade,
    OrderIntent,
    Position,
    PositionStatus,
)
from mentor.domain.backtest.strategy import Strategy, StrategyContext
from mentor.domain.backtest.walk_forward import WalkForwardResult, walk_forward

__all__ = [
    "BacktestMetrics",
    "BacktestResult",
    "ClosedTrade",
    "CostModel",
    "MarketView",
    "OrderIntent",
    "Position",
    "PositionStatus",
    "Strategy",
    "StrategyContext",
    "WalkForwardResult",
    "compute_metrics",
    "run_backtest",
    "walk_forward",
]
