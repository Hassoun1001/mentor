"""Economic-calendar endpoints."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep
from mentor.application.calendar import CalendarService
from mentor.domain.calendar.event import ImpactLevel
from mentor.infrastructure.adapters.calendar import FinnhubCalendarAdapter
from mentor.infrastructure.repositories import EconomicEventRepository

router = APIRouter(prefix="/calendar", tags=["calendar"])


class IngestRequest(BaseModel):
    hours_back: int = Field(default=24, ge=0, le=720)
    hours_ahead: int = Field(default=72, ge=1, le=720)


class IngestResponse(BaseModel):
    fetched: int
    upserted: int


@router.post("/ingest", response_model=IngestResponse)
async def ingest(body: IngestRequest, session: SessionDep) -> IngestResponse:
    api_key = os.environ.get("FINNHUB_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="FINNHUB_KEY not configured — add it to .env to fetch the economic calendar.",
        )
    adapter = FinnhubCalendarAdapter(api_key=api_key)
    repo = EconomicEventRepository(session)
    service = CalendarService(adapter=adapter, repo=repo)

    now = datetime.now(UTC)
    since = now - timedelta(hours=body.hours_back)
    until = now + timedelta(hours=body.hours_ahead)
    try:
        result = await service.ingest(since=since, until=until)
    finally:
        await adapter.aclose()
    return IngestResponse(fetched=result.fetched, upserted=result.upserted)


class EconomicEventDTO(BaseModel):
    id: uuid.UUID
    source: str
    ts: datetime
    name: str
    country: str
    impact: int
    forecast: str | None
    previous: str | None
    actual: str | None


@router.get("", response_model=list[EconomicEventDTO])
async def list_events(
    session: SessionDep,
    hours_back: int = 6,
    hours_ahead: int = 48,
    min_impact: int = 2,  # default to MEDIUM+
) -> list[EconomicEventDTO]:
    now = datetime.now(UTC)
    impact_level = ImpactLevel(max(1, min(3, min_impact)))
    items = await EconomicEventRepository(session).range(
        start=now - timedelta(hours=hours_back),
        end=now + timedelta(hours=hours_ahead),
        min_impact=impact_level,
    )
    return [
        EconomicEventDTO(
            id=item.id,
            source=item.source,
            ts=item.ts,
            name=item.name,
            country=item.country,
            impact=int(item.impact),
            forecast=item.forecast,
            previous=item.previous,
            actual=item.actual,
        )
        for item in items
    ]
