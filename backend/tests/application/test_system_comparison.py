"""Log from a plan → open → close → compare, as one chain.

Runs the service against fake repositories, for the same reason as
``test_trade_lifecycle``: the endpoints need Postgres. It covers what the
domain tests cannot: that a provisional bar is dropped on the way in, that
hand-logged trades stay out of the comparison, and that the prediction is
looked up for the plan's own bar.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.application.journal import TradeService
from mentor.application.journal.system_comparison import SystemComparisonService
from mentor.domain.errors import ValidationError
from mentor.domain.journal.comparison import Verdict
from mentor.domain.journal.system_plan import (
    PlanSnapshot,
    PlanStance,
    SystemStatus,
    time_stop_deadline,
)
from mentor.domain.journal.trade import Trade, TradePlan
from mentor.domain.market.bars import Timeframe
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.strategy_lab.simulator import ExitReason

ASOF = datetime(2026, 11, 3, 8, tzinfo=UTC)
HOUR = timedelta(hours=1)
NOW = datetime(2026, 12, 1, tzinfo=UTC)
PREDICTION = uuid.uuid4()


class _FakeTrades:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Trade] = {}

    async def add(self, trade: Trade) -> Trade:
        self.rows[trade.id] = trade
        return trade

    async def get(self, trade_id: uuid.UUID) -> Trade | None:
        return self.rows.get(trade_id)

    async def save(self, trade: Trade) -> Trade:
        self.rows[trade.id] = trade
        return trade

    async def list_recent(self, *, symbol: str | None = None, limit: int = 100) -> list[Trade]:
        return list(self.rows.values())[:limit]


class _FakePlans:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, PlanSnapshot] = {}

    async def add(self, trade_id: uuid.UUID, snapshot: PlanSnapshot) -> None:
        self.rows[trade_id] = snapshot

    async def for_trades(self, trade_ids: list[uuid.UUID]) -> dict[uuid.UUID, PlanSnapshot]:
        return {i: self.rows[i] for i in trade_ids if i in self.rows}


@dataclass
class _Row:
    ts: datetime
    high: Decimal
    low: Decimal
    ingested_at: datetime
    symbol: str = "EURUSD"
    timeframe: str = "1h"
    open: Decimal = Decimal("1.1000")
    close: Decimal = Decimal("1.1000")
    volume: Decimal | None = None
    source: str = "test"


def _row(ts: datetime, high: str = "1.1005", low: str = "1.0995", *, early: bool = False) -> _Row:
    return _Row(
        ts=ts,
        high=Decimal(high),
        low=Decimal(low),
        ingested_at=ts + timedelta(minutes=10) if early else ts + timedelta(hours=1, minutes=2),
    )


class _FakePrices:
    def __init__(self, rows: list[_Row]) -> None:
        self.rows = rows

    async def range(
        self, *, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[_Row]:
        return [r for r in self.rows if start <= r.ts < end]


class _FakePredictions:
    async def id_at(
        self, *, symbol: str, timeframe: str, asof: datetime, model_name: str
    ) -> uuid.UUID | None:
        return PREDICTION if asof == ASOF and model_name == "champion" else None


def _snapshot(stance: PlanStance = PlanStance.LONG, model: str = "champion") -> PlanSnapshot:
    levels: dict[str, Decimal] = (
        {
            "entry": Decimal("1.1000"),
            "stop": Decimal("1.0970"),
            "target": Decimal("1.1060"),
            "reward_multiple": Decimal("2"),
        }
        if stance is PlanStance.LONG
        else {}
    )
    return PlanSnapshot(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        asof=ASOF,
        model_name=model,
        p_up=Decimal("0.62"),
        confidence=Decimal("0.24"),
        stance=stance,
        horizon_bars=24,
        time_stop_deadline=time_stop_deadline(ASOF, 24, Timeframe.H1),
        **levels,
    )


def _ticket(symbol: str = "EURUSD") -> TradePlan:
    return TradePlan(
        symbol=symbol,
        direction=Direction.LONG,
        size_lots=Decimal("0.33"),
        entry=Decimal("1.1000"),
        stop=Decimal("1.0970"),
        target=Decimal("1.1060"),
        initial_risk=Money(Decimal("100"), "USD"),
        reason="taking the system's plan as shown",
    )


@dataclass
class _Rig:
    trades: _FakeTrades
    plans: _FakePlans
    journal: TradeService
    service: SystemComparisonService


def _rig(rows: list[_Row] | None = None) -> _Rig:
    trades, plans = _FakeTrades(), _FakePlans()
    return _Rig(
        trades=trades,
        plans=plans,
        journal=TradeService(trades),  # type: ignore[arg-type]
        service=SystemComparisonService(
            trades=trades,  # type: ignore[arg-type]
            plans=plans,  # type: ignore[arg-type]
            prices=_FakePrices(rows or []),  # type: ignore[arg-type]
            predictions=_FakePredictions(),  # type: ignore[arg-type]
        ),
    )


async def _log_and_close(rig: _Rig, exit_price: str, snapshot: PlanSnapshot | None = None) -> None:
    trade = await rig.service.log_from_plan(_ticket(), snapshot or _snapshot())
    await rig.journal.open(trade.id, fill_price=Decimal("1.1001"), at=ASOF + HOUR * 2)
    await rig.journal.close(trade.id, exit_price=Decimal(exit_price), at=ASOF + HOUR * 4)


@pytest.mark.asyncio
async def test_logging_links_the_prediction_for_the_plans_own_bar() -> None:
    rig = _rig()
    trade = await rig.service.log_from_plan(_ticket(), _snapshot())
    assert rig.plans.rows[trade.id].prediction_id == PREDICTION


@pytest.mark.asyncio
async def test_a_plan_with_no_logged_prediction_is_still_saved() -> None:
    rig = _rig()
    trade = await rig.service.log_from_plan(_ticket(), _snapshot(model="other"))
    assert rig.plans.rows[trade.id].prediction_id is None


@pytest.mark.asyncio
async def test_a_plan_and_trade_on_different_symbols_is_refused() -> None:
    rig = _rig()
    with pytest.raises(ValidationError):
        await rig.service.log_from_plan(_ticket("GBPUSD"), _snapshot())
    assert not rig.trades.rows


@pytest.mark.asyncio
async def test_full_chain_from_plan_to_match() -> None:
    rig = _rig([_row(ASOF + HOUR * 3, high="1.1070")])
    await _log_and_close(rig, "1.1060")

    review = await rig.service.review(now=NOW)

    assert len(review.comparisons) == 1
    c = review.comparisons[0]
    assert c.system.exit_reason is ExitReason.TARGET
    assert c.verdict is Verdict.MATCH
    assert review.summary.matches == 1


@pytest.mark.asyncio
async def test_a_bar_stored_before_it_finished_cannot_decide_the_result() -> None:
    rig = _rig([_row(ASOF + HOUR * 3, high="1.1070", early=True)])
    await _log_and_close(rig, "1.1060")

    c = (await rig.service.review(now=NOW)).comparisons[0]

    assert c.system.status is SystemStatus.PENDING
    assert c.verdict is Verdict.PENDING


@pytest.mark.asyncio
async def test_a_trade_taken_against_a_stand_aside_plan_is_no_match() -> None:
    rig = _rig()
    await _log_and_close(rig, "1.1030", _snapshot(PlanStance.STAND_ASIDE))

    review = await rig.service.review(now=NOW)

    assert review.comparisons[0].verdict is Verdict.NO_MATCH
    assert review.summary.system_r == Decimal("0")


@pytest.mark.asyncio
async def test_hand_logged_trades_stay_valid_and_are_only_counted_as_unlinked() -> None:
    rig = _rig()
    trade = await rig.journal.plan(_ticket())
    await rig.journal.open(trade.id, fill_price=Decimal("1.1001"))
    await rig.journal.close(trade.id, exit_price=Decimal("1.1030"))

    review = await rig.service.review(now=NOW)

    assert review.comparisons == ()
    assert review.summary.unlinked == 1


@pytest.mark.asyncio
async def test_cancelled_trades_are_left_out() -> None:
    rig = _rig()
    trade = await rig.service.log_from_plan(_ticket(), _snapshot())
    await rig.journal.cancel(trade.id)

    assert (await rig.service.review(now=NOW)).comparisons == ()
