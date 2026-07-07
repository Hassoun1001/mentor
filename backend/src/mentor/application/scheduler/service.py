"""In-process scheduler for the autonomous prediction loop.

Runs three jobs on a cadence, each in its own DB transaction:

- **predict** — generate a live forecast from the latest bars and log it
  to the audit table (champion model if one has been promoted, else the
  baseline rule).
- **resolve** — fill the realised outcome of any prediction whose horizon
  has elapsed and whose outcome bar now exists.
- **retrain** — retrain a challenger and promote it only if it beats the
  champion's out-of-sample calibration.

The scheduler is opt-in (`MENTOR_LOOP_ENABLED`). The same job bodies are
exposed as `run_*_once` so the API can trigger a single cycle on demand —
useful for testing without waiting for the next tick.
"""

from __future__ import annotations

from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mentor.application.forecasting.inference_service import ForecastService
from mentor.application.forecasting.promotion import PromotionService
from mentor.application.forecasting.resolver import resolve_pending_predictions
from mentor.config import Settings
from mentor.domain.errors import DomainError
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.scheduler")


@dataclass(frozen=True, slots=True)
class CycleResult:
    predicted: bool
    prediction_id: str | None
    resolved: int
    note: str


class LoopScheduler:
    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._settings = settings
        self._sessions = session_factory
        self._scheduler = AsyncIOScheduler(timezone="UTC")

    # ---- champion resolution ----

    def _champion_model(self) -> str:
        # Reading the champion pointer needs no DB session.
        promo = PromotionService(model_store_dir=self._settings.model_store_dir)
        champion = promo.current_champion()
        if champion and isinstance(champion.get("model_name"), str):
            return str(champion["model_name"])
        return "baseline"

    # ---- job bodies (also callable on demand) ----

    async def run_predict_once(self) -> str | None:
        s = self._settings
        async with self._sessions() as session:
            try:
                service = ForecastService(
                    prices=PriceBarRepository(session),
                    predictions=PredictionRepository(session),
                    model_store_dir=s.model_store_dir,
                )
                payload = await service.predict(
                    symbol=s.loop_symbol,
                    timeframe=Timeframe(s.loop_timeframe),
                    model_name=self._champion_model(),
                    horizon_bars=s.loop_horizon_bars,
                    record=True,
                )
                await session.commit()
                log.info("loop.predicted", id=str(payload.prediction_id))
                return str(payload.prediction_id)
            except DomainError as exc:
                await session.rollback()
                log.warning("loop.predict_skipped", error=str(exc))
                return None

    async def run_resolve_once(self) -> int:
        async with self._sessions() as session:
            result = await resolve_pending_predictions(
                predictions=PredictionRepository(session),
                prices=PriceBarRepository(session),
            )
            await session.commit()
            return result.resolved

    async def run_retrain_once(self) -> str:
        s = self._settings
        async with self._sessions() as session:
            try:
                promo = PromotionService(
                    prices=PriceBarRepository(session),
                    model_store_dir=s.model_store_dir,
                )
                result = await promo.retrain_and_promote(
                    symbol=s.loop_symbol,
                    timeframe=Timeframe(s.loop_timeframe),
                    horizon_bars=s.loop_horizon_bars,
                )
                await session.commit()
                return result.reason
            except DomainError as exc:
                await session.rollback()
                log.warning("loop.retrain_skipped", error=str(exc))
                return f"skipped: {exc}"

    async def run_cycle_once(self) -> CycleResult:
        """One predict + resolve cycle — what the API's run-once endpoint calls."""
        prediction_id = await self.run_predict_once()
        resolved = await self.run_resolve_once()
        return CycleResult(
            predicted=prediction_id is not None,
            prediction_id=prediction_id,
            resolved=resolved,
            note="live predictions resolve once their horizon bar prints",
        )

    # ---- lifecycle ----

    def start(self) -> None:
        if not self._settings.loop_enabled:
            log.info("loop.disabled")
            return
        s = self._settings
        self._scheduler.add_job(
            self.run_predict_once,
            "interval",
            minutes=s.loop_predict_interval_minutes,
            id="predict",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self.run_resolve_once,
            "interval",
            minutes=s.loop_resolve_interval_minutes,
            id="resolve",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self.run_retrain_once,
            "interval",
            hours=s.loop_retrain_interval_hours,
            id="retrain",
            replace_existing=True,
        )
        self._scheduler.start()
        log.info(
            "loop.started",
            predict_min=s.loop_predict_interval_minutes,
            resolve_min=s.loop_resolve_interval_minutes,
            retrain_hr=s.loop_retrain_interval_hours,
        )

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    @property
    def running(self) -> bool:
        return bool(self._scheduler.running)

    def status(self) -> dict[str, object]:
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                }
            )
        return {
            "enabled": self._settings.loop_enabled,
            "running": self.running,
            "symbol": self._settings.loop_symbol,
            "timeframe": self._settings.loop_timeframe,
            "horizon_bars": self._settings.loop_horizon_bars,
            "champion": self._champion_model(),
            "jobs": jobs,
        }
