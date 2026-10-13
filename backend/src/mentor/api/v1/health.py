"""Liveness and readiness probes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel

from mentor import __version__
from mentor.api.deps import SessionDep, SettingsDep
from mentor.application.health.collect import collect_digest
from mentor.application.health.self_report import collect_self_report

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


# ---------- "has this been working while I was away?" ----------


class CheckDTO(BaseModel):
    key: str
    label: str
    level: str
    detail: str


class DigestResponse(BaseModel):
    generated_at: datetime
    window_days: int
    status: str  # worst level across the checks
    headline: str
    evidence: str
    checks: list[CheckDTO]


@router.get("/digest", response_model=DigestResponse)
async def digest(
    request: Request, session: SessionDep, settings: SettingsDep
) -> DigestResponse:
    """Did it run, and where does the evidence stand.

    Deliberately answers those two separately: the first is knowable after a
    week, the second is not, and merging them is how a rising signal count
    starts looking like progress.
    """
    now = datetime.now(UTC)
    d = await collect_digest(
        session, settings, alerts_enabled=_alerts_enabled(request), now=now
    )

    return DigestResponse(
        generated_at=d.generated_at,
        window_days=d.window_days,
        status=d.worst.value,
        headline=d.headline,
        evidence=d.evidence,
        checks=[
            CheckDTO(key=c.key, label=c.label, level=c.level.value, detail=c.detail)
            for c in d.checks
        ],
    )


def _loop_status(request: Request) -> dict[str, object] | None:
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None or not hasattr(scheduler, "status"):
        return None
    status = scheduler.status()
    return status if isinstance(status, dict) else None


def _alerts_enabled(request: Request) -> bool:
    status = _loop_status(request)
    return bool(status.get("alerts_enabled", False)) if status else False


# ---------- the self-report: what the system knows about itself ----------


@router.get("/report")
async def report(
    request: Request, session: SessionDep, settings: SettingsDep
) -> dict[str, object]:
    """Everything the system can tell about its own state, machine-readable.

    Computed live on request; the weekly job additionally writes it to disk
    and sends the summary to Telegram. Aggregates only — no credentials, no
    raw predictions — because like the digest it is served without auth, so
    a maintenance agent can read it without holding a secret.
    """
    r = await collect_self_report(session, settings, loop_status=_loop_status(request))
    return r.to_dict()
