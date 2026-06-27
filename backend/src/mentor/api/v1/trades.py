"""Trade journal endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from mentor.api.deps import SessionDep
from mentor.application.journal import TradeService
from mentor.domain.journal.trade import TradePlan, TradeStatus
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction
from mentor.infrastructure.repositories.trades import TradeRepository

router = APIRouter(prefix="/trades", tags=["journal"])


class MoneyDTO(BaseModel):
    amount: Decimal
    currency: str = Field(..., min_length=3, max_length=3)


class PlanTradeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "EURUSD",
                "direction": "long",
                "size_lots": "0.33",
                "entry": "1.08500",
                "stop": "1.08200",
                "target": "1.09100",
                "initial_risk": {"amount": "100", "currency": "USD"},
                "reason": "Pullback to 200-EMA in an uptrend, with calm news calendar.",
            }
        }
    )

    symbol: str
    direction: Direction
    size_lots: Annotated[Decimal, Field(ge=0)]
    entry: Annotated[Decimal, Field(gt=0)]
    stop: Annotated[Decimal, Field(gt=0)]
    target: Annotated[Decimal | None, Field(gt=0)] = None
    initial_risk: MoneyDTO
    reason: str


class OpenTradeRequest(BaseModel):
    fill_price: Annotated[Decimal, Field(gt=0)]
    at: datetime | None = None


class CloseTradeRequest(BaseModel):
    exit_price: Annotated[Decimal, Field(gt=0)]
    at: datetime | None = None
    quote_to_account_rate: Annotated[Decimal, Field(gt=0)] = Decimal("1")
    mistake_tags: list[str] = Field(default_factory=list)
    emotion: str | None = None
    notes: str | None = None


class TradeResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    direction: Direction
    status: TradeStatus
    size_lots: Decimal
    planned_entry: Decimal
    planned_stop: Decimal
    planned_target: Decimal | None
    actual_entry: Decimal | None
    actual_exit: Decimal | None
    entry_ts: datetime | None
    exit_ts: datetime | None
    initial_risk: MoneyDTO
    realised_pnl: MoneyDTO | None
    realised_r: Decimal | None
    reason: str
    mistake_tags: list[str]
    emotion: str | None
    notes: str | None


def _to_response(t) -> TradeResponse:  # type: ignore[no-untyped-def]
    return TradeResponse(
        id=t.id,
        symbol=t.symbol,
        direction=t.direction,
        status=t.status,
        size_lots=t.size_lots,
        planned_entry=t.planned_entry,
        planned_stop=t.planned_stop,
        planned_target=t.planned_target,
        actual_entry=t.actual_entry,
        actual_exit=t.actual_exit,
        entry_ts=t.entry_ts,
        exit_ts=t.exit_ts,
        initial_risk=MoneyDTO(amount=t.initial_risk.amount, currency=t.initial_risk.currency),
        realised_pnl=(
            MoneyDTO(amount=t.realised_pnl.amount, currency=t.realised_pnl.currency)
            if t.realised_pnl
            else None
        ),
        realised_r=t.realised_r,
        reason=t.reason,
        mistake_tags=list(t.mistake_tags),
        emotion=t.emotion,
        notes=t.notes,
    )


def _service(session: SessionDep) -> TradeService:
    return TradeService(TradeRepository(session))


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def plan_trade(body: PlanTradeRequest, session: SessionDep) -> TradeResponse:
    plan = TradePlan(
        symbol=body.symbol.upper(),
        direction=body.direction,
        size_lots=body.size_lots,
        entry=body.entry,
        stop=body.stop,
        target=body.target,
        initial_risk=Money(body.initial_risk.amount, body.initial_risk.currency),
        reason=body.reason,
    )
    trade = await _service(session).plan(plan)
    return _to_response(trade)


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    session: SessionDep,
    symbol: str | None = None,
    limit: int = 100,
) -> list[TradeResponse]:
    trades = await _service(session).list_recent(symbol=symbol, limit=limit)
    return [_to_response(t) for t in trades]


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: uuid.UUID, session: SessionDep) -> TradeResponse:
    repo = TradeRepository(session)
    trade = await repo.get(trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail="trade not found")
    return _to_response(trade)


@router.post("/{trade_id}/open", response_model=TradeResponse)
async def open_trade_endpoint(
    trade_id: uuid.UUID, body: OpenTradeRequest, session: SessionDep
) -> TradeResponse:
    trade = await _service(session).open(trade_id, fill_price=body.fill_price, at=body.at)
    return _to_response(trade)


@router.post("/{trade_id}/cancel", response_model=TradeResponse)
async def cancel_trade_endpoint(trade_id: uuid.UUID, session: SessionDep) -> TradeResponse:
    trade = await _service(session).cancel(trade_id)
    return _to_response(trade)


@router.post("/{trade_id}/close", response_model=TradeResponse)
async def close_trade_endpoint(
    trade_id: uuid.UUID, body: CloseTradeRequest, session: SessionDep
) -> TradeResponse:
    trade = await _service(session).close(
        trade_id,
        exit_price=body.exit_price,
        at=body.at,
        quote_to_account_rate=body.quote_to_account_rate,
        mistake_tags=tuple(body.mistake_tags),
        emotion=body.emotion,
        notes=body.notes,
    )
    return _to_response(trade)
