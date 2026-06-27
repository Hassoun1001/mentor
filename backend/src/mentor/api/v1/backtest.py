"""Backtest endpoints."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from mentor.api.deps import SessionDep
from mentor.application.backtest import BacktestRunner
from mentor.domain.backtest import CostModel
from mentor.domain.backtest.strategies import STRATEGY_REGISTRY
from mentor.domain.market.bars import Timeframe
from mentor.domain.money import Money
from mentor.infrastructure.repositories import PriceBarRepository

router = APIRouter(prefix="/backtest", tags=["backtest"])


# ---------- request ----------


class CostModelDTO(BaseModel):
    spread_pips: Decimal = Decimal("0.8")
    slippage_pips: Decimal = Decimal("0.2")
    commission_per_lot_round_trip: Decimal = Decimal("0")


class StartingBalanceDTO(BaseModel):
    amount: Decimal
    currency: str = Field(..., min_length=3, max_length=3)


class BacktestRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "EURUSD",
                "timeframe": "1h",
                "start": "2025-01-01T00:00:00Z",
                "end": "2026-06-01T00:00:00Z",
                "strategy": "ma_crossover",
                "strategy_params": {"fast_period": 20, "slow_period": 50},
                "starting_balance": {"amount": "10000", "currency": "USD"},
                "risk_per_trade_percent": "1",
                "do_walk_forward": True,
                "walk_forward_windows": 4,
            }
        }
    )

    symbol: str
    timeframe: Timeframe
    start: datetime
    end: datetime
    strategy: str
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    starting_balance: StartingBalanceDTO
    risk_per_trade_percent: Annotated[Decimal, Field(gt=0, le=10)] = Decimal("1")
    cost_model: CostModelDTO = Field(default_factory=CostModelDTO)
    do_walk_forward: bool = False
    walk_forward_windows: Annotated[int, Field(ge=2, le=10)] = 4


# ---------- response ----------


class EquityPointDTO(BaseModel):
    ts: datetime
    balance: Decimal


class ClosedTradeDTO(BaseModel):
    direction: str
    size_lots: Decimal
    entry_price: Decimal
    exit_price: Decimal
    entry_ts: datetime
    exit_ts: datetime
    realised_pnl: Decimal
    realised_r: Decimal
    costs_paid: Decimal
    exit_reason: str
    reason: str


class MetricsDTO(BaseModel):
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
    sharpe_like: Decimal
    forced_closes: int


class WalkForwardWindowDTO(BaseModel):
    index: int
    train_metrics: MetricsDTO
    test_metrics: MetricsDTO
    train_bars: int
    test_bars: int


class WalkForwardDTO(BaseModel):
    windows: list[WalkForwardWindowDTO]
    in_sample_avg_expectancy_r: Decimal
    out_of_sample_avg_expectancy_r: Decimal
    degradation_pct: Decimal | None
    is_overfit_signal: bool


class BacktestResponse(BaseModel):
    strategy: str
    symbol: str
    starting_balance: Decimal
    ending_balance: Decimal
    currency: str
    equity_curve: list[EquityPointDTO]
    closed_trades: list[ClosedTradeDTO]
    metrics: MetricsDTO
    walk_forward: WalkForwardDTO | None


class StrategyInfo(BaseModel):
    name: str


# ---------- endpoints ----------


@router.get("/strategies", response_model=list[StrategyInfo])
async def list_strategies() -> list[StrategyInfo]:
    return [StrategyInfo(name=name) for name in STRATEGY_REGISTRY]


@router.post("", response_model=BacktestResponse)
async def run_backtest_endpoint(body: BacktestRequest, session: SessionDep) -> BacktestResponse:
    runner = BacktestRunner(PriceBarRepository(session))
    payload = await runner.run(
        symbol=body.symbol,
        timeframe=body.timeframe,
        start=body.start,
        end=body.end,
        strategy_name=body.strategy,
        strategy_params=body.strategy_params,
        starting_balance=Money(body.starting_balance.amount, body.starting_balance.currency),
        cost_model=CostModel(
            spread_pips=body.cost_model.spread_pips,
            slippage_pips=body.cost_model.slippage_pips,
            commission_per_lot_round_trip=body.cost_model.commission_per_lot_round_trip,
        ),
        risk_per_trade_fraction=body.risk_per_trade_percent / Decimal("100"),
        do_walk_forward=body.do_walk_forward,
        walk_forward_windows=body.walk_forward_windows,
    )

    return BacktestResponse(
        strategy=payload.result.strategy,
        symbol=payload.result.symbol,
        starting_balance=payload.result.starting_balance.amount,
        ending_balance=payload.result.ending_balance.amount,
        currency=payload.result.starting_balance.currency,
        equity_curve=[
            EquityPointDTO(ts=p.ts, balance=p.balance) for p in payload.result.equity_curve
        ],
        closed_trades=[
            ClosedTradeDTO(
                direction=t.direction.value,
                size_lots=t.size_lots,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                entry_ts=t.entry_ts,
                exit_ts=t.exit_ts,
                realised_pnl=t.realised_pnl_account,
                realised_r=t.realised_r,
                costs_paid=t.costs_paid,
                exit_reason=t.exit_reason.value,
                reason=t.reason,
            )
            for t in payload.result.closed_trades
        ],
        metrics=_to_metrics_dto(payload.metrics),
        walk_forward=(
            WalkForwardDTO(
                windows=[
                    WalkForwardWindowDTO(
                        index=w.index,
                        train_metrics=_to_metrics_dto(w.train_metrics),
                        test_metrics=_to_metrics_dto(w.test_metrics),
                        train_bars=w.train_bars,
                        test_bars=w.test_bars,
                    )
                    for w in payload.walk_forward.windows
                ],
                in_sample_avg_expectancy_r=payload.walk_forward.in_sample_avg_expectancy_r,
                out_of_sample_avg_expectancy_r=payload.walk_forward.out_of_sample_avg_expectancy_r,
                degradation_pct=payload.walk_forward.degradation_pct,
                is_overfit_signal=payload.walk_forward.is_overfit_signal,
            )
            if payload.walk_forward is not None
            else None
        ),
    )


def _to_metrics_dto(m) -> MetricsDTO:  # type: ignore[no-untyped-def]
    return MetricsDTO(
        total_return_pct=m.total_return_pct,
        max_drawdown_pct=m.max_drawdown_pct,
        max_drawdown_duration_bars=m.max_drawdown_duration_bars,
        bars_evaluated=m.bars_evaluated,
        trade_count=m.trade_count,
        win_rate_pct=m.win_rate_pct,
        expectancy_r=m.expectancy_r,
        profit_factor=m.profit_factor,
        total_costs_paid=m.total_costs_paid,
        avg_win_r=m.avg_win_r,
        avg_loss_r=m.avg_loss_r,
        largest_win_r=m.largest_win_r,
        largest_loss_r=m.largest_loss_r,
        sharpe_like=m.sharpe_like,
        forced_closes=m.forced_closes,
    )
