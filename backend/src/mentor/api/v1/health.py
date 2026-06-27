"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from mentor import __version__

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)
