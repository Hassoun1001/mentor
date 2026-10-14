"""Re-grade already-resolved calls against their own finished horizon bars.

Until 2026-10-13 the resolver graded a call from the newest bar before its
horizon whenever the horizon bar was not stored yet — and it runs every 15
minutes, so that was nearly every call (2,134 of 2,229 hourly, 105 of 106
daily), on bars that were themselves captured mid-period. The bars have
since been repaired; this puts every graded call on the bar the resolver
now uses (``resolver.outcome_bar``), so the track record, drift watch and
live recalibration all read real outcomes.

Operator-run, owner-approved, in three phases like the bar repair
(``mentor.cli.regrade_predictions``):

- **plan** is read-only and reports what would change, per lane.
- **apply** changes ``realised_close`` and ``realised_outcome`` only —
  never ``asof_close``, the probabilities, ``resolved_at`` or which calls
  exist — logging the old values to ``prediction_regrades`` under one
  batch id.
- **revert** restores a batch.

A call whose own outcome bar is missing or not trustworthy is reported and
left exactly as it is; nothing is guessed.
"""

from __future__ import annotations

import bisect
import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from mentor.application.forecasting.resolver import MAX_RESOLUTION_LAG, outcome_bar
from mentor.domain.forecasting.outcome import OutcomeRegrade
from mentor.domain.market.bars import Timeframe
from mentor.domain.market.settlement import StoredBar
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.regrade")

REGRADE_REASON = (
    "re-graded on its own finished horizon bar (was graded on the bar before it, "
    "captured mid-period)"
)


class GradedCall(Protocol):
    @property
    def id(self) -> uuid.UUID: ...
    @property
    def symbol(self) -> str: ...
    @property
    def timeframe(self) -> str: ...
    @property
    def horizon_at(self) -> datetime: ...
    @property
    def asof_close(self) -> Decimal: ...
    @property
    def p_up(self) -> Decimal: ...
    @property
    def realised_close(self) -> Decimal | None: ...
    @property
    def realised_outcome(self) -> int | None: ...


class RegradeStore(Protocol):
    async def all_resolved(self) -> Sequence[GradedCall]: ...

    async def apply_regrades(
        self,
        regrades: Sequence[OutcomeRegrade],
        *,
        batch_id: str,
        reason: str,
        now: datetime,
    ) -> int: ...

    async def revert_regrades(self, *, batch_id: str, now: datetime) -> tuple[int, int]: ...


