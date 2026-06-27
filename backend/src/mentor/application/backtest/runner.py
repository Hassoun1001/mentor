"""BacktestRunner — load bars, drive the engine, return the verdict.

The runner is the only place in the codebase that knows how to
materialise domain `PriceBar` objects from the database. The engine
itself stays pure.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from mentor.domain.backtest import (
    BacktestMetrics,
    BacktestResult,
    CostModel,
    Strategy,
    WalkForwardResult,
    compute_metrics,
    run_backtest,
    walk_forward,
)
from mentor.domain.backtest.strategies import build_strategy
from mentor.domain.errors import ValidationError
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.money import Money
from mentor.infrastructure.models import PriceBar as PriceBarORM
from mentor.infrastructure.repositories.price_bars import PriceBarRepository


def _to_domain_bars(rows: Sequence[PriceBarORM]) -> list[PriceBar]:
    return [
        PriceBar(
            symbol=r.symbol,
            timeframe=Timeframe(r.timeframe),
            ts=r.ts,
            open=Decimal(r.open),
            high=Decimal(r.high),
            low=Decimal(r.low),
            close=Decimal(r.close),
            volume=Decimal(r.volume) if r.volume is not None else None,
            source=r.source,
        )
        for r in rows
    ]


@dataclass(frozen=True, slots=True)
class BacktestPayload:
    result: BacktestResult
    metrics: BacktestMetrics
    walk_forward: WalkForwardResult | None


class BacktestRunner:
    def __init__(self, repo: PriceBarRepository) -> None:
        self._repo = repo

    async def run(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        strategy_name: str,
        strategy_params: dict[str, Any],
        starting_balance: Money,
        cost_model: CostModel,
        risk_per_trade_fraction: Decimal,
        do_walk_forward: bool = False,
        walk_forward_windows: int = 4,
    ) -> BacktestPayload:
        rows = await self._repo.range(symbol=symbol, timeframe=timeframe, start=start, end=end)
        if not rows:
            raise ValidationError(
                f"no bars in DB for {symbol} {timeframe.value} in window — "
                "run the ingestion CLI first"
            )
        bars = _to_domain_bars(rows)
        instrument = get_instrument(symbol)

        def factory() -> Strategy:
            return build_strategy(strategy_name, instrument, strategy_params)

        result = run_backtest(
            bars=bars,
            strategy=factory(),
            instrument=instrument,
            starting_balance=starting_balance,
            cost_model=cost_model,
            risk_per_trade_fraction=risk_per_trade_fraction,
            symbol=symbol,
        )
        metrics = compute_metrics(result)

        wf: WalkForwardResult | None = None
        if do_walk_forward:
            wf = walk_forward(
                bars=bars,
                instrument=instrument,
                strategy_factory=factory,
                starting_balance=starting_balance,
                n_windows=walk_forward_windows,
            )

        return BacktestPayload(result=result, metrics=metrics, walk_forward=wf)
