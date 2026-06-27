"""Journal analytics + pre-trade checklist endpoints."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep
from mentor.application.journal import TradeService
from mentor.domain.journal import (
    PreTradeChecklist,
    evaluate_pre_trade_checklist,
)
from mentor.domain.journal.trade import TradePlan
from mentor.domain.money import Money, Percent
from mentor.domain.risk import GuardrailLimits, OpenPosition, check_guardrails
from mentor.domain.risk.position_sizing import Direction
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


@router.get("/journal/analytics", response_model=AnalyticsResponse)
async def journal_analytics(session: SessionDep, symbol: str | None = None) -> AnalyticsResponse:
    service = TradeService(TradeRepository(session))
    a = await service.analytics(symbol=symbol)

    if a.sample_size == 0:
        interp = "No closed trades yet — log a few and analytics will populate."
    elif a.sample_size < 20:
        interp = (
            f"Only {a.sample_size} closed trades — too few to draw conclusions. "
            "Variance dominates this sample; keep journalling."
        )
    elif a.expectancy_r > Decimal("0.2"):
        interp = "Positive expectancy with a meaningful sample — keep doing what works."
    elif a.expectancy_r > 0:
        interp = "Marginal edge — costs and slippage can easily erase it. Watch trade count."
    else:
        interp = "Negative expectancy — review mistake tags and tighten the entry criteria."

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

    # Optional guardrail-context inputs; if absent, the checklist will
    # treat guardrails as passing (UI may still show the warning).
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
    if (
        body.account_balance is not None
        and body.max_risk_per_trade_percent is not None
        and body.max_open_risk_percent is not None
        and body.daily_loss_limit_percent is not None
    ):
        guardrails = check_guardrails(
            account_balance=Money(body.account_balance, body.risk_currency),
            limits=GuardrailLimits(
                max_risk_per_trade=Percent.from_percent(body.max_risk_per_trade_percent),
                max_open_risk=Percent.from_percent(body.max_open_risk_percent),
                daily_loss_limit=Percent.from_percent(body.daily_loss_limit_percent),
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
            ChecklistItemDTO(key=i.key, label=i.label, passed=i.passed, detail=i.detail)
            for i in result.items
        ],
        failed_keys=[i.key for i in result.failed],
    )
