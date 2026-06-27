"""Alerts endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep
from mentor.application.alerts import AlertService
from mentor.domain.alerts.alert import Alert, AlertKind, AlertStatus
from mentor.domain.alerts.event_freeze import evaluate_event_freeze
from mentor.domain.calendar.event import ImpactLevel
from mentor.domain.errors import ValidationError
from mentor.infrastructure.repositories import (
    AlertRepository,
    EconomicEventRepository,
    NewsRepository,
    PriceBarRepository,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ---------- DTOs ----------


class CreatePriceAlertRequest(BaseModel):
    symbol: str
    kind: Literal["price_above", "price_below"]
    price_level: Annotated[Decimal, Field(gt=0)]
    label: str


class AlertDTO(BaseModel):
    id: uuid.UUID
    kind: AlertKind
    label: str
    status: AlertStatus
    symbol: str | None
    price_level: Decimal | None
    created_at: datetime
    fired_at: datetime | None


class SweepResponse(BaseModel):
    evaluated: int
    fired: int


class EventFreezeDTO(BaseModel):
    triggered: bool
    upcoming_count: int
    soft: bool
    blocking_reason: str | None
    label: str


# ---------- helpers ----------


def _service(session: SessionDep) -> AlertService:
    return AlertService(alerts=AlertRepository(session), prices=PriceBarRepository(session))


def _to_dto(alert: Alert) -> AlertDTO:
    return AlertDTO(
        id=alert.id,
        kind=alert.kind,
        label=alert.label,
        status=alert.status,
        symbol=alert.condition.symbol,
        price_level=alert.condition.price_level,
        created_at=alert.created_at,
        fired_at=alert.fired_at,
    )


# ---------- endpoints ----------


@router.get("", response_model=list[AlertDTO])
async def list_alerts(session: SessionDep) -> list[AlertDTO]:
    items = await _service(session).list()
    return [_to_dto(a) for a in items]


@router.post("", response_model=AlertDTO)
async def create_price_alert(body: CreatePriceAlertRequest, session: SessionDep) -> AlertDTO:
    try:
        alert = await _service(session).arm_price_alert(
            symbol=body.symbol,
            kind=AlertKind(body.kind),
            price_level=body.price_level,
            label=body.label,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_dto(alert)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: uuid.UUID, session: SessionDep) -> None:
    ok = await _service(session).delete(alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="alert not found")


@router.post("/{alert_id}/disable", response_model=AlertDTO)
async def disable_alert(alert_id: uuid.UUID, session: SessionDep) -> AlertDTO:
    alert = await _service(session).disable(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return _to_dto(alert)


@router.post("/sweep", response_model=SweepResponse)
async def sweep(session: SessionDep) -> SweepResponse:
    result = await _service(session).sweep_price_alerts()
    return SweepResponse(evaluated=result.evaluated, fired=result.fired)


@router.get("/event-freeze", response_model=EventFreezeDTO)
async def event_freeze(
    session: SessionDep,
    minutes_before: int = 30,
    minutes_after: int = 30,
    min_impact: Decimal = Decimal("0.6"),
) -> EventFreezeDTO:
    """Evaluate the event-freeze window against classified news *and*
    scheduled economic releases surrounding *now*. The frontend calls
    this before showing the new-trade form."""
    now = datetime.now(UTC)
    news = await NewsRepository(session).recent(
        limit=100, only_classified=True, min_impact=min_impact
    )
    # Window for scheduled events covers a generous buffer; the evaluator
    # filters by the actual minutes_before/after.
    events = await EconomicEventRepository(session).range(
        start=now - timedelta(minutes=max(minutes_after, 120)),
        end=now + timedelta(minutes=max(minutes_before, 120)),
        min_impact=ImpactLevel.MEDIUM,
    )
    window = evaluate_event_freeze(
        now=now,
        upcoming=news,
        upcoming_events=events,
        min_impact=min_impact,
        minutes_before=minutes_before,
        minutes_after=minutes_after,
    )
    return EventFreezeDTO(
        triggered=window.triggered,
        upcoming_count=window.upcoming_count,
        soft=window.soft,
        blocking_reason=window.blocking_reason,
        label=window.label,
    )
