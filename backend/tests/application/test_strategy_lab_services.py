"""Strategy-lab services end to end, on an in-memory store and fixture bars."""

from __future__ import annotations

import json
import uuid
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from mentor.api.v1.strategy_lab import LabResponse
from mentor.application.strategy_lab.evaluation import StrategyLabEvaluator
from mentor.application.strategy_lab.paper import PaperTrader
from mentor.application.strategy_lab.summary import collect_lab_view
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import Timeframe
from mentor.domain.strategy_lab import indicators
from mentor.domain.strategy_lab.library import CandidateDefinition
from mentor.domain.strategy_lab.simulator import Closed, Friction, PlanBook
from mentor.domain.strategy_lab.spec import ExitRules
from mentor.infrastructure.models import StrategyCandidateORM
from tests.application.lab_fakes import MemoryLabStore, loader_for
from tests.domain.strategy_lab.planted import marker_candidate, planted_market

EDGE = planted_market()
END = EDGE.ts[-1] + timedelta(days=1)  # every fixture bar settled
FRICTION = Friction.for_instrument(get_instrument("EURUSD"))


def _evaluator(store: MemoryLabStore, *candidates: CandidateDefinition) -> StrategyLabEvaluator:
    return StrategyLabEvaluator(
        store=store,
        load_bars=loader_for({Timeframe.D1: EDGE}),
        symbol="EURUSD",
        candidates=candidates,
    )


async def test_evaluation_records_every_trial_and_judges_each_candidate_once() -> None:
    store = MemoryLabStore()
    edge = marker_candidate("planted_d1")
    outcome = await _evaluator(store, edge).evaluate_pending(now=END)
    assert outcome.evaluated == (("planted_d1", True),)
    assert outcome.trials_recorded == 2 and outcome.trials_ever == 2
    (row,) = store.candidates
    assert row.status == "paper" and row.paper_started_at == END
    plan = json.loads(row.plan_json or "{}")
    assert plan["config_key"].startswith("planted_d1|") and plan["plan"]
    evidence = json.loads(row.evidence_json)
    assert evidence["passed"] is True and evidence["n_trials"] == 2
    assert "trades" not in json.dumps(evidence["out_of_sample"])  # aggregates, not a trade list
    assert [e.kind for e in store.events] == ["paper"]

    again = await _evaluator(store, edge).evaluate_pending(now=END + timedelta(days=7))
    assert again.evaluated == () and len(store.trials) == 2 and len(store.candidates) == 1


async def test_a_batch_is_graded_against_the_same_bar() -> None:
    store = MemoryLabStore()
    await _evaluator(
        store, marker_candidate("first_d1"), marker_candidate("second_d1")
    ).evaluate_pending(now=END)
    assert {c.n_trials_at_evaluation for c in store.candidates} == {4}


async def test_an_edited_definition_is_reported_not_retested() -> None:
    store = MemoryLabStore()
    original = marker_candidate("planted_d1")
    await _evaluator(store, original).evaluate_pending(now=END)
    edited = replace(
        original, grid=((original.grid[0][0], ExitRules(stop_atr=3.0, target_r=1.0, max_bars=5)),)
    )
    outcome = await _evaluator(store, edited).evaluate_pending(now=END)
    assert outcome.changed == ("planted_d1",) and outcome.evaluated == ()
    assert len(store.trials) == 2


async def test_insufficient_history_is_rejected_with_its_trials_counted() -> None:
    store = MemoryLabStore()
    short = EDGE.window(len(EDGE) - 300)
    evaluator = StrategyLabEvaluator(
        store=store,
        load_bars=loader_for({Timeframe.D1: short}),
        symbol="EURUSD",
        candidates=[marker_candidate()],
    )
    outcome = await evaluator.evaluate_pending(now=END)
    assert outcome.evaluated == (("test_marker_d1", False),)
    assert store.candidates[0].status == "rejected" and len(store.trials) == 2
    assert store.candidates[0].plan_json is None


def _paper_row(definition: CandidateDefinition, started: datetime) -> StrategyCandidateORM:
    spec = definition.specs()[0]
    return StrategyCandidateORM(
        id=uuid.uuid4(),
        key=definition.key,
        family=definition.family,
        timeframe=definition.timeframe.value,
        title=definition.title,
        hypothesis=definition.hypothesis,
        fingerprint=definition.fingerprint(),
        status="paper",
        status_reason="passed",
        evaluated_at=started,
        n_trials_at_evaluation=2,
        plan_json=json.dumps(
            {"config_key": definition.config_key(spec), "params": spec.params(), "plan": "p"}
        ),
        evidence_json=json.dumps({"passed": True, "score": 9.0, "bar": 2.5}),
        paper_started_at=started,
        last_bar_ts=None,
        live_looks=0,
    )


