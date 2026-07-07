"""Macro / FX-driver endpoints — FRED cache ingest + read."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from mentor.api.deps import SessionDep
from mentor.application.macro.ingest import MacroIngestService
from mentor.domain.errors import DomainError
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository

router = APIRouter(prefix="/macro", tags=["macro"])


class MacroIngestRequest(BaseModel):
    days_back: int = Field(default=3650, ge=30, le=7300)


class MacroIngestResponse(BaseModel):
    series_ids: list[str]
    observations_fetched: int
    rows_written: int
    counts_by_series: dict[str, int]


@router.post("/ingest", response_model=MacroIngestResponse)
async def ingest_macro(body: MacroIngestRequest, session: SessionDep) -> MacroIngestResponse:
    """Backfill FRED macro drivers (US rates, 2s10s, broad USD index, VIX)
    so the forecast model can use them as features. Free, no key."""
    service = MacroIngestService(repo=MacroSeriesRepository(session))
    start = datetime.now(UTC) - timedelta(days=body.days_back)
    try:
        result = await service.backfill(start=start, end=datetime.now(UTC))
    except DomainError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return MacroIngestResponse(
        series_ids=list(result.series_ids),
        observations_fetched=result.observations_fetched,
        rows_written=result.rows_written,
        counts_by_series=result.counts_by_series,
    )


class MacroPointDTO(BaseModel):
    series_id: str
    day: datetime
    value: Decimal


@router.get("/series", response_model=list[MacroPointDTO])
async def macro_series(session: SessionDep, limit_per_series: int = 30) -> list[MacroPointDTO]:
    """Most recent observations per series — the macro context snapshot."""
    rows = await MacroSeriesRepository(session).series()
    # Keep only the tail of each series (rows are ordered series, day asc).
    tail: dict[str, list[MacroPointDTO]] = {}
    for r in rows:
        tail.setdefault(r.series_id, []).append(
            MacroPointDTO(series_id=r.series_id, day=r.day, value=Decimal(r.value))
        )
    out: list[MacroPointDTO] = []
    for pts in tail.values():
        out.extend(pts[-limit_per_series:])
    return out
