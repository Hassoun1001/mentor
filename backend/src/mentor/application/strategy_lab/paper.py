"""Paper trading: the plans that passed history, meeting the live market.

Each run, for every candidate that is paper trading:

1. Load enough recent *settled* bars to cover the plan's lookback.
2. Rebuild its ``PlanBook`` from the database (a pending order, an open
   position) and feed it every bar it has not seen yet — the same
   ``on_bar`` the back-test used, so the paper record is the tested plan
   itself, not a re-implementation.
3. Persist what happened: signals become pending paper positions (with the
   size the risk engine would give on a stated account), fills open them,
   exits close them with their R net of costs.
4. Re-judge the live record (``domain/strategy_lab/live.py``): promote,
   demote, retire, or keep watching.

Paper trading starts strictly forward: on its first run a plan only marks
the newest settled bar as its starting line. Nothing is back-filled into
the paper record — history already had its say at the gate.

Idempotent: a re-run with no new settled bar changes nothing, and a signal
can only ever be recorded once (unique on candidate and signal bar).
Nothing here talks to a broker. These are paper trades by construction.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Final

from mentor.application.strategy_lab.store import BarLoader, LabStore
from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument, get_instrument
from mentor.domain.money import Money
from mentor.domain.risk.position_sizing import Direction
from mentor.domain.stats.independence import select_independent
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.library import CANDIDATES, CandidateDefinition
from mentor.domain.strategy_lab.live import LabStatus, LiveAction, LiveDecision, judge_live
from mentor.domain.strategy_lab.simulator import (
    BookEvent,
    Cancelled,
    Closed,
    Filled,
    Friction,
    OpenTrade,
    PendingEntry,
    PlanBook,
    Signalled,
)
from mentor.domain.strategy_lab.spec import StrategySpec
from mentor.infrastructure.models import (
    PaperPositionORM,
    StrategyCandidateORM,
    StrategyEventORM,
)
from mentor.logging import get_logger

log = get_logger("mentor.strategy_lab.paper")

# Paper positions are sized as if on this account, so "how big would this
# have been?" has a concrete answer. Results are graded in R, which does
# not depend on it.
PAPER_ACCOUNT: Final = Money(Decimal("10000"), "USD")

# Recent history loaded per run: twice the plan's lookback in bars, plus
# room for weekends and holidays.
_LOOKBACK_SLACK = timedelta(days=10)

_PRICE = Decimal("0.00000001")
_R = Decimal("0.0001")


def _price(x: float) -> Decimal:
    return Decimal(repr(x)).quantize(_PRICE)


@dataclass(slots=True)
class PaperUpdate:
    key: str
    bars: int = 0
    log: list[str] = field(default_factory=list)
    decision: LiveDecision | None = None

    @property
    def alert(self) -> str | None:
        """A status change worth telling the owner about, in plain words."""
        d = self.decision
        if d is None or d.action is LiveAction.NONE:
            return None
        marker = {
            LiveAction.PROMOTE: "📈",
            LiveAction.DEMOTE: "📉",
            LiveAction.RETIRE: "🛑",
        }[d.action]
        return f"{marker} Strategy lab — {self.key}: {d.reason} (paper trading only)"


def chosen_spec(definition: CandidateDefinition, row: StrategyCandidateORM) -> StrategySpec | None:
    """The parameter set the gate chose for this candidate."""
    if row.plan_json is None:
        return None
    config_key = json.loads(row.plan_json).get("config_key")
    return next((s for s in definition.specs() if definition.config_key(s) == config_key), None)


def independent_paper_rs(
    closed: Sequence[PaperPositionORM], *, since: datetime | None = None
) -> list[float]:
    """R of non-overlapping closed paper trades entered at or after ``since``, oldest first."""
    calls: list[tuple[datetime, datetime, float, int]] = []
    for p in closed:
        if p.entry_ts is None or p.exit_ts is None or p.realised_r is None:
            continue
        if since is not None and p.entry_ts < since:
            continue
        calls.append((p.entry_ts, p.exit_ts, float(p.realised_r), len(calls)))
    kept = sorted((i for _, i in select_independent(calls)), key=lambda i: calls[i][0])
    return [calls[i][2] for i in kept]


class PaperTrader:
    def __init__(
        self,
        *,
        store: LabStore,
        load_bars: BarLoader,
        symbol: str,
        candidates: Sequence[CandidateDefinition] = CANDIDATES,
    ) -> None:
        self._store = store
        self._load = load_bars
        self._instrument: Instrument = get_instrument(symbol)
        self._friction = Friction.for_instrument(self._instrument)
        self._definitions = {c.key: c for c in candidates}

    async def advance(self, *, now: datetime) -> list[PaperUpdate]:
        rows = await self._store.list_candidates()
        updates: list[PaperUpdate] = []
        for row in rows:
            if not LabStatus(row.status).trades:
                continue
            definition = self._definitions.get(row.key)
            spec = chosen_spec(definition, row) if definition is not None else None
            if definition is None or spec is None:
                log.warning("strategy_lab.paper_orphan", candidate=row.key)
                continue
            update = await self._advance_one(row, spec, now=now)
            update.decision = await self._judge(row, rows, now=now)
            updates.append(update)
        await self._store.flush()
        return updates

    async def _advance_one(
        self, row: StrategyCandidateORM, spec: StrategySpec, *, now: datetime
    ) -> PaperUpdate:
        update = PaperUpdate(key=row.key)
        anchor = row.last_bar_ts or now
        span = timedelta(seconds=spec.timeframe.seconds * spec.lookback * 2) + _LOOKBACK_SLACK
        series = await self._load(spec.timeframe, anchor - span, now)
        if not len(series):
            return update
        if row.last_bar_ts is None:
            # The starting line: forward from here, never back-filled.
            row.last_bar_ts = series.ts[-1]
            update.log.append(f"paper trading starts after {series.ts[-1].isoformat()}")
            return update

        first_new = series.index_at_or_after(row.last_bar_ts)
        if first_new < len(series) and series.ts[first_new] == row.last_bar_ts:
            first_new += 1
        if first_new >= len(series):
            return update

        live = await self._store.positions(row.id, statuses=("pending", "open"))
        ledger = _Ledger(
            pending=next((p for p in live if p.status == "pending"), None),
            open=next((p for p in live if p.status == "open"), None),
        )
        book = PlanBook(
            pending=_pending_from(ledger.pending) if ledger.pending is not None else None,
            open=_open_from(ledger.open) if ledger.open is not None else None,
        )

        signals = spec.rule.signals(series)
        atrs = indicators.atr(series.high, series.low, series.close, spec.exits.atr_period)
        for i in range(first_new, len(series)):
            events = book.on_bar(
                series, i, signal=signals[i], atr=atrs[i], exits=spec.exits, friction=self._friction
            )
            for event in events:
                if isinstance(event, Signalled):
                    ledger.pending = self._new_position(row, spec, event.pending, series.close[i])
                    await self._store.add_position(ledger.pending)
                update.log.append(ledger.apply(event))
        if ledger.open is not None and book.open is not None:
            ledger.open.bars_held = book.open.bars_held
        update.bars = len(series) - first_new
        row.last_bar_ts = series.ts[-1]
        return update

    def _new_position(
        self,
        row: StrategyCandidateORM,
        spec: StrategySpec,
        pending: PendingEntry,
        reference: float,
    ) -> PaperPositionORM:
        lots: Decimal | None
        try:
            lots = spec.size(
                account=PAPER_ACCOUNT,
                entry=_price(reference),
                stop=_price(pending.stop),
                target=_price(pending.target) if pending.target is not None else None,
                direction=pending.direction,
                instrument=self._instrument,
            ).lots
        except ValidationError:
            lots = None
        return PaperPositionORM(
            id=uuid.uuid4(),
            candidate_id=row.id,
            status="pending",
            direction=pending.direction.value,
            reason=pending.reason,
            signal_ts=pending.signal_ts,
            stop_price=_price(pending.stop),
            target_price=_price(pending.target) if pending.target is not None else None,
            suggested_lots=lots,
            bars_held=0,
        )

    async def _judge(
        self,
        row: StrategyCandidateORM,
        rows: Sequence[StrategyCandidateORM],
        *,
        now: datetime,
    ) -> LiveDecision:
        closed = await self._store.positions(row.id, statuses=("closed",))
        decision = judge_live(
            status=LabStatus(row.status),
            rs=independent_paper_rs(closed),
            since_promotion=(
                independent_paper_rs(closed, since=row.promoted_at)
                if row.promoted_at is not None
                else []
            ),
            looks_taken=row.live_looks,
            live_looks_ever=sum(r.live_looks for r in rows),
        )
        row.live_looks = decision.looks_taken
        row.status_reason = decision.reason
        if decision.action is LiveAction.NONE:
            return decision
        row.status = decision.status.value
        kind = {
            LiveAction.PROMOTE: "promoted",
            LiveAction.DEMOTE: "demoted",
            LiveAction.RETIRE: "retired",
        }[decision.action]
        if decision.action is LiveAction.PROMOTE:
            row.promoted_at = now
        elif decision.action is LiveAction.DEMOTE:
            row.demoted_at = now
        else:
            row.retired_at = now
        await self._store.add_event(
            StrategyEventORM(
                id=uuid.uuid4(), candidate_key=row.key, kind=kind, detail=decision.reason, at=now
            )
        )
        log.info("strategy_lab.live_decision", candidate=row.key, action=kind)
        return decision


@dataclass(slots=True)
class _Ledger:
    """The database rows mirroring a ``PlanBook``'s pending order and open position."""

    pending: PaperPositionORM | None
    open: PaperPositionORM | None

    def apply(self, event: BookEvent) -> str:
        """Write one book event onto its row; return a log line."""
        if isinstance(event, Signalled):
            return f"signal {event.pending.direction.value}: {event.pending.reason}"
        if isinstance(event, Filled) and self.pending is not None:
            row, self.pending = self.pending, None
            row.status = "open"
            row.entry_ts = event.trade.entry_ts
            row.entry_price = _price(event.trade.entry_price)
            row.bars_held = 0
            self.open = row
            return f"filled at {event.trade.entry_price:.5f}"
        if isinstance(event, Cancelled) and self.pending is not None:
            row, self.pending = self.pending, None
            row.status = "cancelled"
            row.note = event.why
            return f"cancelled: {event.why}"
        if isinstance(event, Closed) and self.open is not None:
            row, self.open = self.open, None
            t = event.trade
            row.status = "closed"
            row.exit_ts = t.exit_ts
            row.exit_price = _price(t.exit_price)
            row.exit_reason = t.exit_reason.value
            row.realised_r = Decimal(repr(t.r)).quantize(_R)
            row.bars_held = t.bars_held
            return f"closed ({t.exit_reason.value}) at {t.r:+.2f}R"
        # The book and the rows disagree — a bug, never silently skipped.
        raise ValidationError(f"paper book event {type(event).__name__} has no matching row")


def _pending_from(p: PaperPositionORM) -> PendingEntry:
    return PendingEntry(
        direction=Direction(p.direction),
        signal_ts=p.signal_ts,
        stop=float(p.stop_price),
        target=float(p.target_price) if p.target_price is not None else None,
        reason=p.reason,
    )


def _open_from(p: PaperPositionORM) -> OpenTrade:
    if p.entry_ts is None or p.entry_price is None:
        raise ValidationError(f"open paper position {p.id} has no entry")
    return OpenTrade(
        direction=Direction(p.direction),
        signal_ts=p.signal_ts,
        entry_ts=p.entry_ts,
        entry_price=float(p.entry_price),
        stop=float(p.stop_price),
        target=float(p.target_price) if p.target_price is not None else None,
        bars_held=p.bars_held,
        reason=p.reason,
    )
