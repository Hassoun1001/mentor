"""Save the plan behind a trade, and later set the two side by side.

Reads prices, predictions and trades. The only things it writes are a new
trade and its saved plan; forecasts, grading and training are never touched.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import get_instrument
from mentor.domain.journal.comparison import (
    ComparisonSummary,
    TradeComparison,
    compare_trade,
    summarise,
)
from mentor.domain.journal.system_plan import (
    PlanSnapshot,
    SystemResult,
    SystemStatus,
    play_forward,
)
from mentor.domain.journal.trade import Trade, TradePlan, TradeStatus, plan_trade
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.settlement import was_stored_provisional
from mentor.infrastructure.repositories.plan_snapshots import PlanSnapshotRepository
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.infrastructure.repositories.trades import TradeRepository

# How far past a deadline to look for a bar proving the deadline's own bar
# will never arrive. Long enough to span a weekend plus a market holiday.
_FEED_LOOKAHEAD = timedelta(days=5)
_MAX_TRADES = 500


@dataclass(frozen=True, slots=True)
class ComparisonReview:
    comparisons: tuple[TradeComparison, ...]
    summary: ComparisonSummary


class SystemComparisonService:
    def __init__(
        self,
        *,
        trades: TradeRepository,
        plans: PlanSnapshotRepository,
        prices: PriceBarRepository,
        predictions: PredictionRepository,
    ) -> None:
        self._trades = trades
        self._plans = plans
        self._prices = prices
        self._predictions = predictions

    async def log_from_plan(self, plan: TradePlan, snapshot: PlanSnapshot) -> Trade:
        """Create a trade with the plan it came from attached for good."""
        if plan.symbol.upper() != snapshot.symbol.upper():
            raise ValidationError("the trade and its plan are on different symbols", field="symbol")
        prediction_id = await self._predictions.id_at(
            symbol=snapshot.symbol,
            timeframe=snapshot.timeframe.value,
            asof=snapshot.asof,
            model_name=snapshot.model_name,
        )
        trade = await self._trades.add(plan_trade(plan))
        await self._plans.add(trade.id, replace(snapshot, prediction_id=prediction_id))
        return trade

    async def review(self, *, now: datetime | None = None) -> ComparisonReview:
        """Every trade logged from a plan, compared, newest first."""
        moment = now or datetime.now(UTC)
        trades = await self._trades.list_recent(limit=_MAX_TRADES)
        plans = await self._plans.for_trades([t.id for t in trades])

        comparisons: list[TradeComparison] = []
        for trade in trades:
            plan = plans.get(trade.id)
            if plan is None or trade.status is TradeStatus.CANCELLED:
                continue
            system = await self._system_result(plan, moment)
            comparisons.append(
                compare_trade(trade, plan, system, get_instrument(trade.symbol))
            )

        unlinked = sum(1 for t in trades if t.status is TradeStatus.CLOSED and t.id not in plans)
        return ComparisonReview(
            comparisons=tuple(comparisons),
            summary=summarise(comparisons, unlinked_closed=unlinked),
        )

    async def _system_result(self, plan: PlanSnapshot, now: datetime) -> SystemResult:
        if plan.direction is None:
            return SystemResult(status=SystemStatus.NO_TRADE)
        rows = await self._prices.range(
            symbol=plan.symbol,
            timeframe=plan.timeframe,
            start=plan.asof + timedelta(seconds=plan.timeframe.seconds),
            end=plan.time_stop_deadline + _FEED_LOOKAHEAD,
        )
        bars = [
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
            if not was_stored_provisional(r.ts, plan.timeframe, r.ingested_at)
        ]
        return play_forward(plan, bars, instrument=get_instrument(plan.symbol), now=now)
