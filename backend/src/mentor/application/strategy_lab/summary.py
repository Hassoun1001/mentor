"""Where every idea stands — for the Strategy Lab page and the self-report.

Read-only. Collects each evaluated candidate's back-test verdict, its
paper record graded with the same statistics as the gate, and the bar as
it stands *today* (it only rises, so a candidate that passed last month
may no longer clear it — shown, not hidden).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from mentor.application.strategy_lab.paper import PAPER_ACCOUNT, independent_paper_rs
from mentor.application.strategy_lab.store import LabStore
from mentor.domain.stats.significance import assess_expectancy
from mentor.domain.strategy_lab.deflation import deflated_bar, trade_stats, trial_dispersion
from mentor.domain.strategy_lab.library import CANDIDATES, CandidateDefinition
from mentor.domain.strategy_lab.live import LabStatus, next_checkpoint
from mentor.infrastructure.models import PaperPositionORM, StrategyCandidateORM

_WEEK = timedelta(days=7)


def position_dict(p: PaperPositionORM) -> dict[str, object]:
    return {
        "status": p.status,
        "direction": p.direction,
        "reason": p.reason,
        "signal_ts": p.signal_ts.isoformat(),
        "entry_ts": p.entry_ts.isoformat() if p.entry_ts else None,
        "entry_price": float(p.entry_price) if p.entry_price is not None else None,
        "stop_price": float(p.stop_price),
        "target_price": float(p.target_price) if p.target_price is not None else None,
        "suggested_lots": float(p.suggested_lots) if p.suggested_lots is not None else None,
        "bars_held": p.bars_held,
        "exit_ts": p.exit_ts.isoformat() if p.exit_ts else None,
        "exit_price": float(p.exit_price) if p.exit_price is not None else None,
        "exit_reason": p.exit_reason,
        "realised_r": float(p.realised_r) if p.realised_r is not None else None,
        "note": p.note,
    }


@dataclass(frozen=True, slots=True)
class PaperRecord:
    trades: int  # independent closed paper trades
    mean_r: float | None
    win_rate: float | None
    breakeven_win_rate: float | None
    ci_low: float | None
    ci_high: float | None
    verdict: str
    next_check_at: int
    open_position: dict[str, object] | None
    pending_order: dict[str, object] | None
    last_bar_ts: str | None


@dataclass(frozen=True, slots=True)
class CandidateView:
    key: str
    title: str
    family: str
    timeframe: str
    hypothesis: str
    status: str
    status_reason: str
    evaluated_at: str
    n_trials_at_evaluation: int
    plan: dict[str, object] | None
    evidence: dict[str, object]
    clears_todays_bar: bool
    paper_started_at: str | None
    promoted_at: str | None
    demoted_at: str | None
    retired_at: str | None
    paper: PaperRecord | None


@dataclass(frozen=True, slots=True)
class LabView:
    trials_ever: int
    dispersion: float
    bar_now: float  # the score a new candidate must reach today
    paper_account: str
    candidates: tuple[CandidateView, ...]
    waiting: tuple[str, ...]  # registered but not yet evaluated
    changed: tuple[str, ...]  # edited after evaluation — refused a re-test
    events_week: tuple[dict[str, str], ...]

    def count(self, *statuses: LabStatus) -> int:
        wanted = {s.value for s in statuses}
        return sum(1 for c in self.candidates if c.status in wanted)

    def to_dict(self) -> dict[str, object]:
        out = asdict(self)
        out["counts"] = {
            "evaluated": len(self.candidates),
            "passed_backtest": len(self.candidates) - self.count(LabStatus.REJECTED),
            "paper": self.count(LabStatus.PAPER, LabStatus.DEMOTED),
            "recommended": self.count(LabStatus.RECOMMENDED),
            "retired": self.count(LabStatus.RETIRED),
        }
        return out


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


async def _paper_record(store: LabStore, row: StrategyCandidateORM) -> PaperRecord:
    closed = await store.positions(row.id, statuses=("closed",))
    live = await store.positions(row.id, statuses=("pending", "open"))
    rs = independent_paper_rs(closed)
    stats = trade_stats(rs)
    verdict = assess_expectancy(rs, label="paper trades")
    open_row = next((p for p in live if p.status == "open"), None)
    pending_row = next((p for p in live if p.status == "pending"), None)
    return PaperRecord(
        trades=stats.n,
        mean_r=stats.mean if stats.n else None,
        win_rate=stats.win_rate,
        breakeven_win_rate=stats.breakeven_win_rate,
        ci_low=verdict.low if stats.n >= 2 else None,
        ci_high=verdict.high if stats.n >= 2 else None,
        verdict=verdict.verdict,
        next_check_at=next_checkpoint(row.live_looks),
        open_position=position_dict(open_row) if open_row is not None else None,
        pending_order=position_dict(pending_row) if pending_row is not None else None,
        last_bar_ts=_iso(row.last_bar_ts),
    )


async def collect_lab_view(
    store: LabStore,
    *,
    now: datetime,
    candidates: Sequence[CandidateDefinition] = CANDIDATES,
) -> LabView:
    rows = await store.list_candidates()
    trials = await store.trial_count()
    dispersion = trial_dispersion(await store.trial_t_stats())
    bar_now = deflated_bar(trials, dispersion)
    by_key = {r.key: r for r in rows}
    registered = {c.key: c for c in candidates}

    views: list[CandidateView] = []
    for row in rows:
        evidence = json.loads(row.evidence_json)
        score = evidence.get("score")
        # The bar only rises; a candidate that passed when the ledger was
        # smaller may no longer clear it. Shown, never acted on retroactively.
        clears = bool(evidence.get("passed")) and isinstance(score, int | float)
        clears = clears and float(score) >= bar_now
        views.append(
            CandidateView(
                key=row.key,
                title=row.title,
                family=row.family,
                timeframe=row.timeframe,
                hypothesis=row.hypothesis,
                status=row.status,
                status_reason=row.status_reason,
                evaluated_at=row.evaluated_at.isoformat(),
                n_trials_at_evaluation=row.n_trials_at_evaluation,
                plan=json.loads(row.plan_json) if row.plan_json else None,
                evidence=evidence,
                clears_todays_bar=clears,
                paper_started_at=_iso(row.paper_started_at),
                promoted_at=_iso(row.promoted_at),
                demoted_at=_iso(row.demoted_at),
                retired_at=_iso(row.retired_at),
                paper=(
                    await _paper_record(store, row)
                    if row.paper_started_at is not None
                    else None
                ),
            )
        )
    events = await store.events_since(now - _WEEK)
    return LabView(
        trials_ever=trials,
        dispersion=dispersion,
        bar_now=bar_now,
        paper_account=f"{PAPER_ACCOUNT.amount:,.0f} {PAPER_ACCOUNT.currency}",
        candidates=tuple(views),
        waiting=tuple(k for k in registered if k not in by_key),
        changed=tuple(
            k
            for k, c in registered.items()
            if k in by_key and by_key[k].fingerprint != c.fingerprint()
        ),
        events_week=tuple(
            {"key": e.candidate_key, "kind": e.kind, "at": e.at.isoformat(), "detail": e.detail}
            for e in events
        ),
    )
