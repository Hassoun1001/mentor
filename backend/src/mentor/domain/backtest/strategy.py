"""Strategy interface.

A strategy is a *pure function* of the visible market plus its open
positions: given what you can see now, what would you do?

The strategy is **forbidden** from:
- Mutating any input.
- Calling external services or reading from disk.
- Storing state in module globals (use the `state` dict instead).

Following these rules makes the strategy deterministic and replayable —
two runs over the same data must produce identical results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from mentor.domain.backtest.market_view import MarketView
from mentor.domain.backtest.orders import OrderIntent, Position
from mentor.domain.money import Money


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """Read-only environment passed to the strategy on every bar.

    The strategy gets the current view, the open positions, and a
    snapshot of account equity. The `state` dict is the *only* mutable
    surface — strategies stash any rolling indicators or flags there.
    """

    view: MarketView
    open_positions: Sequence[Position]
    account_equity: Money
    risk_per_trade_fraction: Decimal
    state: dict[str, Any]


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:
        """Return zero or more intents to act on at the *next* bar's open.

        A strategy may also return intents that close positions early by
        not opening new ones — the engine never re-evaluates an open
        position once it has stop/target set. Add an explicit "exit"
        intent in a future revision if needed.
        """
        ...

    def initial_state(self) -> dict[str, Any]:
        """Optional override — return the strategy's starting state dict."""
        return {}
