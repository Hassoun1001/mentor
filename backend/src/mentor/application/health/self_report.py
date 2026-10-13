"""The weekly self-report — what the system knows about itself, written down.

It has two readers. The owner gets a short Telegram summary. The
maintenance agent gets the full machine-readable report: every health
check, each lane's live record graded against that lane's own breakeven,
what retrained and what was decided, whether live calibration is
correcting anything, which jobs are failing, and which warnings keep
recurring. Each problem is an ``Issue`` with a stable ``code``, so a later
reader can tell "still broken" from "new".

The judgement — what counts as a problem, and how bad — lives in the pure
``assemble_report``. ``collect_self_report`` only fetches. Nothing here
changes behaviour: this module reports, and something else acts.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePath

from sqlalchemy.ext.asyncio import AsyncSession

from mentor.application.forecasting.economics import lane_breakeven
from mentor.application.forecasting.live_calibration import (
    champion_live_calls,
    parse_promoted_at,
)
from mentor.application.forecasting.promotion import PromotionService
from mentor.application.health.collect import collect_digest, last_decision_at
from mentor.application.health.digest import Digest, Level
from mentor.config import Settings
from mentor.domain.forecasting.forecast import Direction
from mentor.domain.stats.independence import select_independent
from mentor.domain.stats.significance import MIN_SAMPLE_FOR_VERDICT, assess_proportion
from mentor.infrastructure.models import PredictionORM
from mentor.infrastructure.repositories import PredictionRepository
from mentor.logging import log_tally

_WEEK = timedelta(days=7)

# A week's Brier this far above a coin flip (0.25), on enough calls to mean
# something, deserves a look before the slower verdict machinery would flag it.
_BRIER_ALARM = 0.27
_BRIER_MIN_CALLS = 20

# A warning that fires this often inside the tally window is a recurring
# degradation, not a blip.
_WARNING_RECURS = 10

# Matches the promotion gate's demotion streak; reported, never enforced here.
_DEMOTION_AFTER = 3

# The server's deploy script records each outcome here (inside the models
# volume, so the app can read it). It is the only way the maintenance agent
# learns that its push was refused or rolled back, and why.
_DEPLOY_STATUS_FILE = "deploy_status.json"
_BAD_DEPLOYS = frozenset(
    {"refused_protected", "refused_history", "refused_backup", "rolled_back", "rollback_failed"}
)

_REPORTS_DIR = "reports"
_KEEP_REPORTS = 26  # half a year of weekly reports
_HISTORY_IN_REPORT = 8


@dataclass(frozen=True, slots=True)
class Issue:
    code: str  # stable across runs, e.g. "h1.champion_failing"
    severity: str  # "fail" | "warn"
    detail: str


@dataclass(frozen=True, slots=True)
class LaneInputs:
    """Everything known about one lane, fetched but not yet judged."""

    lane: str
    label: str
    timeframe: str
    champion_name: str | None
    champion_promoted_at: datetime | None
    floor_failures: int
    independent_windows: int
    hits: int
    breakeven: float
    breakeven_measured: bool
    brier_week: float | None
    calls_week: int
    brier_prev_week: float | None
    calls_prev_week: int
    champion_calls_week: int
    decisions_week: tuple[dict[str, object], ...]
    last_decision_at: datetime | None
    retrain_interval_hours: int
    calibration: dict[str, object] | None
    calibration_progress: int


@dataclass(frozen=True, slots=True)
class LaneReport:
    lane: str
    label: str
    timeframe: str
    model: str
    champion_since: str | None
    floor_failures: int
    independent_windows: int
    win_rate: float | None
    ci_low: float | None
    ci_high: float | None
    breakeven: float
    significant: bool
    verdict: str
    brier_week: float | None
    brier_prev_week: float | None
    calls_week: int
    champion_share_week: float | None
    retrains_week: int
    promotions_week: int
    demotions_week: int
    last_decision_reason: str | None
    calibration: str


@dataclass(frozen=True, slots=True)
class SelfReport:
    generated_at: datetime
    status: str  # "ok" | "warn" | "fail" — the worst issue
    headline: str
    digest_checks: tuple[dict[str, str], ...]
    lanes: tuple[LaneReport, ...]
    failing_jobs: tuple[dict[str, str], ...]
    recurring: tuple[dict[str, object], ...]
    tally_since: str | None
    issues: tuple[Issue, ...]
    notes: tuple[str, ...]
    history: tuple[dict[str, object], ...]
    deploy: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        out = asdict(self)
        out["generated_at"] = self.generated_at.isoformat()
        return out

    def telegram_text(self, *, report_url: str | None = None) -> str:
        """A phone-sized summary. Plain words; the JSON carries the detail."""
        marker = {"ok": "✅", "warn": "⚠️", "fail": "❌"}.get(self.status, "")
        lines = [f"📋 Mentor weekly report {marker} {self.status.upper()}", self.headline, ""]
        for lane in self.lanes:
            since = f" (since {lane.champion_since[:10]})" if lane.champion_since else ""
            lines.append(f"{lane.label} — model: {lane.model}{since}")
            if lane.win_rate is not None:
                lines.append(
                    f"  {lane.independent_windows} independent results, "
                    f"{lane.win_rate * 100:.1f}% right (needs {lane.breakeven * 100:.1f}%)"
                    f" — {'proven' if lane.significant else 'not proven yet'}"
                )
            if lane.brier_week is not None:
                prev = (
                    f" (last week {lane.brier_prev_week:.3f})"
                    if lane.brier_prev_week is not None
                    else ""
                )
                lines.append(f"  prediction error this week {lane.brier_week:.3f}{prev}")
            lines.append(
                f"  {lane.retrains_week} retrain(s), {lane.promotions_week} promotion(s), "
                f"{lane.demotions_week} demotion(s)"
            )
        if self.issues:
            lines += ["", "Issues:"]
            lines += [f" {'❌' if i.severity == 'fail' else '⚠️'} {i.detail}" for i in self.issues]
        if self.notes:
            lines += ["", "Notes:"]
            lines += [f" • {n}" for n in self.notes]
        if report_url:
            lines += ["", f"Full report: {report_url}"]
        return "\n".join(lines)


# ---- judgement (pure) --------------------------------------------------------


def _parse_at(entry: dict[str, object]) -> datetime | None:
    raw = entry.get("at")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _calibration_sentence(lane: LaneInputs) -> str:
    if lane.champion_name is None:
        return "No trained model in force, so there is no confidence to correct."
    decision = lane.calibration
    if not decision or decision.get("model_name") != lane.champion_name:
        return (
            f"Collecting live results: {lane.calibration_progress} of "
            f"{MIN_SAMPLE_FOR_VERDICT} independent outcomes before the first check."
        )
    if decision.get("applied") is True:
        return f"Correcting its stated confidence from live results ({decision.get('reason', '')})."
    return f"Checked against live results; no correction applied ({decision.get('reason', '')})."


def _judge_lane(
    lane: LaneInputs, *, now: datetime, issues: list[Issue], notes: list[str]
) -> LaneReport:
    verdict = assess_proportion(
        lane.hits,
        lane.independent_windows,
        baseline=lane.breakeven,
        label="independent windows",
        baseline_label=(
            "the spread-adjusted breakeven" if lane.breakeven_measured else "a coin flip"
        ),
    )
    if verdict.significant and verdict.worse_than_baseline:
        issues.append(
            Issue(
                f"{lane.lane}.below_breakeven",
                "warn",
                f"{lane.label}: live record is significantly below the "
                f"{lane.breakeven * 100:.1f}% needed to pay for itself.",
            )
        )
    if (
        lane.brier_week is not None
        and lane.calls_week >= _BRIER_MIN_CALLS
        and lane.brier_week >= _BRIER_ALARM
    ):
        issues.append(
            Issue(
                f"{lane.lane}.calibration_week",
                "warn",
                f"{lane.label}: prediction error {lane.brier_week:.3f} this week over "
                f"{lane.calls_week} calls — clearly worse than a coin flip (0.250).",
            )
        )
    if lane.champion_name is not None and lane.floor_failures > 0:
        issues.append(
            Issue(
                f"{lane.lane}.champion_failing",
                "warn",
                f"{lane.label}: the live model failed its re-check {lane.floor_failures} "
                f"retrain(s) in a row; it is removed at {_DEMOTION_AFTER}.",
            )
        )
    # The digest already watches the primary lane's retrain cadence.
    if lane.lane != "h1":
        stalled_after = timedelta(hours=2 * lane.retrain_interval_hours)
        if lane.last_decision_at is None:
            issues.append(
                Issue(f"{lane.lane}.retrain_stalled", "warn", f"{lane.label}: never retrained.")
            )
        elif now - lane.last_decision_at > stalled_after:
            days = (now - lane.last_decision_at).days
            issues.append(
                Issue(
                    f"{lane.lane}.retrain_stalled",
                    "warn",
                    f"{lane.label}: last retrain was {days} days ago — it has stopped learning.",
                )
            )

    promotions = [d for d in lane.decisions_week if d.get("promoted") is True]
    demotions = [d for d in lane.decisions_week if d.get("demoted") is True]
    for d in promotions:
        notes.append(f"{lane.label}: new model {d.get('challenger')} went live.")
    for _ in demotions:
        notes.append(f"{lane.label}: the live model was removed after repeated failures.")

    win_rate = (
        lane.hits / lane.independent_windows if lane.independent_windows else None
    )
    last_reason: str | None = None
    if lane.decisions_week:
        raw_reason = lane.decisions_week[0].get("reason")
        last_reason = str(raw_reason) if raw_reason is not None else None
    share = (
        lane.champion_calls_week / lane.calls_week if lane.calls_week else None
    )
    return LaneReport(
        lane=lane.lane,
        label=lane.label,
        timeframe=lane.timeframe,
        model=lane.champion_name or "baseline rule",
        champion_since=(
            lane.champion_promoted_at.isoformat() if lane.champion_promoted_at else None
        ),
        floor_failures=lane.floor_failures,
        independent_windows=lane.independent_windows,
        win_rate=win_rate,
        ci_low=verdict.low if lane.independent_windows else None,
        ci_high=verdict.high if lane.independent_windows else None,
        breakeven=lane.breakeven,
        significant=verdict.significant,
        verdict=verdict.verdict,
        brier_week=lane.brier_week,
        brier_prev_week=lane.brier_prev_week,
        calls_week=lane.calls_week,
        champion_share_week=share,
        retrains_week=len(lane.decisions_week),
        promotions_week=len(promotions),
        demotions_week=len(demotions),
        last_decision_reason=last_reason,
        calibration=_calibration_sentence(lane),
    )


def _digest_issues(digest: Digest) -> list[Issue]:
    """Every digest check that is not OK, at the digest's own severity."""
    return [
        Issue(f"digest.{c.key}", c.level.value, f"{c.label}: {c.detail}")
        for c in digest.checks
        if c.level is not Level.OK
    ]


