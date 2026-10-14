"""LoopScheduler job wiring tests.

These verify the scheduler registers the full set of jobs (including the
newly-added ingest job that keeps data fresh) at the configured cadence, and
that it stays dormant when the loop is disabled. No DB or network is touched —
we only inspect the registered APScheduler jobs.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from mentor.application.scheduler.service import LoopScheduler, _next_boundary
from mentor.config import Settings
from mentor.infrastructure.locks import try_exclusive


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
        assert {"ingest", "predict", "resolve", "retrain"} <= job_ids
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


def test_next_boundary_is_just_after_the_next_bar_closes() -> None:
    hour = timedelta(hours=1)
    at = datetime(2026, 10, 13, 17, 41, tzinfo=UTC)
    assert _next_boundary(at, hour) == datetime(2026, 10, 13, 18, 2, tzinfo=UTC)
    # Exactly on the run time: the next one, never the same instant twice.
    on = datetime(2026, 10, 13, 18, 2, tzinfo=UTC)
    assert _next_boundary(on, hour) == datetime(2026, 10, 13, 19, 2, tzinfo=UTC)
    # In the grace minutes the bar that just closed is still ahead.
    early = datetime(2026, 10, 13, 18, 0, 30, tzinfo=UTC)
    assert _next_boundary(early, hour) == datetime(2026, 10, 13, 18, 2, tzinfo=UTC)
    # Daily: two minutes past UTC midnight.
    assert _next_boundary(at, timedelta(days=1)) == datetime(2026, 10, 14, 0, 2, tzinfo=UTC)


async def test_ingest_runs_just_after_bar_boundaries_plus_once_at_startup() -> None:
    """Only settled bars are stored, so ingest must not keep the boot minute.

    An interval started at boot (17:41, say) would leave each hour's bar
    unstored for 41 minutes after it closed.
    """
    scheduler = _scheduler(enabled=True)
    try:
        scheduler.start()
        ingest = scheduler._scheduler.get_job("ingest")
        assert ingest is not None
        first = ingest.next_run_time.astimezone(UTC)
        assert first.minute in (2, 32) and first.second == 0  # 30-minute cadence
        assert scheduler._scheduler.get_job("ingest_startup") is not None
        d1 = scheduler._scheduler.get_job("ingest_d1")
        assert d1 is not None
        assert d1.next_run_time.astimezone(UTC).time() == time(0, 2)
    finally:
        scheduler.shutdown()


async def test_a_lane_already_retraining_is_not_retrained_twice(tmp_path: Path) -> None:
    """The weekly slot, a drift trigger and the operator's CLI share one store."""
    settings = Settings(loop_enabled=False, db_password="x", model_store_dir=str(tmp_path))
    sessions = MagicMock(side_effect=AssertionError("must not open a session"))
    scheduler = LoopScheduler(settings=settings, session_factory=sessions)
    with try_exclusive(tmp_path / ".retrain.lock") as held:
        assert held
        result = await scheduler.run_retrain_once()
    assert result.startswith("skipped: another retrain")
