"""The self-report must name real problems, stay quiet about non-problems,
and keep a trend across restarts."""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import mentor.logging as mentor_logging
from mentor.application.health import Check, Digest, Level
from mentor.application.health.self_report import (
    LaneInputs,
    ReportStore,
    SelfReport,
    assemble_report,
)
from mentor.logging import LogTally, TallyingFilter, _tally_event

NOW = datetime(2026, 10, 17, 6, 0, tzinfo=UTC)


def _digest(*levels: Level) -> Digest:
    checks = tuple(
        Check(key=f"c{i}", label=f"Check {i}", level=lv, detail=f"detail {i}")
        for i, lv in enumerate(levels or (Level.OK,))
    )
    return Digest(generated_at=NOW, window_days=7, checks=checks, headline="h", evidence="e")


_BASE_LANE = LaneInputs(
    lane="h1",
    label="24-hour lane",
    timeframe="1h",
    champion_name="auto_m",
    champion_promoted_at=NOW - timedelta(days=11),
    floor_failures=0,
    independent_windows=78,
    hits=42,
    breakeven=0.5178,
    breakeven_measured=True,
    brier_week=0.234,
    calls_week=96,
    brier_prev_week=0.244,
    calls_prev_week=110,
    champion_calls_week=96,
    decisions_week=(),
    last_decision_at=NOW - timedelta(days=1),
    retrain_interval_hours=168,
    calibration=None,
    calibration_progress=6,
)


def _lane(**over: object) -> LaneInputs:
    return replace(_BASE_LANE, **over)  # type: ignore[arg-type]


def _report(**over: object) -> SelfReport:
    kwargs: dict[str, object] = {
        "now": NOW,
        "digest": _digest(),
        "lanes": [_lane()],
        "heartbeats": [{"job": "ingest", "at": NOW.isoformat(), "ok": True, "note": "ok"}],
        "tally": {"since": NOW.isoformat(), "events": []},
    }
    kwargs.update(over)
    return assemble_report(**kwargs)  # type: ignore[arg-type]


def _codes(report: SelfReport) -> set[str]:
    return {i.code for i in report.issues}


# ---------- quiet when there is nothing to say ----------


def test_a_healthy_week_reports_ok_with_no_issues() -> None:
    r = _report()
    assert r.status == "ok"
    assert r.issues == ()
    assert "nothing needs attention" in r.headline
    lane = r.lanes[0]
    assert lane.win_rate == pytest.approx(42 / 78)
    assert not lane.significant  # 53.8% over 78 does not clear a 51.8% hurdle


def test_a_handful_of_warnings_is_not_called_recurring() -> None:
    tally = {
        "since": "x",
        "events": [{"level": "warning", "event": "gdelt.rate_limited", "count": 3}],
    }
    assert _report(tally=tally).issues == ()


# ---------- names what is wrong ----------


def test_a_failed_health_check_makes_the_report_fail() -> None:
    r = _report(digest=_digest(Level.OK, Level.FAIL))
    assert r.status == "fail"
    assert "digest.c1" in _codes(r)


def test_a_failing_job_is_named() -> None:
    beats = [{"job": "news_tone", "at": NOW.isoformat(), "ok": False, "note": "GDELT down"}]
    r = _report(heartbeats=beats)
    assert "job.news_tone" in _codes(r)
    assert r.failing_jobs[0]["note"] == "GDELT down"


def test_a_record_proven_below_breakeven_is_flagged() -> None:
    r = _report(lanes=[_lane(independent_windows=400, hits=160)])  # 40%, decisively short
    assert "h1.below_breakeven" in _codes(r)


def test_a_champion_failing_its_recheck_is_flagged_with_the_streak() -> None:
    r = _report(lanes=[_lane(floor_failures=2)])
    issue = next(i for i in r.issues if i.code == "h1.champion_failing")
    assert "2 retrain(s) in a row" in issue.detail
    assert "removed at 3" in issue.detail


def test_a_bad_calibration_week_needs_enough_calls_to_count() -> None:
    bad_and_busy = _report(lanes=[_lane(brier_week=0.29, calls_week=60)])
    bad_but_thin = _report(lanes=[_lane(brier_week=0.29, calls_week=5)])
    assert "h1.calibration_week" in _codes(bad_and_busy)
    assert "h1.calibration_week" not in _codes(bad_but_thin)


def test_a_secondary_lane_that_stopped_retraining_is_flagged() -> None:
    d1 = _lane(lane="d1", label="5-day lane", last_decision_at=NOW - timedelta(days=30))
    issue = next(i for i in _report(lanes=[d1]).issues if i.code == "d1.retrain_stalled")
    assert "30 days ago" in issue.detail