def _recurring_issues(tally: dict[str, object]) -> tuple[list[dict[str, object]], list[Issue]]:
    """Any logged error, and any warning that keeps recurring."""
    raw_events = tally.get("events")
    events = raw_events if isinstance(raw_events, list) else []
    recurring: list[dict[str, object]] = []
    issues: list[Issue] = []
    for e in events:
        if not isinstance(e, dict):
            continue
        level, event = str(e.get("level")), str(e.get("event"))
        count = e.get("count")
        n = count if isinstance(count, int) else 0
        if level in ("error", "critical", "exception"):
            recurring.append(e)
            issues.append(Issue(f"log.{level}.{event}", "warn", f"Logged {n}× as {level}: {event}"))
        elif n >= _WARNING_RECURS:
            recurring.append(e)
            issues.append(
                Issue(f"log.warning.{event}", "warn", f"Recurring warning ({n}×): {event}")
            )
    return recurring, issues


def _deploy_issues(deploy: dict[str, object] | None) -> list[Issue]:
    """The latest deploy outcome, if the server refused or rolled it back."""
    events = (deploy or {}).get("events")
    if not isinstance(events, list) or not events or not isinstance(events[0], dict):
        return []
    latest = events[0]
    outcome = str(latest.get("outcome"))
    if outcome not in _BAD_DEPLOYS:
        return []
    sha = str(latest.get("sha") or "")[:7]
    why = str(latest.get("detail") or "").strip().splitlines()
    return [
        Issue(
            f"deploy.{outcome}",
            "fail" if outcome == "rollback_failed" else "warn",
            f"The last push ({sha}) was {outcome.replace('_', ' ')}"
            + (f": {why[0]}" if why else "."),
        )
    ]


