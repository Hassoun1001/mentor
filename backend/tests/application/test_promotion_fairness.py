"""Promotion fairness tests — fair champion re-grade + candidate family.

Uses synthetic bars (sine + seeded noise so both label classes occur) and a
fake price repository, so no DB is needed. Training a small HGB on ~500
samples is fast enough for the unit suite.
"""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from mentor.application.forecasting.promotion import PromotionService
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.sklearn_forecaster import (
    evaluate_forecaster_on_tail,
    train_sklearn_forecaster,
)

_HORIZON = 24


def _bars(n: int = 500) -> list[PriceBar]:
    rng = random.Random(7)
    start = datetime(2025, 1, 1, tzinfo=UTC)
    out: list[PriceBar] = []
    for i in range(n):
        px = 1.10 + 0.01 * math.sin(i / 20) + rng.uniform(-0.002, 0.002)
        p = Decimal(f"{px:.5f}")
        out.append(
            PriceBar(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                ts=start + timedelta(hours=i),
                open=p,
                high=p + Decimal("0.0010"),
                low=p - Decimal("0.0010"),
                close=p,
                volume=Decimal("100"),
                source="test",
            )
        )
    return out


class _FakePriceRepo:
    """Just enough of PriceBarRepository for retrain_and_promote."""

    def __init__(self, bars: list[PriceBar]) -> None:
        self._bars = bars

    async def range(self, *, symbol: str, timeframe: Timeframe, start: datetime, end: datetime):  # type: ignore[no-untyped-def]
        return [
            SimpleNamespace(
                symbol=b.symbol,
                timeframe=b.timeframe.value,
                ts=b.ts,
                open=str(b.open),
                high=str(b.high),
                low=str(b.low),
                close=str(b.close),
                volume=str(b.volume),
                source=b.source,
            )
            for b in self._bars
        ]


def test_evaluate_on_tail_matches_training_report() -> None:
    """Grading a model on the same tail it was tested on must reproduce
    the trainer's own Brier — proof the fair gate compares like with like."""
    bars = _bars()
    model = train_sklearn_forecaster(bars=bars, horizon_bars=_HORIZON)
    brier = evaluate_forecaster_on_tail(model, bars=bars, horizon_bars=_HORIZON)
    assert brier is not None
    assert brier == pytest.approx(model.report.test_brier, rel=1e-9)


def test_evaluate_on_tail_returns_none_when_history_too_short() -> None:
    bars = _bars(120)  # under the 100-sample floor after labelling
    model = train_sklearn_forecaster(bars=_bars(), horizon_bars=_HORIZON)
    assert evaluate_forecaster_on_tail(model, bars=bars, horizon_bars=_HORIZON) is None


async def test_first_retrain_installs_champion_with_family_audit(tmp_path: Path) -> None:
    service = PromotionService(model_store_dir=tmp_path, prices=_FakePriceRepo(_bars()))  # type: ignore[arg-type]
    result = await service.retrain_and_promote(
        symbol="EURUSD", timeframe=Timeframe.H1, horizon_bars=_HORIZON
    )
    assert result.promoted is True
    assert result.champion_name is None
    # No news/macro repos → the family is one of the technical-side configs,
    # chosen by walk-forward selection across pre-tail folds.
    assert result.challenger_family in {"technical", "regularized", "pruned"}
    # The audit carries every fold score plus the winner's final tail Brier.
    assert len(result.candidate_briers) >= 2
    assert any(k.endswith("(final)") for k in result.candidate_briers)
    champion = service.current_champion()
    assert champion is not None
    assert champion["model_name"] == result.challenger_name
    assert champion["feature_family"] == result.challenger_family


async def test_second_retrain_regrades_champion_on_fresh_window(tmp_path: Path) -> None:
    """The gate must use the fresh re-grade (champion_brier_fresh set), and
    the champion pointer must match the decision it recorded. Note: the
    second retrain may legitimately promote — its pruned candidate consumes
    the FIRST retrain's lesson, so the two runs are no longer identical.
    That's the feedback loop working, and the invariants below hold either
    way."""
    service = PromotionService(model_store_dir=tmp_path, prices=_FakePriceRepo(_bars()))  # type: ignore[arg-type]
    first = await service.retrain_and_promote(
        symbol="EURUSD", timeframe=Timeframe.H1, horizon_bars=_HORIZON
    )
    second = await service.retrain_and_promote(
        symbol="EURUSD", timeframe=Timeframe.H1, horizon_bars=_HORIZON
    )
    assert second.champion_name == first.challenger_name
    assert second.champion_brier_fresh is not None  # fair gate exercised
    assert second.champion_brier == pytest.approx(second.champion_brier_fresh)
    # Decision consistency: promotion iff margin AND floor were both cleared.
    improvement = second.champion_brier - second.challenger_brier
    should_promote = improvement >= 0.002 and second.challenger_brier <= 0.248
    assert second.promoted is should_promote
    champion = service.current_champion()
    assert champion is not None
    expected_champion = second.challenger_name if second.promoted else first.challenger_name
    assert champion["model_name"] == expected_champion
    # Every decision lands in the durable audit + lessons logs, newest first.
    assert len(service.promotion_history()) == 2
    lessons = service.lessons_history()
    assert len(lessons) == 2
    assert "importances" in lessons[0] and "selection" in lessons[0]
