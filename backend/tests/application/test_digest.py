"""The digest must fail loudly and never let signal count look like evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from mentor.application.health import Level, build_digest
from mentor.config import Settings

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


def test_overdue_predictions_are_named_as_lost_record_not_a_queue() -> None:
    d = _digest(overdue_predictions=14)
    check = next(c for c in d.checks if c.key == "resolution")
    assert check.level is Level.FAIL
    assert "permanently lost" in check.detail


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