async def _paper_trade(start_index: int, step: timedelta) -> tuple[MemoryLabStore, list[str]]:
    definition = marker_candidate("planted_d1")
    store = MemoryLabStore()
    now = EDGE.ts[start_index] + timedelta(days=1)
    store.candidates.append(_paper_row(definition, now))
    trader = PaperTrader(
        store=store,
        load_bars=loader_for({Timeframe.D1: EDGE}),
        symbol="EURUSD",
        candidates=[definition],
    )
    alerts: list[str] = []
    while now <= END:
        for update in await trader.advance(now=now):
            if update.alert:
                alerts.append(update.alert)
        now += step
    return store, alerts


def _expected_from(start_index: int) -> list[tuple[datetime, datetime, float]]:
    """The back-test of the same plan, starting flat at the paper start line."""
    spec = marker_candidate("planted_d1").specs()[0]
    signals = spec.rule.signals(EDGE)
    atrs = indicators.atr(EDGE.high, EDGE.low, EDGE.close, spec.exits.atr_period)
    book = PlanBook()
    out = []
    for i in range(start_index + 1, len(EDGE)):
        for e in book.on_bar(
            EDGE, i, signal=signals[i], atr=atrs[i], exits=spec.exits, friction=FRICTION
        ):
            if isinstance(e, Closed):
                out.append((e.trade.entry_ts, e.trade.exit_ts, e.trade.r))
    return out


async def test_paper_trading_is_the_backtested_plan_meeting_the_future() -> None:
    start = 3000
    store, _ = await _paper_trade(start, timedelta(days=3))
    closed = sorted(
        (p for p in store.positions_ if p.status == "closed"), key=lambda p: p.signal_ts
    )
    expected = _expected_from(start)
    assert len(closed) == len(expected) > 30
    for p, (entry, exit_, r) in zip(closed, expected, strict=True):
        assert (p.entry_ts, p.exit_ts) == (entry, exit_)
        assert float(p.realised_r or 0) == pytest.approx(r, abs=1e-3)
        assert p.suggested_lots is not None and p.suggested_lots > 0
    assert all(p.signal_ts > EDGE.ts[start] for p in store.positions_), "never back-filled"


async def test_paper_runs_are_idempotent() -> None:
    store, _ = await _paper_trade(3000, timedelta(days=5))
    trader = PaperTrader(
        store=store,
        load_bars=loader_for({Timeframe.D1: EDGE}),
        symbol="EURUSD",
        candidates=[marker_candidate("planted_d1")],
    )
    before = [(p.status, p.signal_ts, p.realised_r) for p in store.positions_]
    await trader.advance(now=END)
    await trader.advance(now=END)
    assert [(p.status, p.signal_ts, p.realised_r) for p in store.positions_] == before


async def test_a_plan_that_proves_itself_live_is_promoted_and_the_owner_told() -> None:
    store, alerts = await _paper_trade(600, timedelta(days=7))
    kinds = [e.kind for e in store.events]
    assert "promoted" in kinds
    assert any("📈" in a and "paper trading only" in a for a in alerts)
    row = store.candidates[0]
    assert row.live_looks >= 1 and row.promoted_at is not None


async def test_the_lab_view_and_api_schema_agree() -> None:
    store, _ = await _paper_trade(3000, timedelta(days=7))
    waiting = marker_candidate("not_yet_d1")
    view = await collect_lab_view(
        store, now=END, candidates=[marker_candidate("planted_d1"), waiting]
    )
    assert view.waiting == ("not_yet_d1",)
    (c,) = view.candidates
    assert c.paper is not None and c.paper.trades > 30
    assert c.paper.breakeven_win_rate is not None
    counts = view.to_dict()["counts"]
    assert isinstance(counts, dict) and counts["evaluated"] == 1
    LabResponse.model_validate(view.to_dict())
    retitled = replace(marker_candidate("planted_d1"), title="A new name changes nothing")
    assert (await collect_lab_view(store, now=END, candidates=[retitled])).changed == ()
    regridded = replace(retitled, grid=retitled.grid[:1])
    view2 = await collect_lab_view(store, now=END, candidates=[regridded])
    assert view2.changed == ("planted_d1",)

