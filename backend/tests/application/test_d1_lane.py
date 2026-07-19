"""D1 lane: job registration and model-store isolation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from mentor.application.forecasting.promotion import PromotionService
from mentor.application.scheduler.service import LoopScheduler
from mentor.config import Settings


def _scheduler(*, d1: bool) -> LoopScheduler:
    settings = Settings(
        loop_enabled=True,
        loop_d1_enabled=d1,
        db_password="x",
    )
    return LoopScheduler(settings=settings, session_factory=MagicMock())


async def test_d1_jobs_registered_when_enabled() -> None:
    scheduler = _scheduler(d1=True)
    try:
        scheduler.start()
        job_ids = {job["id"] for job in scheduler.status()["jobs"]}  # type: ignore[union-attr]
        assert {"ingest", "predict", "resolve", "retrain"} <= job_ids
        assert {"ingest_d1", "predict_d1", "retrain_d1"} <= job_ids
    finally:
        scheduler.shutdown()


async def test_d1_jobs_absent_when_disabled() -> None:
    scheduler = _scheduler(d1=False)
    try:
        scheduler.start()
        job_ids = {job["id"] for job in scheduler.status()["jobs"]}  # type: ignore[union-attr]
        assert "ingest_d1" not in job_ids
        assert "predict_d1" not in job_ids
        assert "retrain_d1" not in job_ids
    finally:
        scheduler.shutdown()


def test_status_reports_both_lane_champions(tmp_path: Path) -> None:
    settings = Settings(
        loop_enabled=True, db_password="x", model_store_dir=str(tmp_path)
    )
    scheduler = LoopScheduler(settings=settings, session_factory=MagicMock())
    status = scheduler.status()
    assert status["champion"] == "baseline"
    assert status["champion_d1"] == "baseline"

    # Crown a D1 champion in the substore; the H1 lane must not see it.
    PromotionService(model_store_dir=tmp_path / "d1")._write_champion(
        name="daily_hero", brier=0.24, family="technical+macro"
    )
    status = scheduler.status()
    assert status["champion"] == "baseline"  # H1 root store untouched
    assert status["champion_d1"] == "daily_hero"


def test_lane_stores_are_isolated(tmp_path: Path) -> None:
    h1 = PromotionService(model_store_dir=tmp_path)
    d1 = PromotionService(model_store_dir=tmp_path / "d1")
    h1._write_champion(name="hourly", brier=0.246, family="technical")
    d1._write_champion(name="daily", brier=0.235, family="technical+macro")
    assert h1.current_champion()["model_name"] == "hourly"  # type: ignore[index]
    assert d1.current_champion()["model_name"] == "daily"  # type: ignore[index]
    # Logs are separate files too.
    assert not (tmp_path / "d1" / "promotions.jsonl").exists()
    assert (tmp_path / "d1" / "champion.json").exists()
    assert (tmp_path / "champion.json").exists()
