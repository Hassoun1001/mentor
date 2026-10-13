"""The digest must fail loudly and never let signal count look like evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from mentor.application.health import Level, build_digest
from mentor.application.health.collect import late_predictions, outcome_expected_by
from mentor.config import Settings
from mentor.domain.market.bars import Timeframe

NOW = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def _digest(**over: object):  # type: ignore[no-untyped-def]
    kwargs: dict[str, object] = {
        "window_days": 7,
        "newest_bar": NOW - timedelta(minutes=20),
        "ingest_interval_minutes": 60,
        "pending_predictions": 12,
        "overdue_predictions": 0,
        "last_retrain": NOW - timedelta(days=3),
        "retrain_interval_hours": 168,
        "alerts_enabled": True,
        "independent_windows": 40,
        "windows_needed": 30,
        "paper_verdict": "40 windows, 58% correct — the edge is real.",
        "now": NOW,
    }
    kwargs.update(over)
    return build_digest(**kwargs)  # type: ignore[arg-type]


# ---------- healthy ----------


def test_a_healthy_system_says_so_plainly() -> None:
    d = _digest()
    assert d.worst is Level.OK
    assert "Everything ran" in d.headline


# ---------- the failures that matter ----------


def test_a_dead_feed_is_a_failure_and_discredits_everything_else() -> None:
    d = _digest(newest_bar=NOW - timedelta(hours=9))
    feed = next(c for c in d.checks if c.key == "feed")
    assert feed.level is Level.FAIL
    assert d.worst is Level.FAIL
    # The headline must stop the reader trusting the numbers underneath.
    assert "describe the past" in d.headline


def test_lost_predictions_are_named_as_lost_record_not_a_queue() -> None:
    d = _digest(lost_predictions=14)
    check = next(c for c in d.checks if c.key == "resolution")
    assert check.level is Level.FAIL
    assert "permanently lost" in check.detail


def test_late_but_recoverable_predictions_warn_rather_than_fail() -> None:
    d = _digest(overdue_predictions=3)
    check = next(c for c in d.checks if c.key == "resolution")
    assert check.level is Level.WARN
    assert "recoverable" in check.detail


# ---- when a pending call is late (production false FAIL, 2026-10-13) ----

_LOOP = Settings(
    db_password="x",
    loop_ingest_interval_minutes=60,
    loop_resolve_interval_minutes=15,
    loop_d1_ingest_interval_hours=24,
)
_WED_18 = datetime(2026, 10, 14, 18, 0, tzinfo=UTC)  # a Wednesday, market open


def _call(horizon_at: datetime, timeframe: str = "1h") -> SimpleNamespace:
    return SimpleNamespace(horizon_at=horizon_at, timeframe=timeframe)


def test_a_call_five_minutes_past_its_horizon_is_not_overdue() -> None:
    """Regression: the report went red every hour for a call due at 18:00
    and checked at 18:05 — its outcome bar cannot exist before 19:00."""
    assert late_predictions([_call(_WED_18)], _LOOP, now=_WED_18 + timedelta(minutes=5)) == (0, 0)


def test_an_hourly_call_is_late_only_after_its_bar_settled_and_was_fetched() -> None:
    due = outcome_expected_by(
        _WED_18, Timeframe.H1, ingest_every=timedelta(hours=1), resolve_every=timedelta(minutes=15)
    )
    assert due == _WED_18 + timedelta(hours=2, minutes=45)  # bar 1h + ingest 1h + 15m + 30m
    assert late_predictions([_call(_WED_18)], _LOOP, now=due) == (0, 0)
    assert late_predictions([_call(_WED_18)], _LOOP, now=due + timedelta(minutes=1)) == (1, 0)


def test_a_call_expiring_into_the_weekend_waits_for_the_reopen() -> None:
    saturday = datetime(2026, 10, 17, 6, 0, tzinfo=UTC)  # when the weekly report runs
    friday_late = datetime(2026, 10, 16, 23, 0, tzinfo=UTC)
    assert late_predictions([_call(friday_late)], _LOOP, now=saturday) == (0, 0)
    sunday_reopen = datetime(2026, 10, 18, 23, 0, tzinfo=UTC)
    assert late_predictions([_call(friday_late)], _LOOP, now=sunday_reopen) == (0, 0)
    monday = datetime(2026, 10, 19, 6, 0, tzinfo=UTC)
    assert late_predictions([_call(friday_late)], _LOOP, now=monday) == (1, 0)


def test_a_daily_call_has_about_two_days_before_it_is_late() -> None:
    horizon = datetime(2026, 10, 13, tzinfo=UTC)  # Tuesday
    assert late_predictions([_call(horizon, "1d")], _LOOP, now=horizon + timedelta(days=2)) == (
        0,
        0,
    )
    assert late_predictions([_call(horizon, "1d")], _LOOP, now=horizon + timedelta(days=3)) == (
        1,
        0,
    )


def test_a_call_past_the_resolvers_limit_is_lost_not_merely_late() -> None:
    lost_at = _WED_18 + timedelta(days=4)
    assert late_predictions([_call(_WED_18)], _LOOP, now=lost_at - timedelta(hours=1)) == (1, 0)
    assert late_predictions([_call(_WED_18)], _LOOP, now=lost_at) == (0, 1)
    d = _digest(overdue_predictions=0, lost_predictions=1)
    assert next(c for c in d.checks if c.key == "resolution").level is Level.FAIL


def test_a_retrain_that_stopped_firing_is_caught() -> None:
    """Silent, and the exact failure the interval-job bug caused all day."""
    d = _digest(last_retrain=NOW - timedelta(days=20), retrain_interval_hours=168)
    check = next(c for c in d.checks if c.key == "retrain")
    assert check.level is Level.FAIL
    assert "stopped learning" in check.detail


def test_a_retrain_inside_twice_the_cadence_is_fine() -> None:
    d = _digest(last_retrain=NOW - timedelta(days=9), retrain_interval_hours=168)
    assert next(c for c in d.checks if c.key == "retrain").level is Level.OK


def test_missing_alerting_is_flagged_because_silence_is_the_risk() -> None:
    d = _digest(alerts_enabled=False)
    check = next(c for c in d.checks if c.key == "alerting")
    assert check.level is Level.WARN
    assert "only find out by looking" in check.detail


def test_a_bar_one_interval_late_is_not_an_emergency() -> None:
    """The current bar has simply not closed yet."""
    d = _digest(newest_bar=NOW - timedelta(minutes=55))
    assert next(c for c in d.checks if c.key == "feed").level is Level.OK


# ---------- evidence, stated in time rather than signals ----------


def test_a_thin_sample_is_translated_into_weeks_of_waiting() -> None:
    d = _digest(
        independent_windows=5,
        windows_needed=30,
        paper_verdict="5 independent windows — not distinguishable from a coin flip.",
    )
    assert "25 more independent windows" in d.evidence
    assert "5 more week(s)" in d.evidence
    assert "one independent observation per trading day" in d.evidence


def test_a_sufficient_sample_reports_the_verdict_unqualified() -> None:
    d = _digest(independent_windows=40, windows_needed=30)
    assert d.evidence == "40 windows, 58% correct — the edge is real."
    assert "more week" not in d.evidence


# ---------- alert configuration ----------


def test_both_telegram_settings_read_unprefixed_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: the token carried an explicit TELEGRAM_BOT_TOKEN alias but
    the chat id did not, so the MENTOR_ prefix applied to it alone. Setting
    the obvious pair left the chat id empty — and because both-unset disables
    alerting silently, that produced no alerts and no error.

    monkeypatch rather than os.environ: the first version of this test set the
    variables directly and leaked MENTOR_DB_PASSWORD into the rest of the
    session, breaking an unrelated security test that asserts production
    defaults are flagged when unset.
    """
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654")
    monkeypatch.setenv("MENTOR_DB_PASSWORD", "x")
    monkeypatch.setenv("MENTOR_JWT_SECRET", "y" * 32)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.telegram_bot_token.get_secret_value() == "123:abc"
    assert settings.telegram_chat_id == "987654"