class BarRange(Protocol):
    async def range(
        self, *, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> Sequence[StoredBar]: ...


@dataclass
class LaneTally:
    examined: int = 0
    unchanged: int = 0
    changed: int = 0
    flipped: int = 0
    unavailable: int = 0
    hits_before: int = 0
    hits_after: int = 0

    def line(self, timeframe: str) -> str:
        n = self.examined - self.unavailable
        before = f"{self.hits_before / n:.1%}" if n else "n/a"
        after = f"{self.hits_after / n:.1%}" if n else "n/a"
        return (
            f"{timeframe}: {self.examined} graded call(s); {self.changed} move to their own bar "
            f"({self.flipped} flip up/down), {self.unchanged} already right, "
            f"{self.unavailable} left as they are (no trustworthy outcome bar). "
            f"Raw hit rate on re-gradable calls {before} -> {after} "
            f"(every call, overlapping; not the independent record)."
        )


@dataclass(frozen=True)
class RegradePlan:
    regrades: tuple[OutcomeRegrade, ...]
    unavailable: tuple[tuple[uuid.UUID, str, datetime], ...]
    lanes: dict[str, LaneTally] = field(default_factory=dict)

    def describe(self) -> str:
        lines = [self.lanes[tf].line(tf) for tf in sorted(self.lanes)]
        if self.unavailable:
            sample = ", ".join(
                f"{tf} {h:%Y-%m-%d %H:%M}" for _, tf, h in self.unavailable[:10]
            )
            lines.append(f"  not re-gradable (horizon): {sample}")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class RegradeOutcome:
    batch_id: str
    changed: int


def _called_up(p_up: Decimal) -> bool:
    return p_up >= Decimal("0.5")


class PredictionRegradeService:
    def __init__(self, *, predictions: RegradeStore, prices: BarRange) -> None:
        self._predictions = predictions
        self._prices = prices

    async def plan(self, *, now: datetime) -> RegradePlan:
        """Read-only: which graded calls move to their own finished bar."""
        calls = await self._predictions.all_resolved()
        groups: dict[tuple[str, str], list[GradedCall]] = defaultdict(list)
        for c in calls:
            groups[(c.symbol, c.timeframe)].append(c)

        regrades: list[OutcomeRegrade] = []
        unavailable: list[tuple[uuid.UUID, str, datetime]] = []
        lanes: dict[str, LaneTally] = defaultdict(LaneTally)
        for (symbol, tf_value), group in groups.items():
            tf = Timeframe(tf_value)
            step = timedelta(seconds=tf.seconds * 2)
            bars = sorted(
                await self._prices.range(
                    symbol=symbol,
                    timeframe=tf,
                    start=min(c.horizon_at for c in group) - step,
                    end=max(c.horizon_at for c in group) + MAX_RESOLUTION_LAG,
                ),
                key=lambda b: b.ts,
            )
            stamps = [b.ts for b in bars]
            for c in group:
                realised = c.realised_close
                if realised is None:
                    continue
                tally = lanes[tf_value]
                tally.examined += 1
                lo = bisect.bisect_left(stamps, c.horizon_at - step)
                hi = bisect.bisect_left(stamps, c.horizon_at + MAX_RESOLUTION_LAG)
                bar = outcome_bar(bars[lo:hi], horizon_at=c.horizon_at, timeframe=tf, now=now)
                old_close = Decimal(realised)
                old_outcome = int(c.realised_outcome or 0)
                if bar is None:
                    tally.unavailable += 1
                    unavailable.append((c.id, tf_value, c.horizon_at))
                    continue
                new_close = Decimal(bar.close)
                g = OutcomeRegrade(
                    prediction_id=c.id,
                    timeframe=tf_value,
                    old_close=old_close,
                    old_outcome=old_outcome,
                    new_close=new_close,
                    outcome_bar_ts=bar.ts,
                    asof_close=Decimal(c.asof_close),
                )
                up = _called_up(Decimal(c.p_up))
                tally.hits_before += int(up == (old_outcome == 1))
                tally.hits_after += int(up == (g.new_outcome == 1))
                if new_close == old_close:
                    tally.unchanged += 1
                    continue
                tally.changed += 1
                tally.flipped += int(g.flips)
                regrades.append(g)
        return RegradePlan(tuple(regrades), tuple(unavailable), dict(lanes))

    async def apply(self, plan: RegradePlan, *, now: datetime) -> RegradeOutcome:
        batch_id = regrade_batch_id(now)
        changed = await self._predictions.apply_regrades(
            plan.regrades, batch_id=batch_id, reason=REGRADE_REASON, now=now
        )
        log.warning(
            "predictions.regraded",
            batch_id=batch_id,
            changed=changed,
            planned=len(plan.regrades),
            unavailable=len(plan.unavailable),
        )
        return RegradeOutcome(batch_id, changed)

    async def revert(self, *, batch_id: str, now: datetime) -> tuple[int, int]:
        restored, skipped = await self._predictions.revert_regrades(batch_id=batch_id, now=now)
        log.warning(
            "predictions.regrade_reverted", batch_id=batch_id, restored=restored, skipped=skipped
        )
        return restored, skipped


def regrade_batch_id(now: datetime) -> str:
    return f"regrade:{now.astimezone(UTC):%Y%m%dT%H%M%SZ}"
