"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from mentor import __version__
from mentor.api.deps import SettingsDep

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


class IntegrationDTO(BaseModel):
    key: str
    label: str
    configured: bool
    env_var: str
    why: str  # what the user loses while it is unset


class IntegrationsResponse(BaseModel):
    integrations: list[IntegrationDTO]


@router.get("/integrations", response_model=IntegrationsResponse)
async def integrations(settings: SettingsDep) -> IntegrationsResponse:
    """Which optional data sources are actually configured.

    Without this the UI cannot tell "nothing happened in this window" from
    "this feature has never been able to run", so empty panels invite the
    user to press a Refresh button that can only fail. Reports presence
    only — never the key itself.
    """
    return IntegrationsResponse(
        integrations=[
            IntegrationDTO(
                key="news_headlines",
                label="News headlines",
                configured=bool(settings.newsapi_key.get_secret_value().strip()),
                env_var="NEWSAPI_KEY",
                why="The news panel stays empty. Model sentiment is unaffected — "
                "that comes from GDELT, which needs no key.",
            ),
            IntegrationDTO(
                key="economic_calendar",
                label="Economic calendar",
                configured=bool(settings.finnhub_key.get_secret_value().strip()),
                env_var="FINNHUB_KEY",
                why="No scheduled releases are shown, so the event-freeze "
                "warning cannot fire before high-impact news.",
            ),
        ]
    )
