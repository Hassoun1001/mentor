"""An in-memory ``LabStore`` and bar loader for the strategy-lab service tests.

Behaves like ``StrategyLabRepository`` where it matters: the trial ledger
ignores a configuration it already holds, positions come back newest
signal first, and a signal can be recorded only once per candidate.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from mentor.domain.market.bars import Timeframe
from mentor.domain.strategy_lab.series import BarSeries
from mentor.infrastructure.models import (
    PaperPositionORM,
    StrategyCandidateORM,
    StrategyEventORM,
    StrategyTrialORM,
)


class MemoryLabStore:
    def __init__(self) -> None:
        self.trials: list[StrategyTrialORM] = []
        self.candidates: list[StrategyCandidateORM] = []
        self.positions_: list[PaperPositionORM] = []
        self.events: list[StrategyEventORM] = []

    async def record_trials(self, rows: Sequence[StrategyTrialORM]) -> int:
        known = {t.config_key for t in self.trials}
        fresh = [r for r in rows if r.config_key not in known]
        self.trials += fresh
        return len(fresh)

    async def trial_count(self) -> int:
        return len(self.trials)

    async def trial_t_stats(self) -> list[float]:
        return [t.t_stat for t in self.trials if t.n_trades >= 2]

    async def list_candidates(self) -> list[StrategyCandidateORM]:
        return list(self.candidates)

    async def add_candidate(self, row: StrategyCandidateORM) -> None:
        assert all(c.key != row.key for c in self.candidates), "candidate keys are unique"
        self.candidates.append(row)

    async def positions(
        self,
        candidate_id: uuid.UUID,
        *,
        statuses: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> list[PaperPositionORM]:
        rows = [
            p
            for p in self.positions_
            if p.candidate_id == candidate_id and (statuses is None or p.status in statuses)
        ]
        rows.sort(key=lambda p: p.signal_ts, reverse=True)
        return rows[:limit] if limit is not None else rows

    async def add_position(self, row: PaperPositionORM) -> None:
        assert all(
            (p.candidate_id, p.signal_ts) != (row.candidate_id, row.signal_ts)
            for p in self.positions_
        ), "a signal is recorded once"
        self.positions_.append(row)

    async def add_event(self, row: StrategyEventORM) -> None:
        self.events.append(row)

    async def events_since(self, since: datetime) -> list[StrategyEventORM]:
        return sorted((e for e in self.events if e.at >= since), key=lambda e: e.at, reverse=True)

    async def flush(self) -> None:
        return None


def loader_for(series_by_tf: dict[Timeframe, BarSeries]):  # type: ignore[no-untyped-def]
    """Serve settled bars of a fixture series, as the SQL loader would."""

    async def load(timeframe: Timeframe, start: datetime, now: datetime) -> BarSeries:
        full = series_by_tf[timeframe]
        lo = full.index_at_or_after(start)
        cutoff = now.timestamp() - timeframe.seconds
        hi = lo
        while hi < len(full) and full.ts[hi].timestamp() <= cutoff:
            hi += 1
        return full.window(lo, hi)

    return load