def assemble_report(
    *,
    now: datetime,
    digest: Digest,
    lanes: Sequence[LaneInputs],
    heartbeats: Sequence[dict[str, object]],
    tally: dict[str, object],
    history: Sequence[dict[str, object]] = (),
    deploy: dict[str, object] | None = None,
) -> SelfReport:
    issues: list[Issue] = [*_digest_issues(digest), *_deploy_issues(deploy)]
    notes: list[str] = []

    failing_jobs = tuple(
        {"job": str(b.get("job")), "at": str(b.get("at")), "note": str(b.get("note"))}
        for b in heartbeats
        if b.get("ok") is False
    )
    issues += [
        Issue(f"job.{job['job']}", "warn", f"Job '{job['job']}' last failed: {job['note']}")
        for job in failing_jobs
    ]

    lane_reports = tuple(_judge_lane(lane, now=now, issues=issues, notes=notes) for lane in lanes)

    recurring, log_issues = _recurring_issues(tally)
    issues += log_issues

    if any(i.severity == "fail" for i in issues):
        status = Level.FAIL.value
    elif issues:
        status = Level.WARN.value
    else:
        status = Level.OK.value

    if not issues:
        headline = "Everything ran and nothing needs attention."
    else:
        fails = sum(1 for i in issues if i.severity == "fail")
        headline = f"{len(issues)} issue(s) need attention" + (
            f", {fails} of them failures." if fails else "."
        )

    since = tally.get("since")
    return SelfReport(
        generated_at=now,
        status=status,
        headline=headline,
        digest_checks=tuple(
            {"key": c.key, "label": c.label, "level": c.level.value, "detail": c.detail}
            for c in digest.checks
        ),
        lanes=lane_reports,
        failing_jobs=failing_jobs,
        recurring=tuple(recurring),
        tally_since=str(since) if since is not None else None,
        issues=tuple(issues),
        notes=tuple(notes),
        history=tuple(history),
        deploy=deploy,
    )


