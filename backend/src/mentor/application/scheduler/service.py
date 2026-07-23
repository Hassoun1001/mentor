"""In-process scheduler for the autonomous prediction loop.

Runs four jobs on a cadence, each in its own DB transaction:

- **ingest** — pull fresh price bars for the loop symbol so every later
  step works on current data (idempotent upsert; overlap fills gaps).
- **predict** — generate a live forecast from the latest bars and log it
  to the audit table (champion model if one has been promoted, else the
  baseline rule). Guarded by the **data-quality gate**: a broken window
  (intraweek feed hole, stale feed) skips the prediction loudly instead
  of forecasting on garbage.
- **resolve** — fill the realised outcome of any prediction whose horizon
  has elapsed and whose outcome bar now exists. After each resolve pass
  the **drift watch** grades the rolling live Brier and triggers an
  early retrain when calibration has degraded (see `drift.py`).
- **retrain** — train a challenger *family* (technical / +macro / +news)
  and promote the best only if it beats the champion re-graded on the
  same fresh out-of-sample window.

Every job reports a heartbeat to `LoopHealth` and notable moments
(drift, promotions, quality skips, feed failures, strong signals) are
recorded as events and — when Telegram is configured — pushed to the
user's phone. Observability is not optional for a system that runs
unattended.

The scheduler is opt-in (`MENTOR_LOOP_ENABLED`). The same job bodies are
exposed as `run_*_once` so the API can trigger a single cycle on demand —
useful for testing without waiting for the next tick.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mentor.application.forecasting.inference_service import ForecastService
from mentor.application.forecasting.promotion import PromotionService
from mentor.application.forecasting.resolver import resolve_pending_predictions
from mentor.application.market import IngestionService
from mentor.application.market.quality import scan_quality
from mentor.application.news.tone_ingest import ToneIngestService
from mentor.application.scheduler.drift import assess_drift, select_independent
from mentor.application.scheduler.health import LoopHealth
from mentor.application.scheduler.quality_gate import assess_quality
from mentor.config import Settings
from mentor.domain.errors import DomainError
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.adapters import FailoverMarketDataAdapter
from mentor.infrastructure.adapters.factory import build_sources, close_sources
from mentor.infrastructure.alerts import build_notifier
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.infrastructure.repositories.news_tone import NewsToneRepository
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.scheduler")

# GDELT publishes daily; refreshing every 6 hours keeps the latest day
# current without hammering a free service. The lookback re-fetches a
# fortnight each time so revised days and any missed window self-heal.
_TONE_REFRESH_HOURS = 6
_TONE_REFRESH_DAYS = 14

# APScheduler interval jobs first fire one whole interval AFTER registration,
# so a restart silently reset every clock: no ingest or predict for an hour,
# no daily lane for 24 hours, no news sentiment for 6. Deploy a few times in
# a day and the loop does almost nothing while looking perfectly healthy —
# which is exactly what happened, and why the trade plan was serving a price
# over two hours old.
#
# Data-refresh jobs therefore get a kick shortly after boot. The delay lets
# the app finish starting before work begins. Retraining is deliberately NOT
# in this set: it costs about an hour of CPU, and running it on every deploy
# would be far worse than waiting for its weekly slot.
_STARTUP_DELAY_SECONDS = 45


def _soon(seconds: int = _STARTUP_DELAY_SECONDS) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=seconds)


# An overdue retrain still waits this long after boot: it costs about an
# hour of CPU, and a container that crash-loops must not spend every restart
# retraining instead of serving.
_OVERDUE_RETRAIN_DELAY = timedelta(minutes=10)

# How much history to (idempotently) pull each ingest tick, per timeframe.
_INGEST_DAYS: dict[Timeframe, int] = {
    Timeframe.M1: 3,
    Timeframe.M5: 7,
    Timeframe.H1: 10,
    Timeframe.D1: 60,
}

# How many recent bars the pre-prediction quality scan examines.
_QUALITY_WINDOW_BARS = 72


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
        self._health = LoopHealth()
        self._notifier = build_notifier(settings)
        # Cooldown marker so a rough patch can't trigger a retrain storm.
        self._last_drift_retrain: datetime | None = None
        # Consecutive ingest failures — alert once when the streak crosses
        # the threshold, reset on the next success.
        self._ingest_failures = 0

    # ---- champion resolution ----

    def _lane_store(self, lane: str) -> str:
        """Model-store directory for a lane: H1 keeps the root (backwards
        compatible with the live volume); D1 lives in a `d1/` substore with
        its own champion, promotions, and lessons."""
        root = self._settings.model_store_dir
        return root if lane == "h1" else str(Path(root) / lane)

    def _champion_model(self, lane: str = "h1") -> str:
        # Reading the champion pointer needs no DB session.
        promo = PromotionService(model_store_dir=self._lane_store(lane))
        champion = promo.current_champion()
        if champion and isinstance(champion.get("model_name"), str):
            return str(champion["model_name"])
        return "baseline"

    async def _alert(self, text: str) -> None:
        if await self._notifier.send(text):
            self._health.event("alert", text)

    # ---- job bodies (also callable on demand) ----

    async def _ingest_lane(self, *, tf: Timeframe, job: str) -> int:
        """Pull fresh bars for one lane's timeframe.

        Idempotent: the repository upserts on (symbol, timeframe, ts), so an
        overlapping window each tick just fills any gap without duplicating.
        """
        s = self._settings
        end = datetime.now(UTC)
        start = end - timedelta(days=_INGEST_DAYS.get(tf, 10))
        sources = build_sources(s)
        if not sources:
            log.warning("loop.ingest_skipped", job=job, error="no sources configured")
            self._health.beat(job, ok=False, note="no market data sources configured")
            return 0
        adapter = FailoverMarketDataAdapter(sources)
        try:
            async with self._sessions() as session:
                service = IngestionService(
                    adapter=adapter,
                    repo=PriceBarRepository(session),
                )
                result = await service.ingest(
                    symbol=s.loop_symbol,
                    timeframe=tf,
                    start=start,
                    end=end,
                )
                await session.commit()
            log.info("loop.ingested", job=job, persisted=result.persisted)
            self._health.beat(
                job, ok=True, note=f"{result.persisted} new bars ({result.fetched} fetched)"
            )
            self._ingest_failures = 0
            return result.persisted
        except DomainError as exc:
            log.warning("loop.ingest_skipped", job=job, error=str(exc))
            self._health.beat(job, ok=False, note=str(exc))
            self._ingest_failures += 1
            if self._ingest_failures == s.loop_ingest_failure_alert_after:
                detail = f"ingest failed {self._ingest_failures}x in a row: {exc}"
                self._health.event("ingest_error", detail)
                await self._alert(f"⚠️ Mentor: data feed problem — {detail}")
            return 0
        finally:
            await close_sources(sources)

    async def run_ingest_once(self) -> int:
        return await self._ingest_lane(tf=Timeframe(self._settings.loop_timeframe), job="ingest")

    async def run_ingest_d1_once(self) -> int:
        return await self._ingest_lane(tf=Timeframe.D1, job="ingest_d1")

    async def run_news_tone_once(self) -> int:
        """Refresh GDELT daily news sentiment.

        This feeds the model's news features. It is free and needs no API
        key, but nothing was scheduled to run it — so production had a
        healthy backfill that quietly went stale, and every prediction since
        was reading week-old sentiment as if it were current. A failure here
        must never take the loop down: stale tone is a degraded feature, not
        an outage.
        """
        s = self._settings
        try:
            async with self._sessions() as session:
                repo = NewsToneRepository(session)
                # GDELT publishes one point per day and rate-limits hard. The
                # startup kick means every deploy would otherwise re-fetch a
                # fortnight — eight deploys in an afternoon earned a 429, which
                # is exactly what happened. Skip when the stored series is
                # already current; the data cannot have changed.
                existing = await repo.series(query_key=s.news_query_key)
                if existing:
                    newest = max(row.day for row in existing)
                    if newest.date() >= (datetime.now(UTC) - timedelta(days=1)).date():
                        self._health.beat(
                            "news_tone",
                            ok=True,
                            note=f"already current to {newest.date()} — skipped",
                        )
                        return 0

                service = ToneIngestService(
                    repo=repo,
                    query=s.news_query,
                    query_key=s.news_query_key,
                )
                result = await service.backfill(
                    start=datetime.now(UTC) - timedelta(days=_TONE_REFRESH_DAYS),
                    end=datetime.now(UTC),
                )
                await session.commit()
            self._health.beat(
                "news_tone", ok=True, note=f"{result.rows_written} day(s) refreshed"
            )
            return result.rows_written
        except (DomainError, OSError) as exc:
            log.warning("loop.news_tone_failed", error=str(exc))
            self._health.event("news_tone_error", f"news sentiment refresh failed: {exc}")
            return 0

    async def _quality_check(self, tf: Timeframe) -> tuple[bool, str]:
        """Scan the recent bar window; False means 'do not predict on this'."""
        s = self._settings
        now = datetime.now(UTC)
        async with self._sessions() as session:
            repo = PriceBarRepository(session)
            newest = await repo.latest(symbol=s.loop_symbol, timeframe=tf)
            if newest is None:
                return False, "no bars stored yet — backfill first"
            window_start = newest.ts - timedelta(seconds=tf.seconds * _QUALITY_WINDOW_BARS)
            rows = await repo.range(
                symbol=s.loop_symbol, timeframe=tf, start=window_start, end=newest.ts
            )
        report = scan_quality(symbol=s.loop_symbol, timeframe=tf, bars=rows)
        verdict = assess_quality(report, now=now)
        return verdict.predict_ok, verdict.reason

    async def _predict_lane(
        self, *, tf: Timeframe, horizon_bars: int, lane: str, job: str
    ) -> str | None:
        s = self._settings

        predict_ok, quality_reason = await self._quality_check(tf)
        if not predict_ok:
            log.warning("loop.predict_quality_skip", job=job, reason=quality_reason)
            self._health.beat(job, ok=False, note=f"quality gate: {quality_reason}")
            self._health.event("quality_skip", f"[{lane}] {quality_reason}")
            return None

        async with self._sessions() as session:
            try:
                service = ForecastService(
                    prices=PriceBarRepository(session),
                    predictions=PredictionRepository(session),
                    model_store_dir=self._lane_store(lane),
                    # A promoted +macro/+news champion needs these at inference
                    # time — without them its exogenous columns are silently
                    # zeroed and the model predicts half-blind.
                    news_tone=NewsToneRepository(session),
                    news_query_key=s.news_query_key,
                    macro=MacroSeriesRepository(session),
                )
                payload = await service.predict(
                    symbol=s.loop_symbol,
                    timeframe=tf,
                    model_name=self._champion_model(lane),
                    horizon_bars=horizon_bars,
                    record=True,
                )
                await session.commit()
            except DomainError as exc:
                await session.rollback()
                log.warning("loop.predict_skipped", job=job, error=str(exc))
                self._health.beat(job, ok=False, note=str(exc))
                return None

        f = payload.forecast
        log.info("loop.predicted", job=job, id=str(payload.prediction_id))
        self._health.beat(
            job,
            ok=True,
            note=f"{f.direction.value} P(up)={float(f.p_up):.2f} h={f.horizon_bars}",
        )
        if float(f.confidence) >= s.loop_alert_min_confidence:
            await self._alert(
                f"📈 Mentor signal: {f.symbol} {f.direction.value.upper()} — "
                f"P(up) {float(f.p_up) * 100:.0f}% over the next {f.horizon_bars} bars "
                f"({tf.value}). Not advice; check the dashboard."
            )
        return str(payload.prediction_id)

    async def run_predict_once(self) -> str | None:
        s = self._settings
        return await self._predict_lane(
            tf=Timeframe(s.loop_timeframe),
            horizon_bars=s.loop_horizon_bars,
            lane="h1",
            job="predict",
        )

    async def run_predict_d1_once(self) -> str | None:
        s = self._settings
        return await self._predict_lane(
            tf=Timeframe.D1,
            horizon_bars=s.loop_d1_horizon_bars,
            lane="d1",
            job="predict_d1",
        )

    async def run_resolve_once(self) -> int:
        async with self._sessions() as session:
            result = await resolve_pending_predictions(
                predictions=PredictionRepository(session),
                prices=PriceBarRepository(session),
            )
            await session.commit()
        self._health.beat(
            "resolve",
            ok=True,
            note=f"{result.resolved} resolved, {result.still_pending} still pending",
        )
        if result.resolved:
            # Fresh outcomes just landed — the moment to check whether the
            # system's own live performance says the regime has drifted.
            await self._maybe_retrain_on_drift()
        return result.resolved

    async def _maybe_retrain_on_drift(self) -> None:
        """Learn from live outcomes: retrain early when calibration degrades."""
        s = self._settings
        now = datetime.now(UTC)
        if self._last_drift_retrain is not None and now - self._last_drift_retrain < timedelta(
            hours=s.loop_drift_cooldown_hours
        ):
            return

        promo = PromotionService(model_store_dir=s.model_store_dir)
        champion = promo.current_champion()
        champion_brier = (
            float(champion["test_brier"])  # type: ignore[arg-type]
            if champion and champion.get("test_brier") is not None
            else None
        )
        # Hourly predictions overlap 23/24 of their outcome windows — fetch a
        # wide raw window, then reduce to non-overlapping calls so the drift
        # thresholds count *independent* observations, not autocorrelated
        # copies of the same market day.
        fetch_limit = min(2000, s.loop_drift_window * s.loop_horizon_bars)
        async with self._sessions() as session:
            rows = await PredictionRepository(session).list_resolved(limit=fetch_limit)
        # The drift watch grades the H1 lane only — mixing lanes would blur
        # whose calibration actually drifted. (The D1 lane accumulates
        # independent outcomes too slowly for a drift signal; its weekly
        # retrain is its adaptation path.)
        calls = [
            (r.asof, r.horizon_at, float(r.p_up), int(r.realised_outcome or 0))
            for r in rows
            if r.timeframe == s.loop_timeframe
        ]
        outcomes = select_independent(calls)[: s.loop_drift_window]

        verdict = assess_drift(
            outcomes,
            champion_brier=champion_brier,
            min_samples=s.loop_drift_min_samples,
            margin=s.loop_drift_margin,
        )
        if not verdict.retrain:
            log.debug("loop.drift_ok", reason=verdict.reason)
            return
        log.warning("loop.drift_detected", reason=verdict.reason, live_brier=verdict.live_brier)
        self._health.event("drift_detected", verdict.reason)
        await self._alert(f"🔄 Mentor: {verdict.reason}. Retraining now.")
        self._last_drift_retrain = now
        reason = await self.run_retrain_once()
        log.info("loop.drift_retrain_done", outcome=reason)

    async def _retrain_lane(
        self, *, tf: Timeframe, horizon_bars: int, lane: str, job: str
    ) -> str:
        s = self._settings
        async with self._sessions() as session:
            try:
                promo = PromotionService(
                    prices=PriceBarRepository(session),
                    model_store_dir=self._lane_store(lane),
                    # Exogenous stores unlock the +macro / +news challenger
                    # configurations whenever their data is present; the
                    # predictions repo lets each retrain record the live
                    # post-mortem in its lesson.
                    news_tone=NewsToneRepository(session),
                    macro=MacroSeriesRepository(session),
                    news_query_key=s.news_query_key,
                    predictions=PredictionRepository(session),
                )
                result = await promo.retrain_and_promote(
                    symbol=s.loop_symbol,
                    timeframe=tf,
                    horizon_bars=horizon_bars,
                    max_bars=s.loop_train_max_bars,
                )
                await session.commit()
            except DomainError as exc:
                await session.rollback()
                log.warning("loop.retrain_skipped", job=job, error=str(exc))
                self._health.beat(job, ok=False, note=str(exc))
                return f"skipped: {exc}"

        self._health.beat(job, ok=True, note=result.reason)
        if result.promoted:
            self._health.event("promotion", f"[{lane}] {result.reason}")
            await self._alert(
                f"🏆 Mentor: new {lane.upper()} champion promoted. {result.reason}"
            )
        if result.demoted:
            self._health.event("demotion", f"[{lane}] {result.reason}")
        return result.reason

    def _next_retrain_time(self, lane: str) -> datetime:
        """When retraining should next happen, measured from the last one.

        Interval jobs count from registration, so a weekly retrain on a
        system that is deployed weekly never fires at all — every deploy
        pushes it another seven days out. Excluding retrain from the startup
        kick (it costs an hour of CPU) would have left exactly that hole, so
        the cadence is anchored to the durable promotions log instead: the
        last decision actually recorded, plus the interval.

        A retrain that is already overdue runs shortly after boot rather
        than immediately, so a crash-looping container cannot burn every
        restart on training.
        """
        interval = timedelta(hours=self._settings.loop_retrain_interval_hours)
        store = self._lane_store(lane)
        try:
            history = PromotionService(model_store_dir=str(store)).promotion_history(limit=1)
        except (OSError, ValueError):  # pragma: no cover - unreadable log
            history = []

        last: datetime | None = None
        if history:
            raw = history[0].get("at")
            if isinstance(raw, str):
                try:
                    last = datetime.fromisoformat(raw)
                except ValueError:
                    last = None

        earliest = datetime.now(UTC) + _OVERDUE_RETRAIN_DELAY
        if last is None:
            # Never retrained: do it soon, but not before the app is warm.
            return earliest
        return max(last + interval, earliest)

    async def run_retrain_once(self) -> str:
        s = self._settings
        return await self._retrain_lane(
            tf=Timeframe(s.loop_timeframe),
            horizon_bars=s.loop_horizon_bars,
            lane="h1",
            job="retrain",
        )

    async def run_retrain_d1_once(self) -> str:
        s = self._settings
        return await self._retrain_lane(
            tf=Timeframe.D1,
            horizon_bars=s.loop_d1_horizon_bars,
            lane="d1",
            job="retrain_d1",
        )

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
            self.run_news_tone_once,
            "interval",
            hours=_TONE_REFRESH_HOURS,
            id="news_tone",
            next_run_time=_soon(),
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.add_job(
            self.run_ingest_once,
            "interval",
            minutes=s.loop_ingest_interval_minutes,
            id="ingest",
            next_run_time=_soon(),
            replace_existing=True,
        )
        self._scheduler.add_job(
            self.run_predict_once,
            "interval",
            minutes=s.loop_predict_interval_minutes,
            id="predict",
            next_run_time=_soon(),
            replace_existing=True,
        )
        self._scheduler.add_job(
            self.run_resolve_once,
            "interval",
            minutes=s.loop_resolve_interval_minutes,
            id="resolve",
            next_run_time=_soon(),
            replace_existing=True,
        )
        self._scheduler.add_job(
            self.run_retrain_once,
            "interval",
            hours=s.loop_retrain_interval_hours,
            id="retrain",
            next_run_time=self._next_retrain_time("h1"),
            replace_existing=True,
        )
        if s.loop_d1_enabled:
            # The D1 flagship lane: same machinery, ten years of daily data.
            self._scheduler.add_job(
                self.run_ingest_d1_once,
                "interval",
                hours=s.loop_d1_ingest_interval_hours,
                id="ingest_d1",
                next_run_time=_soon(),
                replace_existing=True,
            )
            self._scheduler.add_job(
                self.run_predict_d1_once,
                "interval",
                hours=s.loop_d1_predict_interval_hours,
                id="predict_d1",
                next_run_time=_soon(),
                replace_existing=True,
            )
            self._scheduler.add_job(
                self.run_retrain_d1_once,
                "interval",
                hours=s.loop_d1_retrain_interval_hours,
                id="retrain_d1",
                next_run_time=self._next_retrain_time("d1"),
                replace_existing=True,
            )
        self._scheduler.start()
        log.info(
            "loop.started",
            ingest_min=s.loop_ingest_interval_minutes,
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
        heartbeats, events = self._health.snapshot()
        return {
            "enabled": self._settings.loop_enabled,
            "running": self.running,
            "symbol": self._settings.loop_symbol,
            "timeframe": self._settings.loop_timeframe,
            "horizon_bars": self._settings.loop_horizon_bars,
            "champion": self._champion_model(),
            "champion_d1": self._champion_model("d1"),
            "jobs": jobs,
            "heartbeats": heartbeats,
            "events": events,
            "alerts_enabled": self._notifier.enabled,
        }
