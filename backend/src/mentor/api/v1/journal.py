"""Journal analytics + pre-trade checklist endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep
from mentor.application.journal import TradeService
from mentor.application.journal.system_comparison import SystemComparisonService
from mentor.domain.journal import (
    PreTradeChecklist,
    evaluate_pre_trade_checklist,
)
from mentor.domain.journal.comparison import TradeComparison
from mentor.domain.journal.trade import TradePlan, TradeStatus
from mentor.domain.money import Money, Percent
from mentor.domain.risk import GuardrailLimits, OpenPosition, check_guardrails
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.stats.significance import assess_expectancy, assess_proportion
from mentor.infrastructure.repositories.plan_snapshots import PlanSnapshotRepository
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.infrastructure.repositories.trades import TradeRepository

router = APIRouter(tags=["journal"])


# -------- analytics ---------------------------------------------------------


class AnalyticsResponse(BaseModel):
    sample_size: int
    wins: int
    losses: int
    breakeven: int
    win_rate_percent: Decimal
    avg_win_r: Decimal
    avg_loss_r: Decimal
    expectancy_r: Decimal
    profit_factor: Decimal | None
    largest_win_r: Decimal
    largest_loss_r: Decimal
    total_r: Decimal
    interpretation: str
    # Is any of the above distinguishable from luck yet?
    win_rate_verdict: str = ""
    win_rate_low: float = 0.0
    win_rate_high: float = 0.0
    win_rate_significant: bool = False
    expectancy_verdict: str = ""
    expectancy_low: float = 0.0
    expectancy_high: float = 0.0
    expectancy_significant: bool = False
    trades_needed: int | None = None


@router.get("/journal/analytics", response_model=AnalyticsResponse)
async def journal_analytics(session: SessionDep, symbol: str | None = None) -> AnalyticsResponse:
    service = TradeService(TradeRepository(session))
    a = await service.analytics(symbol=symbol)

    # Judge the numbers statistically rather than against hand-picked
    # thresholds — "20 trades" was never a real bar, and a positive
    # expectancy over 8 trades is not evidence of anything.
    closed = await service.list_recent(symbol=symbol, limit=1000)
    r_values = [
        float(t.realised_r)
        for t in closed
        if t.status is TradeStatus.CLOSED and t.realised_r is not None
    ]
    win = assess_proportion(a.wins, a.sample_size, label="closed trades")
    exp = assess_expectancy(r_values, label="trades")

    if a.sample_size == 0:
        interp = "No closed trades yet — log a few and analytics will populate."
    elif not exp.significant:
        interp = (
            "Your results are not yet distinguishable from a system with no edge. "
            "That is normal this early — it is not a reason to change anything, "
            "and not a reason to size up either."
        )
    elif exp.mean > 0:
        interp = (
            "Positive expectancy that clears statistical noise on this sample. "
            "Keep the process identical; the edge is in the repetition."
        )
    else:
        interp = (
            "Negative expectancy beyond what variance explains. Work the loss "
            "root-cause review before placing another trade."
        )

    return AnalyticsResponse(
        sample_size=a.sample_size,
        wins=a.wins,
        losses=a.losses,
        breakeven=a.breakeven,
        win_rate_percent=a.win_rate.as_percent,
        avg_win_r=a.avg_win_r,
        avg_loss_r=a.avg_loss_r,
        expectancy_r=a.expectancy_r,
        profit_factor=a.profit_factor,
        largest_win_r=a.largest_win_r,
        largest_loss_r=a.largest_loss_r,
        total_r=a.total_r,
        interpretation=interp,
        win_rate_verdict=win.verdict,
        win_rate_low=win.low,
        win_rate_high=win.high,
        win_rate_significant=win.significant,
        expectancy_verdict=exp.verdict,
        expectancy_low=exp.low,
        expectancy_high=exp.high,
        expectancy_significant=exp.significant,
        trades_needed=exp.n_needed,
    )


# -------- trade versus system -----------------------------------------------


class SystemSideDTO(BaseModel):
    status: str  # pending | finished | no_trade
    entry_price: Decimal | None
    exit_price: Decimal | None
    exit_reason: str | None
    exit_ts: datetime | None
    pips: Decimal | None
    r: Decimal | None


class ActualSideDTO(BaseModel):
    direction: Direction
    entry_price: Decimal | None
    exit_price: Decimal | None
    exit_reason: str | None
    exit_ts: datetime | None
    pips: Decimal | None
    r: Decimal | None


class SavedPlanDTO(BaseModel):
    stance: str
    asof: datetime
    timeframe: str
    model_name: str
    p_up: Decimal
    confidence: Decimal
    entry: Decimal | None
    stop: Decimal | None
    target: Decimal | None
    reward_multiple: Decimal | None
    horizon_bars: int
    time_stop_deadline: datetime
    prediction_id: uuid.UUID | None


class TradeComparisonDTO(BaseModel):
    trade_id: uuid.UUID
    verdict: str | None  # match | partial | no_match | pending; None until closed
    explanation: str
    plan: SavedPlanDTO
    system: SystemSideDTO
    actual: ActualSideDTO
    entry_slippage_pips: Decimal | None
    r_difference: Decimal | None


class ComparisonSummaryDTO(BaseModel):
    matches: int
    partials: int
    no_matches: int
    pending: int
    unlinked: int
    compared: int
    system_r: Decimal
    actual_r: Decimal
    execution_r: Decimal
    headline: str


class SystemComparisonResponse(BaseModel):
    summary: ComparisonSummaryDTO
    trades: list[TradeComparisonDTO]


def _comparison_dto(c: TradeComparison) -> TradeComparisonDTO:
    plan, system = c.plan, c.system
    return TradeComparisonDTO(
        trade_id=c.trade_id,
        verdict=c.verdict.value if c.verdict else None,
        explanation=c.explanation,
        plan=SavedPlanDTO(
            stance=plan.stance.value,
            asof=plan.asof,
            timeframe=plan.timeframe.value,
            model_name=plan.model_name,
            p_up=plan.p_up,
            confidence=plan.confidence,
            entry=plan.entry,
            stop=plan.stop,
            target=plan.target,
            reward_multiple=plan.reward_multiple,
            horizon_bars=plan.horizon_bars,
            time_stop_deadline=plan.time_stop_deadline,
            prediction_id=plan.prediction_id,
        ),
        system=SystemSideDTO(
            status=system.status.value,
            entry_price=system.entry_price,
            exit_price=system.exit_price,
            exit_reason=system.exit_reason.value if system.exit_reason else None,
            exit_ts=system.exit_ts,
            pips=system.pips,
            r=system.r,
        ),
        actual=ActualSideDTO(
            direction=c.actual_direction,
            entry_price=c.actual_entry,
            exit_price=c.actual_exit,
            exit_reason=c.actual_exit_reason.value if c.actual_exit_reason else None,
            exit_ts=c.actual_exit_ts,
            pips=c.actual_pips,
            r=c.actual_r,
        ),
        entry_slippage_pips=c.entry_slippage_pips,
        r_difference=c.r_difference,
    )


@router.get("/journal/system-comparison", response_model=SystemComparisonResponse)
async def system_comparison(session: SessionDep) -> SystemComparisonResponse:
    """Each trade logged from a plan, set beside what the plan itself did."""
    review = await SystemComparisonService(
        trades=TradeRepository(session),
        plans=PlanSnapshotRepository(session),
        prices=PriceBarRepository(session),
        predictions=PredictionRepository(session),
    ).review()
    s = review.summary
    return SystemComparisonResponse(
        summary=ComparisonSummaryDTO(
            matches=s.matches,
            partials=s.partials,
            no_matches=s.no_matches,
            pending=s.pending,
            unlinked=s.unlinked,
            compared=s.compared,
            system_r=s.system_r,
            actual_r=s.actual_r,
            execution_r=s.execution_r,
            headline=s.headline,
        ),
        trades=[_comparison_dto(c) for c in review.comparisons],
    )


# -------- pre-trade checklist ----------------------------------------------


class OpenPositionDTO(BaseModel):
    amount: Decimal
    currency: str


class ChecklistRequest(BaseModel):
    symbol: str
    direction: Direction
    size_lots: Annotated[Decimal, Field(ge=0)]
    entry: Annotated[Decimal, Field(gt=0)]
    stop: Annotated[Decimal, Field(gt=0)]
    target: Annotated[Decimal | None, Field(gt=0)] = None
    initial_risk_amount: Annotated[Decimal, Field(gt=0)]
    risk_currency: str
    reason: str

    # Guardrail context. Supplying account_balance and
    # max_risk_per_trade_percent is enough to check the rule that matters
    # most; the other two limits refine it. With none of them the guardrail
    # item reports as *not checked* rather than as passing.
    account_balance: Annotated[Decimal, Field(gt=0)] | None = None
    max_risk_per_trade_percent: Annotated[Decimal, Field(gt=0, le=10)] | None = None
    max_open_risk_percent: Annotated[Decimal, Field(gt=0, le=25)] | None = None
    daily_loss_limit_percent: Annotated[Decimal, Field(gt=0, le=25)] | None = None
    open_positions: list[OpenPositionDTO] = Field(default_factory=list)
    realised_pnl_today: OpenPositionDTO | None = None


class ChecklistItemDTO(BaseModel):
    key: str
    label: str
    passed: bool
    skipped: bool = False
    detail: str | None


class ChecklistResponse(BaseModel):
    passed: bool
    items: list[ChecklistItemDTO]
    failed_keys: list[str]


@router.post("/checklist/pre-trade", response_model=ChecklistResponse)
async def pre_trade_checklist(body: ChecklistRequest) -> ChecklistResponse:
    plan = TradePlan(
        symbol=body.symbol,
        direction=body.direction,
        size_lots=body.size_lots,
        entry=body.entry,
        stop=body.stop,
        target=body.target,
        initial_risk=Money(body.initial_risk_amount, body.risk_currency),
        reason=body.reason,
    )

    guardrails = None
    # Per-trade risk is the limit that actually stops accounts dying, so it
    # is checkable on its own. Requiring all four before evaluating anything
    # meant the common case — a user who set a risk percent and nothing else
    # — silently got no check at all.
    if body.account_balance is not None and body.max_risk_per_trade_percent is not None:
        guardrails = check_guardrails(
            account_balance=Money(body.account_balance, body.risk_currency),
            limits=GuardrailLimits(
                max_risk_per_trade=Percent.from_percent(body.max_risk_per_trade_percent),
                # Absent limits fall back to the schema's own ceilings rather
                # than blocking the per-trade check that was supplied.
                max_open_risk=Percent.from_percent(
                    body.max_open_risk_percent
                    if body.max_open_risk_percent is not None
                    else Decimal("25")
                ),
                daily_loss_limit=Percent.from_percent(
                    body.daily_loss_limit_percent
                    if body.daily_loss_limit_percent is not None
                    else Decimal("25")
                ),
            ),
            prospective_trade_risk=Money(body.initial_risk_amount, body.risk_currency),
            open_positions=[OpenPosition(Money(p.amount, p.currency)) for p in body.open_positions],
            realised_pnl_today=(
                Money(body.realised_pnl_today.amount, body.realised_pnl_today.currency)
                if body.realised_pnl_today
                else None
            ),
        )

    result = evaluate_pre_trade_checklist(plan, rules=PreTradeChecklist(), guardrails=guardrails)
    return ChecklistResponse(
        passed=result.passed,
        items=[
            ChecklistItemDTO(
                key=i.key,
                label=i.label,
                passed=i.passed,
                detail=i.detail,
                skipped=i.skipped,
            )
            for i in result.items
        ],
        failed_keys=[i.key for i in result.failed],
    )