def test_the_primary_lane_retrain_cadence_is_left_to_the_digest() -> None:
    stale_h1 = _lane(last_decision_at=NOW - timedelta(days=30))
    assert "h1.retrain_stalled" not in _codes(_report(lanes=[stale_h1]))


def test_recurring_warnings_and_any_error_are_surfaced() -> None:
    tally = {
        "since": "x",
        "events": [
            {"level": "warning", "event": "gdelt.rate_limited", "count": 14},
            {"level": "error", "event": "ingest.crashed", "count": 1},
        ],
    }
    codes = _codes(_report(tally=tally))
    assert "log.warning.gdelt.rate_limited" in codes
    assert "log.error.ingest.crashed" in codes


def test_a_promotion_this_week_becomes_a_note_not_an_issue() -> None:
    decision: dict[str, object] = {
        "at": NOW.isoformat(),
        "promoted": True,
        "challenger": "auto_new",
    }
    r = _report(lanes=[_lane(decisions_week=(decision,))])
    assert r.issues == ()
    assert any("auto_new" in n for n in r.notes)
    assert r.lanes[0].promotions_week == 1


def test_calibration_progress_is_described_in_words() -> None:
    assert "6 of 30" in _report().lanes[0].calibration
    applied = {"model_name": "auto_m", "applied": True, "reason": "held-out Brier improved"}
    assert "Correcting" in _report(lanes=[_lane(calibration=applied)]).lanes[0].calibration


# ---------- the summary that reaches the phone ----------


def test_the_telegram_summary_carries_the_essentials() -> None:
    text = _report(lanes=[_lane(floor_failures=1)]).telegram_text(report_url="https://x/report")
    assert "WARN" in text
    assert "78 independent results" in text
    assert "needs 51.8%" in text
    assert "prediction error this week 0.234 (last week 0.244)" in text
    assert "Full report: https://x/report" in text
    assert len(text) < 4096  # Telegram's message limit


# ---------- persistence and trend ----------


def test_reports_persist_prune_and_summarise_as_history(tmp_path: Path) -> None:
    store = ReportStore(tmp_path)
    for weeks in range(30):
        store.write(_report(now=NOW - timedelta(days=7 * weeks)))
    files = sorted((tmp_path / "reports").glob("*.json"))
    assert len(files) == 26  # half a year kept, the rest pruned
    history = store.history(limit=3)
    dates = [str(h["date"]) for h in history]
    assert dates == sorted(dates, reverse=True)
    lanes = history[0]["lanes"]
    assert isinstance(lanes, list)
    assert lanes[0]["independent_windows"] == 78


def test_a_torn_report_file_does_not_break_history(tmp_path: Path) -> None:
    store = ReportStore(tmp_path)
    store.write(_report())
    (tmp_path / "reports" / "2026-01-01.json").write_text("{not json", encoding="utf-8")
    assert len(store.history()) == 1


def test_the_report_serialises_to_json() -> None:
    data = _report().to_dict()
    json.dumps(data)  # must not raise
    assert data["generated_at"] == NOW.isoformat()


# ---------- the recurring-warning tally ----------


@pytest.fixture
def fresh_tally(monkeypatch: pytest.MonkeyPatch) -> LogTally:
    tally = LogTally()
    monkeypatch.setattr(mentor_logging, "_TALLY", tally)
    return tally


def test_structlog_warnings_are_counted_and_info_is_not(fresh_tally: LogTally) -> None:
    _tally_event(None, "warning", {"level": "warning", "event": "gdelt.rate_limited"})
    _tally_event(None, "warning", {"level": "warning", "event": "gdelt.rate_limited"})
    _tally_event(None, "info", {"level": "info", "event": "loop.ingested"})
    assert fresh_tally.snapshot()["events"] == [
        {"level": "warning", "event": "gdelt.rate_limited", "count": 2}
    ]


def test_stdlib_warnings_are_keyed_by_template_not_by_argument(fresh_tally: LogTally) -> None:
    filt = TallyingFilter()
    for secs in (2, 3):
        record = logging.LogRecord(
            "apscheduler", logging.WARNING, __file__, 1, "job %s missed by %ss", ("x", secs), None
        )
        filt.filter(record)
    assert fresh_tally.snapshot()["events"] == [
        {"level": "warning", "event": "apscheduler: job %s missed by %ss", "count": 2}
    ]
