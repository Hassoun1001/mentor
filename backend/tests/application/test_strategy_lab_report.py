"""The strategy lab in the weekly self-report, and its scheduler jobs."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from mentor.application.health.self_report import SelfReport
from mentor.application.scheduler.service import LoopScheduler
from mentor.application.strategy_lab.summary import CandidateView, LabView, PaperRecord
from mentor.config import Settings
from tests.application.test_self_report import NOW, _report


def _paper(last_bar_hours_ago: float) -> PaperRecord:
    return PaperRecord(
        trades=12,
        mean_r=0.1,
        win_rate=0.5,
        breakeven_win_rate=0.45,
        ci_low=-0.3,
        ci_high=0.5,
        verdict="v",
        next_check_at=30,
        open_position=None,
        pending_order=None,
        last_bar_ts=(NOW - timedelta(hours=last_bar_hours_ago)).isoformat(),
    )


def _candidate(key: str, status: str, paper: PaperRecord | None = None) -> CandidateView:
    return CandidateView(
        key=key,
        title=key.replace("_", " "),
        family="f",
        timeframe="1h",
        hypothesis="h",
        status=status,
        status_reason="r",
        evaluated_at=NOW.isoformat(),
        n_trials_at_evaluation=74,
        plan=None,
        evidence={
            "score": 1.2,
            "bar": 4.4,
            "out_of_sample": {"n": 120, "mean_r": 0.05},
            "holdout": {"n": 40, "mean_r": -0.02},
        },
        clears_todays_bar=False,
        paper_started_at=None,
        promoted_at=None,
        demoted_at=None,
        retired_at=None,
        paper=paper,
    )


def _lab(**over: object) -> LabView:
    base: dict[str, object] = {
        "trials_ever": 74,
        "dispersion": 1.0,
        "bar_now": 4.38,
        "paper_account": "10,000 USD",
        "candidates": (_candidate("range_fade", "rejected"),),
        "waiting": (),
        "changed": (),
        "events_week": (),
    }
    base.update(over)
    return LabView(**base)  # type: ignore[arg-type]


def _codes(report: SelfReport) -> set[str]:
    return {i.code for i in report.issues}


def test_a_quiet_lab_adds_a_section_and_no_issues() -> None:
    r = _report(lab=_lab())
    assert r.status == "ok" and r.strategies is not None
    assert r.strategies["trials_ever"] == 74
    (c,) = r.strategies["candidates"]  # type: ignore[misc]
    assert c["status"] == "rejected" and c["oos_trades"] == 120
    assert "🧪 Trading ideas: 1 idea tested so far, none good enough yet." in r.telegram_text()


def test_no_lab_no_section() -> None:
    r = _report()
    assert r.strategies is None and "Trading ideas" not in r.telegram_text()


def test_lab_problems_have_stable_codes() -> None:
    lab = _lab(
        waiting=("new_idea",),
        changed=("edited_idea",),
        candidates=(
            _candidate("stale", "paper", _paper(last_bar_hours_ago=100)),
            _candidate("fresh", "paper", _paper(last_bar_hours_ago=2)),
        ),
        events_week=(
            {"key": "x", "kind": "demoted", "at": NOW.isoformat(), "detail": "Demoted: ..."},
            {"key": "y", "kind": "retired", "at": NOW.isoformat(), "detail": "Retired: ..."},
        ),
    )
    codes = _codes(_report(lab=lab))
    assert {
        "strategies.waiting",
        "strategies.definition_changed",
        "strategy.stale.paper_stalled",
        "strategy.x.demoted",
        "strategy.y.retired",
    } <= codes
    assert "strategy.fresh.paper_stalled" not in codes


def test_good_news_is_a_note_not_an_issue() -> None:
    lab = _lab(
        events_week=(
            {"key": "z", "kind": "promoted", "at": NOW.isoformat(), "detail": "Recommended: ..."},
            {"key": "w", "kind": "rejected", "at": NOW.isoformat(), "detail": "..."},
        )
    )
    r = _report(lab=lab)
    assert r.status == "ok"
    assert any("z is now recommended" in n for n in r.notes)
    assert any("w was tested and rejected" in n for n in r.notes)


def test_an_unreadable_lab_is_reported_not_fatal() -> None:
    r = _report(lab_error="could not be read (ProgrammingError)")
    assert "strategies.unavailable" in _codes(r)
    assert r.strategies is None


def _scheduler(**over: object) -> LoopScheduler:
    settings = Settings(loop_enabled=True, db_password="x", **over)  # type: ignore[arg-type]
    return LoopScheduler(settings=settings, session_factory=MagicMock())


async def test_lab_jobs_are_registered() -> None:
    scheduler = _scheduler()
    try:
        scheduler.start()
        lab = scheduler._scheduler.get_job("strategy_lab")
        paper = scheduler._scheduler.get_job("strategy_paper")
        assert lab is not None and paper is not None
        assert paper.trigger.interval.total_seconds() == 60 * 60
    finally:
        scheduler.shutdown()


async def test_lab_jobs_can_be_switched_off() -> None:
    scheduler = _scheduler(strategy_lab_enabled=False)
    try:
        scheduler.start()
        ids = {j["id"] for j in scheduler.status()["jobs"]}  # type: ignore[union-attr]
        assert not {"strategy_lab", "strategy_paper"} & ids
    finally:
        scheduler.shutdown()
