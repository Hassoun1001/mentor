"""Strategy lab endpoints — read-only views of what the lab has tested and is watching.

Evaluation and paper trading run from the scheduler, never from a request:
an HTTP call that could trigger a re-test would be a way to spend the
held-out period twice.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mentor.api.deps import SessionDep
from mentor.application.strategy_lab.summary import collect_lab_view, position_dict
from mentor.infrastructure.repositories.strategy_lab import StrategyLabRepository

router = APIRouter(prefix="/strategy-lab", tags=["strategy-lab"])


class PaperRecordDTO(BaseModel):
    trades: int
    mean_r: float | None
    win_rate: float | None
    breakeven_win_rate: float | None
    ci_low: float | None
    ci_high: float | None
    verdict: str
    next_check_at: int
    open_position: dict[str, Any] | None
    pending_order: dict[str, Any] | None
    last_bar_ts: str | None


class CandidateDTO(BaseModel):
    key: str
    title: str
    family: str
    timeframe: str
    hypothesis: str
    status: str
    status_reason: str
    evaluated_at: str
    n_trials_at_evaluation: int
    plan: dict[str, Any] | None
    evidence: dict[str, Any]
    clears_todays_bar: bool
    paper_started_at: str | None
    promoted_at: str | None
    demoted_at: str | None
    retired_at: str | None
    paper: PaperRecordDTO | None


class LabCountsDTO(BaseModel):
    evaluated: int
    passed_backtest: int
    paper: int
    recommended: int
    retired: int


class LabEventDTO(BaseModel):
    key: str
    kind: str
    at: str
    detail: str


class LabResponse(BaseModel):
    trials_ever: int
    dispersion: float
    bar_now: float
    paper_account: str
    counts: LabCountsDTO
    candidates: list[CandidateDTO]
    waiting: list[str]
    changed: list[str]
    events_week: list[LabEventDTO]


class PositionsResponse(BaseModel):
    key: str
    positions: list[dict[str, Any]]


@router.get("", response_model=LabResponse)
async def lab(session: SessionDep) -> LabResponse:
    """Every evaluated idea, its back-test verdict, and its paper record."""
    view = await collect_lab_view(StrategyLabRepository(session), now=datetime.now(UTC))
    return LabResponse.model_validate(view.to_dict())


@router.get("/{key}/positions", response_model=PositionsResponse)
async def positions(
    key: str,
    session: SessionDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> PositionsResponse:
    """A paper-trading strategy's positions, newest signal first."""
    repo = StrategyLabRepository(session)
    row = next((c for c in await repo.list_candidates() if c.key == key), None)
    if row is None:
        raise HTTPException(status_code=404, detail=f"no evaluated strategy {key!r}")
    if row.paper_started_at is None:
        return PositionsResponse(key=key, positions=[])  # never paper traded
    rows = await repo.positions(row.id, limit=limit)
    return PositionsResponse(key=key, positions=[position_dict(p) for p in rows])