# ---- persistence --------------------------------------------------------------


class ReportStore:
    """Weekly reports on disk, beside the models, so the trend survives restarts."""

    def __init__(self, model_store_dir: str | Path) -> None:
        self._dir = Path(model_store_dir) / _REPORTS_DIR

    def write(self, report: SelfReport) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{report.generated_at:%Y-%m-%d}.json"
        path.write_text(json.dumps(report.to_dict(), indent=1), encoding="utf-8")
        for stale in sorted(self._dir.glob("*.json"))[:-_KEEP_REPORTS]:
            stale.unlink(missing_ok=True)
        return path

    def history(self, *, limit: int = _HISTORY_IN_REPORT) -> list[dict[str, object]]:
        """Compact headline metrics of earlier reports, newest first."""
        if not self._dir.exists():
            return []
        out: list[dict[str, object]] = []
        for path in sorted(self._dir.glob("*.json"), reverse=True)[:limit]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue  # a torn write must not break the report
            raw_lanes = data.get("lanes")
            lanes = raw_lanes if isinstance(raw_lanes, list) else []
            raw_issues = data.get("issues")
            issue_list = raw_issues if isinstance(raw_issues, list) else []
            out.append(
                {
                    "date": path.stem,
                    "status": data.get("status"),
                    "lanes": [
                        {
                            "lane": ln.get("lane"),
                            "model": ln.get("model"),
                            "independent_windows": ln.get("independent_windows"),
                            "win_rate": ln.get("win_rate"),
                            "brier_week": ln.get("brier_week"),
                        }
                        for ln in lanes
                        if isinstance(ln, dict)
                    ],
                    "issues": [i.get("code") for i in issue_list if isinstance(i, dict)],
                }
            )
        return out


# ---- collection ------------------------------------------------------------------


def _brier(pairs: Sequence[tuple[float, int]]) -> float | None:
    if not pairs:
        return None
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def _outcome_pairs(rows: Sequence[PredictionORM]) -> list[tuple[float, int]]:
    return [
        (float(r.p_up), int(r.realised_outcome)) for r in rows if r.realised_outcome is not None
    ]


def _resolving_between(
    rows: Sequence[PredictionORM], start: datetime, end: datetime
) -> list[PredictionORM]:
    """Calls whose outcome fell due in [start, end) — what this week graded."""
    return [r for r in rows if start <= r.horizon_at < end]


