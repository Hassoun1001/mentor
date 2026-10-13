"""One-off repair of bars stored before their period closed.

Ingestion now corrects a provisional bar whenever its window is fetched
again (``ingestion_service.py``), but its window is the last 10 hourly or
60 daily days. Older provisional rows — back to mid-July 2026 in
production — are never fetched again and need this explicit step.

Three phases, the operator choosing each one (``mentor.cli.repair_bars``):

- **plan** is read-only: it fetches the settled bars covering every
  provisional row and reports what would change and by how much.
- **apply** corrects the rows a settled bar matches, removes misaligned
  rows (a feed's live tick stamped between bars), and — only when asked —
  removes provisional rows no settled bar matches. One batch id covers the
  run; every change is logged with the values it replaced.
- **revert** puts a batch back exactly as it was.

Predictions and graded outcomes are never touched: each keeps the
``asof_close`` and ``realised_close`` it was recorded with.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from mentor.application.market.ingestion_service import BarStore
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.domain.market.settlement import (
    BarCorrection,
    StoredBar,
    is_aligned,
    plan_corrections,
    screen,
)
from mentor.logging import get_logger

log = get_logger("mentor.market.repair")

# Twelve Data serves at most 5,000 bars a request; stay well inside it.
_FETCH_CHUNK_BARS = 4000

REPAIR_CORRECTION_REASON = (
    "repair: stored before its period closed; replaced by the settled bar"
)
REPAIR_MISALIGNED_REASON = "repair: not on a bar boundary (a feed's live tick)"
REPAIR_UNMATCHED_REASON = "repair: stored before its period closed; no settled bar exists"


class RepairStore(BarStore, Protocol):
    async def misaligned(self, *, symbol: str, timeframe: Timeframe) -> Sequence[StoredBar]: ...

    async def remove(
        self,
        rows: Sequence[StoredBar],
        *,
        batch_id: str,
        reason: str,
        now: datetime,
    ) -> int: ...

    async def revert(self, *, batch_id: str, now: datetime) -> tuple[int, int]: ...


@dataclass(frozen=True, slots=True)
class RepairPlan:
    symbol: str
    timeframe: Timeframe
    pip: Decimal
    provisional: int
    corrections: tuple[BarCorrection, ...]
    misaligned: tuple[StoredBar, ...]
    unmatched: tuple[StoredBar, ...]  # provisional, aligned, no settled bar fetched

    def _moves_in_pips(self) -> list[float]:
        return [float(c.max_move / self.pip) for c in self.corrections]

    def describe(self) -> str:
        moves = self._moves_in_pips()
        lines = [
            f"{self.symbol} {self.timeframe.value}: {self.provisional} bar(s) stored before "
            f"their period closed; {len(self.misaligned)} misaligned row(s).",
            f"  correct: {len(self.corrections)} — "
            f"{sum(m > 0.5 for m in moves)} move more than 0.5 pip, "
            f"{sum(m > 5 for m in moves)} more than 5 pips"
            + (
                f" (median {statistics.median(moves):.1f}, largest {max(moves):.1f} pips)"
                if moves
                else ""
            ),
            f"  remove (misaligned): {len(self.misaligned)}",
            f"  no settled bar found: {len(self.unmatched)}"
            + (
                " — " + ", ".join(f"{r.ts:%Y-%m-%d %H:%M}" for r in self.unmatched[:10])
                if self.unmatched
                else ""
            ),
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class RepairOutcome:
    batch_id: str
    corrected: int
    removed_misaligned: int
    removed_unmatched: int


class BarRepairService:
    def __init__(self, *, adapter: MarketDataAdapter, repo: RepairStore, pip: Decimal) -> None:
        self._adapter = adapter
        self._repo = repo
        self._pip = pip

    async def _fetch_settled(
        self, *, symbol: str, timeframe: Timeframe, start: datetime, now: datetime
    ) -> list[PriceBar]:
        chunk = timedelta(seconds=timeframe.seconds * _FETCH_CHUNK_BARS)
        out: dict[datetime, PriceBar] = {}
        cursor = start
        while cursor < now:
            stop = min(cursor + chunk, now)
            fetched = [
                b
                async for b in self._adapter.fetch_bars(
                    symbol=symbol, timeframe=timeframe, start=cursor, end=stop
                )
            ]
            for bar in screen(fetched, now=now).settled:
                out[bar.ts] = bar
            cursor = stop
        return [out[ts] for ts in sorted(out)]

    async def plan(self, *, symbol: str, timeframe: Timeframe, now: datetime) -> RepairPlan:
        """Read-only: what ``apply`` would change."""
        # Only bars whose period is over: a settled version can exist.
        provisional = await self._repo.provisional(
            symbol=symbol, timeframe=timeframe, end=now - timedelta(seconds=timeframe.seconds)
        )
        misaligned = tuple(await self._repo.misaligned(symbol=symbol, timeframe=timeframe))
        aligned = [r for r in provisional if is_aligned(r.ts, timeframe)]
        corrections: list[BarCorrection] = []
        if aligned:
            # Back one bar so the first provisional bar is inside the fetch.
            start = aligned[0].ts - timedelta(seconds=timeframe.seconds)
            settled = await self._fetch_settled(
                symbol=symbol, timeframe=timeframe, start=start, now=now
            )
            corrections = plan_corrections(aligned, settled, timeframe)
        matched = {c.stored.ts for c in corrections}
        return RepairPlan(
            symbol=symbol,
            timeframe=timeframe,
            pip=self._pip,
            provisional=len(provisional),
            corrections=tuple(corrections),
            misaligned=misaligned,
            unmatched=tuple(r for r in aligned if r.ts not in matched),
        )

    async def apply(
        self, plan: RepairPlan, *, now: datetime, remove_unmatched: bool
    ) -> RepairOutcome:
        batch_id = repair_batch_id(plan.timeframe, now)
        corrected = await self._repo.apply_corrections(
            plan.corrections, batch_id=batch_id, reason=REPAIR_CORRECTION_REASON, now=now
        )
        removed_misaligned = await self._repo.remove(
            plan.misaligned, batch_id=batch_id, reason=REPAIR_MISALIGNED_REASON, now=now
        )
        removed_unmatched = (
            await self._repo.remove(
                plan.unmatched, batch_id=batch_id, reason=REPAIR_UNMATCHED_REASON, now=now
            )
            if remove_unmatched
            else 0
        )
        log.warning(
            "bars.repaired",
            batch_id=batch_id,
            symbol=plan.symbol,
            timeframe=plan.timeframe.value,
            corrected=corrected,
            removed_misaligned=removed_misaligned,
            removed_unmatched=removed_unmatched,
        )
        return RepairOutcome(batch_id, corrected, removed_misaligned, removed_unmatched)

    async def revert(self, *, batch_id: str, now: datetime) -> tuple[int, int]:
        restored, skipped = await self._repo.revert(batch_id=batch_id, now=now)
        log.warning("bars.repair_reverted", batch_id=batch_id, restored=restored, skipped=skipped)
        return restored, skipped


def repair_batch_id(timeframe: Timeframe, now: datetime) -> str:
    return f"repair:{timeframe.value}:{now.astimezone(UTC):%Y%m%dT%H%M%SZ}"
