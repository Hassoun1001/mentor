"""MA crossover — the honest baseline.

> A simple, transparent benchmark every fancier model must beat — the
> honest yardstick.   — Mentor product plan, §6.D

Rules:
- Compute fast-EMA and slow-EMA on closes.
- When fast crosses **above** slow, plan a long for the next bar.
- When fast crosses **below** slow, plan a short for the next bar.
- Stop = N × ATR from entry. Target = 2 × stop distance (≥ 1:2 R:R).
- Risk = `risk_per_trade_fraction × equity`, sized by the same formula
  the live risk engine uses.

The strategy never opens a new position while one is already open. It
is deliberately ascetic. If your "fancier" idea can't beat this after
costs, the fancier idea is overfit.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from mentor.domain.backtest.orders import OrderIntent
from mentor.domain.backtest.strategy import Strategy, StrategyContext
from mentor.domain.indicators import atr, ema
from mentor.domain.instruments import Instrument
from mentor.domain.money import round_down_to_step
from mentor.domain.risk.position_sizing import Direction


@dataclass(frozen=True, slots=True)
class MaCrossover(Strategy):
    instrument: Instrument
    fast_period: int = 20
    slow_period: int = 50
    atr_period: int = 14
    atr_stop_multiple: Decimal = Decimal("2")
    target_rr: Decimal = Decimal("2")
    quote_to_account_rate: Decimal = Decimal("1")

    @property
    def name(self) -> str:
        return (
            f"ma_crossover({self.fast_period}/{self.slow_period}, "
            f"atr={self.atr_period}×{self.atr_stop_multiple})"
        )

    def initial_state(self) -> dict[str, Any]:
        return {"prev_relation": None}  # "fast_above" | "fast_below" | None

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:  # noqa: PLR0911 — sequential guard clauses read clearer than nesting
        # Need enough history for the slow EMA + ATR
        needed = max(self.slow_period + 1, self.atr_period + 2)
        if ctx.view.visible_count < needed:
            return []

        # Hold one position at a time. Simpler, easier to reason about,
        # and matches how the discipline guardrails will throttle a live trader.
        if ctx.open_positions:
            return []

        closes = ctx.view.closes(max(self.slow_period, self.atr_period) * 2)
        bars = ctx.view.history(max(self.slow_period, self.atr_period) * 2)
        fast = ema(closes, self.fast_period)
        slow = ema(closes, self.slow_period)
        current_atr = atr(bars, self.atr_period)
        if fast is None or slow is None or current_atr is None or current_atr <= 0:
            return []

        relation = "fast_above" if fast > slow else ("fast_below" if fast < slow else None)
        prev = ctx.state.get("prev_relation")
        ctx.state["prev_relation"] = relation

        if prev is None or relation is None or relation == prev:
            return []

        # Crossover detected
        direction = Direction.LONG if relation == "fast_above" else Direction.SHORT
        last_close = ctx.view.current_close
        stop_distance = current_atr * self.atr_stop_multiple
        if direction is Direction.LONG:
            stop = last_close - stop_distance
            target = last_close + stop_distance * self.target_rr
        else:
            stop = last_close + stop_distance
            target = last_close - stop_distance * self.target_rr
        if stop <= 0:
            return []

        # Position-sizing math identical to the risk engine.
        risk_amount = ctx.account_equity.amount * ctx.risk_per_trade_fraction
        pip_value_per_lot_account = (
            self.instrument.contract_size * self.instrument.pip_size * self.quote_to_account_rate
        )
        pip_distance = stop_distance / self.instrument.pip_size
        denom = pip_distance * pip_value_per_lot_account
        if denom <= 0:
            return []
        raw_lots = risk_amount / denom
        lots = round_down_to_step(raw_lots, self.instrument.lot_step, self.instrument.min_lot)
        if lots <= 0:
            return []

        return [
            OrderIntent(
                direction=direction,
                size_lots=lots,
                stop_price=stop,
                target_price=target,
                reason=f"{self.fast_period}/{self.slow_period} EMA cross "
                f"({'up' if direction is Direction.LONG else 'down'})",
            )
        ]
