"""One answer to "has this thing been working while I was away?"

The information already exists, spread across the Loop page, Data Health,
and Predictions. Reading it means visiting several screens and knowing
which numbers matter — which is fine when you are looking every day, and
useless when you come back after a fortnight and want a yes or a no.

The digest separates two questions that are constantly confused:

**Is it running?** Answerable in a week, and the only question with a
crisp answer. Jobs fired, bars arrived, predictions resolved, nothing
errored.

**Is it any good?** Not answerable in a week, and pretending otherwise is
the failure this whole system was built to avoid. At a 24-hour horizon
you earn roughly one independent observation per trading day, so a
fortnight buys about ten — still short of the thirty below which no
verdict is given at all. The digest says so in those terms rather than
letting a rising signal count look like progress.

Health checks are deliberately blunt and fail loudly. A digest that hedges
is a digest nobody acts on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class Level(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class Check:
    key: str
    label: str
    level: Level
    detail: str


@dataclass(frozen=True, slots=True)
class Digest:
    generated_at: datetime
    window_days: int
    checks: tuple[Check, ...]
    headline: str
    evidence: str

    @property
    def worst(self) -> Level:
        if any(c.level is Level.FAIL for c in self.checks):
            return Level.FAIL
        if any(c.level is Level.WARN for c in self.checks):
            return Level.WARN
        return Level.OK


def _feed_check(newest_bar: datetime | None, interval_minutes: int, now: datetime) -> Check:
    """Stale bars mean everything downstream is describing the past."""
    if newest_bar is None:
        return Check(
            key="feed",
            label="Price feed",
            level=Level.FAIL,
            detail="No bars stored at all — nothing can run.",
        )
    age = (now - newest_bar).total_seconds() / 60
    # One interval late is the current bar not having closed. Beyond three,
    # ingestion has stopped.
    if age > interval_minutes * 3:
        return Check(
            key="feed",
            label="Price feed",
            level=Level.FAIL,
            detail=(
                f"Newest bar is {age / 60:.1f} hours old. Ingestion has stopped — "
                f"every prediction and price on screen is stale."
            ),
        )
    if age > interval_minutes * 1.5:
        return Check(
            key="feed",
            label="Price feed",
            level=Level.WARN,
            detail=f"Newest bar is {age:.0f} minutes old — one cycle may have been missed.",
        )
    return Check(
        key="feed",
        label="Price feed",
        level=Level.OK,
        detail=f"Newest bar is {age:.0f} minutes old.",
    )


def _resolution_check(pending: int, overdue: int) -> Check:
    """Overdue predictions are lost track record, not a queue."""
    if overdue > 0:
        return Check(
            key="resolution",
            label="Predictions resolving",
            level=Level.FAIL,
            detail=(
                f"{overdue} prediction(s) are past their horizon and unresolved. "
                f"Beyond four days they can never be graded — that is track record "
                f"being permanently lost."
            ),
        )
    return Check(
        key="resolution",
        label="Predictions resolving",
        level=Level.OK,
        detail=f"{pending} awaiting their horizon, none overdue.",
    )


def _retrain_check(last_retrain: datetime | None, interval_hours: int, now: datetime) -> Check:
    """A retrain that never fires is a system that stops learning silently."""
    if last_retrain is None:
        return Check(
            key="retrain",
            label="Retraining",
            level=Level.WARN,
            detail="No retrain has ever been recorded.",
        )
    days = (now - last_retrain).total_seconds() / 86400
    allowed = interval_hours / 24 * 2
    if days > allowed:
        return Check(
            key="retrain",
            label="Retraining",
            level=Level.FAIL,
            detail=(
                f"Last retrain was {days:.1f} days ago, more than twice the "
                f"{interval_hours / 24:.0f}-day cadence. The system has stopped learning."
            ),
        )
    return Check(
        key="retrain",
        label="Retraining",
        level=Level.OK,
        detail=f"Last retrain {days:.1f} days ago.",
    )


def _alerting_check(alerts_enabled: bool) -> Check:
    """Silent failure is the whole risk of leaving it alone."""
    if alerts_enabled:
        return Check(
            key="alerting",
            label="Alerting",
            level=Level.OK,
            detail="Configured — a failure will message you.",
        )
    return Check(
        key="alerting",
        label="Alerting",
        level=Level.WARN,
        detail=(
            "Not configured. Nothing will tell you if this stops working — you "
            "will only find out by looking."
        ),
    )


def _evidence_sentence(independent_windows: int, needed: int, verdict: str) -> str:
    """Where the edge question actually stands, in days rather than signals."""
    if independent_windows >= needed:
        return verdict
    short = needed - independent_windows
    # One genuinely independent observation per trading day at a 24-bar horizon.
    weeks = short / 5
    return (
        f"{verdict} Roughly {short} more independent windows are needed — about "
        f"{weeks:.0f} more week(s) of running, because a 24-hour horizon yields "
        f"about one independent observation per trading day no matter how many "
        f"signals are logged."
    )


def build_digest(
    *,
    window_days: int,
    newest_bar: datetime | None,
    ingest_interval_minutes: int,
    pending_predictions: int,
    overdue_predictions: int,
    last_retrain: datetime | None,
    retrain_interval_hours: int,
    alerts_enabled: bool,
    independent_windows: int,
    windows_needed: int,
    paper_verdict: str,
    now: datetime | None = None,
) -> Digest:
    now = now or datetime.now(UTC)
    checks = (
        _feed_check(newest_bar, ingest_interval_minutes, now),
        _resolution_check(pending_predictions, overdue_predictions),
        _retrain_check(last_retrain, retrain_interval_hours, now),
        _alerting_check(alerts_enabled),
    )

    failures = [c for c in checks if c.level is Level.FAIL]
    warnings = [c for c in checks if c.level is Level.WARN]
    if failures:
        headline = (
            f"{len(failures)} thing(s) stopped working: "
            + "; ".join(c.label.lower() for c in failures)
            + ". Fix these before reading any performance number below — a broken "
            "feed makes every other figure describe the past."
        )
    elif warnings:
        headline = (
            "Running, with "
            + "; ".join(c.label.lower() for c in warnings)
            + " worth attention."
        )
    else:
        headline = "Everything ran. No gaps, nothing overdue, nothing errored."

    return Digest(
        generated_at=now,
        window_days=window_days,
        checks=checks,
        headline=headline,
        evidence=_evidence_sentence(independent_windows, windows_needed, paper_verdict),
    )


def horizon_to_days(horizon_bars: int, timeframe_seconds: int) -> float:
    """How long one prediction's outcome window actually spans."""
    return horizon_bars * timeframe_seconds / 86400


def default_window(now: datetime | None = None) -> tuple[datetime, int]:
    """A week back, the interval most people mean by "while I was away"."""
    now = now or datetime.now(UTC)
    return now - timedelta(days=7), 7