def read_deploy_status(model_store_dir: str | Path) -> dict[str, object] | None:
    """What the server's deploy script last recorded; None if nothing yet."""
    path = Path(model_store_dir) / _DEPLOY_STATUS_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _lane_dir(model_store_dir: str, lane: str) -> str:
    """H1 keeps the root store; other lanes live in a substore."""
    return model_store_dir if lane == "h1" else str(PurePath(model_store_dir) / lane)


def report_url(settings: Settings) -> str | None:
    """Public address of the report, from the deploy's HTTPS origin."""
    origin = next((o for o in settings.cors_origins if o.startswith("https://")), None)
    return f"{origin.rstrip('/')}/api/v1/health/report" if origin else None


async def collect_self_report(
    session: AsyncSession,
    settings: Settings,
    *,
    loop_status: dict[str, object] | None,
    now: datetime | None = None,
) -> SelfReport:
    now = now or datetime.now(UTC)
    status = loop_status or {}
    digest = await collect_digest(
        session, settings, alerts_enabled=bool(status.get("alerts_enabled")), now=now
    )

    repo = PredictionRepository(session)
    resolved = await repo.list_resolved(limit=20000)

    lane_specs: list[tuple[str, str, str, int]] = [
        ("h1", "24-hour lane", settings.loop_timeframe, settings.loop_retrain_interval_hours)
    ]
    if settings.loop_d1_enabled:
        lane_specs.append(("d1", "5-day lane", "1d", settings.loop_d1_retrain_interval_hours))

    lanes: list[LaneInputs] = []
    for lane, label, timeframe, interval in lane_specs:
        rows = [r for r in resolved if r.timeframe == timeframe]
        independent = select_independent(
            [
                (r.asof, r.horizon_at, float(r.p_up), int(r.realised_outcome))
                for r in rows
                if r.realised_outcome is not None and r.direction != Direction.NEUTRAL.value
            ]
        )
        hits = sum(1 for p, y in independent if (p >= 0.5) == (y == 1))
        basis = await lane_breakeven(session, settings=settings, timeframe=timeframe)

        week = _resolving_between(rows, now - _WEEK, now)
        prev = _resolving_between(rows, now - 2 * _WEEK, now - _WEEK)

        promo = PromotionService(model_store_dir=_lane_dir(settings.model_store_dir, lane))
        champion = promo.current_champion()
        champion_name = str(champion["model_name"]) if champion else None
        promoted_at = parse_promoted_at(champion)
        raw_failures = (champion or {}).get("floor_failures")
        decisions = tuple(
            d
            for d in promo.promotion_history(limit=50)
            if (at := _parse_at(d)) is not None and at >= now - _WEEK
        )
        progress = 0
        if champion_name is not None and promoted_at is not None:
            since = await repo.list_resolved_since(timeframe=timeframe, since=promoted_at)
            progress = len(champion_live_calls(since, promoted_at=promoted_at))

        lanes.append(
            LaneInputs(
                lane=lane,
                label=label,
                timeframe=timeframe,
                champion_name=champion_name,
                champion_promoted_at=promoted_at,
                floor_failures=int(raw_failures) if isinstance(raw_failures, int) else 0,
                independent_windows=len(independent),
                hits=hits,
                breakeven=basis.breakeven,
                breakeven_measured=basis.measured,
                brier_week=_brier(_outcome_pairs(week)),
                calls_week=len(week),
                brier_prev_week=_brier(_outcome_pairs(prev)),
                calls_prev_week=len(prev),
                champion_calls_week=sum(
                    1 for r in week if not str(r.model_name).startswith("baseline")
                ),
                decisions_week=decisions,
                last_decision_at=last_decision_at(promo),
                retrain_interval_hours=interval,
                calibration=promo.live_calibration(),
                calibration_progress=progress,
            )
        )

    raw_beats = status.get("heartbeats")
    beats = raw_beats if isinstance(raw_beats, list) else []
    heartbeats = [b for b in beats if isinstance(b, dict)]
    return assemble_report(
        now=now,
        digest=digest,
        lanes=lanes,
        heartbeats=heartbeats,
        tally=log_tally().snapshot(),
        history=ReportStore(settings.model_store_dir).history(),
        deploy=read_deploy_status(settings.model_store_dir),
    )
