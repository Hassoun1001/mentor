"""RSI mean-reversion — a second honest baseline to compare against.

A different *kind* of edge from the trend-following MA crossover, so the
comparison actually teaches something:

- Compute RSI(period) on closes.
- RSI below ``oversold`` -> the market is stretched down; plan a **long**
  for the next bar (bet on a bounce).
- RSI above ``overbought`` -> stretched up; plan a **short**.
- Stop = N × ATR from entry, target = stop × R:R. One position at a time.

Mean reversion is a real effect at short horizons and extremes, but it
gets run over in strong trends — exactly the trade-off the backtester and
the comparison view make visible. Sizing math is identical to the live
risk engine (and to ``MaCrossover``).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from mentor.domain.backtest.orders import OrderIntent
from mentor.domain.backtest.strategy import Strategy, StrategyContext
from mentor.domain.indicators import atr, rsi
from mentor.domain.instruments import Instrument
from mentor.domain.money import round_down_to_step
from mentor.domain.risk.position_sizing import Direction


@dataclass(frozen=True, slots=True)
class RsiReversion(Strategy):
    instrument: Instrument
    rsi_period: int = 14
    oversold: Decimal = Decimal("30")
    overbought: Decimal = Decimal("70")
    atr_period: int = 14
    atr_stop_multiple: Decimal = Decimal("2")
    target_rr: Decimal = Decimal("2")
    quote_to_account_rate: Decimal = Decimal("1")

    @property
    def name(self) -> str:
        return (
            f"rsi_reversion({self.rsi_period}, {self.oversold:.0f}/{self.overbought:.0f}, "
            f"atr={self.atr_period}×{self.atr_stop_multiple})"
        )

    def initial_state(self) -> dict[str, Any]:
        return {}

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:  # noqa: PLR0911 — guard clauses read clearer flat
        needed = max(self.rsi_period + 2, self.atr_period + 2)
        if ctx.view.visible_count < needed:
            return []
        if ctx.open_positions:
            return []

        window = max(self.rsi_period, self.atr_period) * 2
        closes = ctx.view.closes(window)
        bars = ctx.view.history(window)
        rsi_v = rsi(closes, self.rsi_period)
        current_atr = atr(bars, self.atr_period)
        if rsi_v is None or current_atr is None or current_atr <= 0:
            return []

        if rsi_v <= self.oversold:
            direction = Direction.LONG
        elif rsi_v >= self.overbought:
            direction = Direction.SHORT
        else:
            return []

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

        verb = "oversold bounce" if direction is Direction.LONG else "overbought fade"
        return [
            OrderIntent(
                direction=direction,
                size_lots=lots,
                stop_price=stop,
                target_price=target,
                reason=f"RSI {rsi_v:.0f} — {verb}",
            )
        ]
