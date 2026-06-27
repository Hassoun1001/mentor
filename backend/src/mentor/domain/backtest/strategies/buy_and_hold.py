"""Buy-and-hold — the "is the market just up over this window?" baseline.

Opens one long on the first bar with a wide stop far enough away that
intraday noise can't take it out, and holds until the end of data.
Useful as the "is the backtest engine producing sane PnL?" sanity check.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.backtest.orders import OrderIntent
from mentor.domain.backtest.strategy import Strategy, StrategyContext
from mentor.domain.instruments import Instrument
from mentor.domain.money import round_down_to_step
from mentor.domain.risk.position_sizing import Direction


@dataclass(frozen=True, slots=True)
class BuyAndHold(Strategy):
    instrument: Instrument
    risk_pct_for_initial_size: Decimal = Decimal("0.5")  # 50% so size is meaningful
    quote_to_account_rate: Decimal = Decimal("1")

    @property
    def name(self) -> str:
        return "buy_and_hold"

    def on_bar(self, ctx: StrategyContext) -> list[OrderIntent]:
        if ctx.open_positions or ctx.state.get("entered"):
            return []
        # Wide stop: 30% below current close.
        last = ctx.view.current_close
        stop = last * Decimal("0.7")
        risk_distance = last - stop
        pip_value_per_lot_account = (
            self.instrument.contract_size * self.instrument.pip_size * self.quote_to_account_rate
        )
        pip_distance = risk_distance / self.instrument.pip_size
        risk_amount = ctx.account_equity.amount * self.risk_pct_for_initial_size
        denom = pip_distance * pip_value_per_lot_account
        if denom <= 0:
            return []
        raw_lots = risk_amount / denom
        lots = round_down_to_step(raw_lots, self.instrument.lot_step, self.instrument.min_lot)
        ctx.state["entered"] = True
        if lots <= 0:
            return []
        return [
            OrderIntent(
                direction=Direction.LONG,
                size_lots=lots,
                stop_price=stop,
                target_price=None,
                reason="buy and hold",
            )
        ]
