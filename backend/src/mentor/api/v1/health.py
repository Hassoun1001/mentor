"""Liveness and readiness probes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel

from mentor import __version__
from mentor.api.deps import SessionDep, SettingsDep
from mentor.application.forecasting.economics import BREAKEVEN_LABEL, lane_breakeven
from mentor.application.forecasting.promotion import PromotionService
from mentor.application.health import build_digest
from mentor.application.scheduler.drift import select_independent
from mentor.domain.forecasting.forecast import Direction
from mentor.domain.market.bars import Timeframe
from mentor.domain.stats.significance import assess_proportion
from mentor.infrastructure.repositories import PredictionRepository, PriceBarRepository

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
    timeframe = Timeframe(settings.loop_timeframe)

    prices = PriceBarRepository(session)
    newest = await prices.latest(symbol=settings.loop_symbol, timeframe=timeframe)

    predictions = PredictionRepository(session)
    recent = await predictions.list_recent(limit=2000)
    pending = [r for r in recent if r.realised_outcome is None]
    overdue = sum(1 for r in pending if r.horizon_at < now)

    # Same independence discipline the Loop page uses: overlapping signals
    # are one observation, not many.
    resolved = await predictions.list_resolved(limit=5000)
    independent = select_independent(
        [
            (r.asof, r.horizon_at, float(r.p_up), int(r.realised_outcome))
            for r in resolved
            if r.realised_outcome is not None and r.direction != Direction.NEUTRAL.value
        ]
    )
    hits = sum(
        1
        for p_up, outcome in independent
        if (p_up >= 0.5 and outcome == 1) or (p_up < 0.5 and outcome == 0)
    )
    # Graded against what a call must clear to pay for itself, not against a
    # coin flip. On the 24-bar lane that is 52.36%, so a 51% record is "still
    # losing money", not "slightly ahead".
    basis = await lane_breakeven(session, settings=settings)
    verdict = assess_proportion(
        hits,
        len(independent),
        baseline=basis.breakeven,
        label="independent windows",
        baseline_label=BREAKEVEN_LABEL if basis.measured else "a coin flip",
    )

    promo = PromotionService(model_store_dir=settings.model_store_dir)
    last_retrain: datetime | None = None
    history = promo.promotion_history(limit=1)
    if history:
        raw = history[0].get("at")
        if isinstance(raw, str):
            try:
                last_retrain = datetime.fromisoformat(raw)
            except ValueError:
                last_retrain = None

    scheduler = getattr(request.app.state, "scheduler", None)
    alerts_enabled = bool(getattr(scheduler, "alerts_enabled", False)) if scheduler else False
    if scheduler is not None and hasattr(scheduler, "status"):
        alerts_enabled = bool(scheduler.status().get("alerts_enabled", False))

    d = build_digest(
        window_days=7,
        newest_bar=newest.ts if newest is not None else None,
        ingest_interval_minutes=settings.loop_ingest_interval_minutes,
        pending_predictions=len(pending),
        overdue_predictions=overdue,
        last_retrain=last_retrain,
        retrain_interval_hours=settings.loop_retrain_interval_hours,
        alerts_enabled=alerts_enabled,
        independent_windows=len(independent),
        windows_needed=verdict.n_needed or 30,
        paper_verdict=verdict.verdict,
        now=now,
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
