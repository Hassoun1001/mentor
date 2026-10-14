"""Re-grading moves graded calls onto their own finished bar — and nothing else.

Regression for the 2026-10-13 audit: the resolver graded nearly every call
from the bar *before* its horizon (that bar captured mid-period too). The
re-grade must change only the realised close and outcome, log what it
replaced, leave calls without a trustworthy bar alone, and be reversible.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from mentor.application.forecasting.regrade import (
    REGRADE_REASON,
    PredictionRegradeService,
    regrade_batch_id,
)
from mentor.domain.forecasting.outcome import OutcomeRegrade, outcome_of
from mentor.domain.market.bars import Timeframe

H = datetime(2026, 9, 16, 10, tzinfo=UTC)  # a horizon
NOW = datetime(2026, 10, 14, 6, tzinfo=UTC)


@dataclass(frozen=True)
class _Call:
    id: uuid.UUID
    horizon_at: datetime
    asof_close: Decimal
    p_up: Decimal
    realised_close: Decimal | None
    realised_outcome: int | None
    symbol: str = "EURUSD"
    timeframe: str = "1h"


def _call(close: str, *, horizon: datetime = H, p_up: str = "0.60") -> _Call:
    c = Decimal(close)
    asof = Decimal("1.1000")
    return _Call(uuid.uuid4(), horizon, asof, Decimal(p_up), c, outcome_of(asof, c))


def _bar(ts: datetime, close: str, *, stored_at: datetime | None = None) -> SimpleNamespace:
    c = Decimal(close)
    return SimpleNamespace(
        symbol="EURUSD",
        timeframe="1h",
        ts=ts,
        open=c,
        high=c,
        low=c,
        close=c,
        volume=None,
        source="twelve_data",
        ingested_at=stored_at or ts + timedelta(hours=1, minutes=2),
    )


class _Store:
    def __init__(self, calls: list[_Call]) -> None:
        self.calls = {c.id: c for c in calls}
        self.log: list[tuple[str, OutcomeRegrade]] = []

    async def all_resolved(self) -> Sequence[_Call]:
        return list(self.calls.values())

    async def apply_regrades(
        self, regrades: Sequence[OutcomeRegrade], *, batch_id: str, reason: str, now: datetime
    ) -> int:
        assert reason == REGRADE_REASON
        n = 0
        for g in regrades:
            c = self.calls[g.prediction_id]
            if c.realised_close != g.old_close:
                continue
            self.calls[c.id] = replace(
                c, realised_close=g.new_close, realised_outcome=g.new_outcome
            )
            self.log.append((batch_id, g))
            n += 1
        return n

    async def revert_regrades(self, *, batch_id: str, now: datetime) -> tuple[int, int]:
        n = 0
        for b, g in self.log:
            if b == batch_id:
                c = self.calls[g.prediction_id]
                self.calls[c.id] = replace(
                    c, realised_close=g.old_close, realised_outcome=g.old_outcome
                )
                n += 1
        return n, 0


class _Bars:
    def __init__(self, bars: list[SimpleNamespace]) -> None:
        self.bars = bars

    async def range(
        self, *, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[SimpleNamespace]:
        return [b for b in self.bars if start <= b.ts < end]


def _service(store: _Store, bars: list[SimpleNamespace]) -> PredictionRegradeService:
    return PredictionRegradeService(predictions=store, prices=_Bars(bars))


async def test_a_call_graded_on_the_bar_before_moves_to_its_own_bar() -> None:
    # Graded on the 09:00 bar's early close (1.0990, "down"); its own 10:00
    # bar closed at 1.1030 — the call was right, and the record said wrong.
    wrong = _call("1.0990")
    store = _Store([wrong])
    bars = [_bar(H - timedelta(hours=1), "1.0990"), _bar(H, "1.1030")]
    snapshot = dict(store.calls)

    plan = await _service(store, bars).plan(now=NOW)
    assert store.calls == snapshot  # plan writes nothing
    [g] = plan.regrades
    assert (g.old_close, g.new_close, g.outcome_bar_ts) == (Decimal("1.0990"), Decimal("1.1030"), H)
    assert g.flips and g.new_outcome == 1
    tally = plan.lanes["1h"]
    assert (tally.changed, tally.flipped, tally.hits_before, tally.hits_after) == (1, 1, 0, 1)

    done = await _service(store, bars).apply(plan, now=NOW)
    assert done.batch_id == regrade_batch_id(NOW) == "regrade:20261014T060000Z"
    after = store.calls[wrong.id]
    assert (after.realised_close, after.realised_outcome) == (Decimal("1.1030"), 1)
    # What was predicted, and from what price, never changes.
    assert (after.asof_close, after.p_up, after.horizon_at) == (
        wrong.asof_close,
        wrong.p_up,
        wrong.horizon_at,
    )

    await _service(store, bars).revert(batch_id=done.batch_id, now=NOW)
    assert store.calls == snapshot


async def test_a_call_already_on_its_own_bar_is_left_alone() -> None:
    right = _call("1.1030")
    plan = await _service(_Store([right]), [_bar(H, "1.1030")]).plan(now=NOW)
    assert plan.regrades == () and plan.lanes["1h"].unchanged == 1


async def test_a_call_without_a_trustworthy_outcome_bar_is_reported_not_guessed() -> None:
    missing = _call("1.0990")
    early = _call("1.0990", horizon=H + timedelta(days=1))
    bars = [
        _bar(H - timedelta(hours=1), "1.0990"),  # only the bar before: no own bar
        _bar(H + timedelta(days=1), "1.1050", stored_at=H + timedelta(days=1, minutes=5)),
    ]
    store = _Store([missing, early])
    plan = await _service(store, bars).plan(now=NOW)
    assert plan.regrades == ()
    assert {pid for pid, _, _ in plan.unavailable} == {missing.id, early.id}
    assert plan.lanes["1h"].unavailable == 2
    assert "not re-gradable" in plan.describe()


async def test_a_weekend_horizon_is_graded_at_the_reopen_like_the_resolver() -> None:
    saturday = datetime(2026, 9, 19, 6, tzinfo=UTC)
    call = _call("1.1001", horizon=saturday)
    bars = [
        _bar(datetime(2026, 9, 18, 20, tzinfo=UTC), "1.1001"),  # Friday's last
        _bar(datetime(2026, 9, 20, 23, tzinfo=UTC), "1.0950"),  # Sunday reopen
    ]
    [g] = (await _service(_Store([call]), bars).plan(now=NOW)).regrades
    assert g.new_close == Decimal("1.0950") and g.new_outcome == 0


async def test_a_call_changed_since_the_plan_is_not_overwritten() -> None:
    call = _call("1.0990")
    store = _Store([call])
    bars = [_bar(H, "1.1030")]
    plan = await _service(store, bars).plan(now=NOW)
    store.calls[call.id] = replace(call, realised_close=Decimal("1.2000"))
    done = await _service(store, bars).apply(plan, now=NOW)
    assert done.changed == 0 and store.calls[call.id].realised_close == Decimal("1.2000")


def test_a_flat_close_is_not_up() -> None:
    assert outcome_of(Decimal("1.1"), Decimal("1.1")) == 0
    assert outcome_of(Decimal("1.1"), Decimal("1.10001")) == 1
