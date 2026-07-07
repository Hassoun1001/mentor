"""LoopScheduler job wiring tests.

These verify the scheduler registers the full set of jobs (including the
newly-added ingest job that keeps data fresh) at the configured cadence, and
that it stays dormant when the loop is disabled. No DB or network is touched —
we only inspect the registered APScheduler jobs.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from mentor.application.scheduler.service import LoopScheduler
from mentor.config import Settings


def _scheduler(*, enabled: bool) -> LoopScheduler:
    settings = Settings(
        loop_enabled=enabled,
        loop_ingest_interval_minutes=30,
        loop_predict_interval_minutes=45,
        db_password="x",
    )
    return LoopScheduler(settings=settings, session_factory=MagicMock())


async def test_start_registers_all_jobs_including_ingest() -> None:
    scheduler = _scheduler(enabled=True)
    try:
        scheduler.start()
        job_ids = {job["id"] for job in scheduler.status()["jobs"]}  # type: ignore[union-attr]
        assert job_ids == {"ingest", "predict", "resolve", "retrain"}
    finally:
        scheduler.shutdown()


async def test_ingest_job_uses_configured_interval() -> None:
    scheduler = _scheduler(enabled=True)
    try:
        scheduler.start()
        ingest = scheduler._scheduler.get_job("ingest")
        assert ingest is not None
        # interval trigger stores the period as a timedelta
        assert ingest.trigger.interval.total_seconds() == 30 * 60
    finally:
        scheduler.shutdown()


def test_disabled_loop_registers_no_jobs() -> None:
    scheduler = _scheduler(enabled=False)
    scheduler.start()
    assert scheduler.status()["jobs"] == []
    assert scheduler.running is False
