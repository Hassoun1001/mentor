"""Strategy registry — the catalogue the API exposes.

Adding a new strategy is one entry here and a class file. Strategies in
the registry are buildable from a small JSON params dict so the
frontend can drive them without writing Python.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any, Final

from mentor.domain.backtest.strategies.buy_and_hold import BuyAndHold
from mentor.domain.backtest.strategies.ma_crossover import MaCrossover
from mentor.domain.backtest.strategy import Strategy
from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument


def _build_ma(instrument: Instrument, params: dict[str, Any]) -> Strategy:
    return MaCrossover(
        instrument=instrument,
        fast_period=int(params.get("fast_period", 20)),
        slow_period=int(params.get("slow_period", 50)),
        atr_period=int(params.get("atr_period", 14)),
        atr_stop_multiple=Decimal(str(params.get("atr_stop_multiple", "2"))),
        target_rr=Decimal(str(params.get("target_rr", "2"))),
        quote_to_account_rate=Decimal(str(params.get("quote_to_account_rate", "1"))),
    )


def _build_bh(instrument: Instrument, params: dict[str, Any]) -> Strategy:
    return BuyAndHold(
        instrument=instrument,
        quote_to_account_rate=Decimal(str(params.get("quote_to_account_rate", "1"))),
    )


STRATEGY_REGISTRY: Final[dict[str, Callable[[Instrument, dict[str, Any]], Strategy]]] = {
    "ma_crossover": _build_ma,
    "buy_and_hold": _build_bh,
}


def build_strategy(name: str, instrument: Instrument, params: dict[str, Any]) -> Strategy:
    try:
        factory = STRATEGY_REGISTRY[name]
    except KeyError as exc:
        raise ValidationError(f"unknown strategy: {name!r}", field="strategy") from exc
    return factory(instrument, params)
