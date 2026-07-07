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
    # No news/macro repos → the family is technical-only, and audited as such.
    assert result.challenger_family == "technical"
    assert set(result.candidate_briers) == {"technical"}
    champion = service.current_champion()
    assert champion is not None
    assert champion["model_name"] == result.challenger_name
    assert champion["feature_family"] == "technical"


async def test_second_retrain_regrades_champion_on_fresh_window(tmp_path: Path) -> None:
    """Same data + same seed → identical challenger, so improvement is ~0 and
    the champion must be kept. Crucially the gate must have used the fresh
    re-grade (champion_brier_fresh set), not the stale stored number."""
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
    assert second.promoted is False  # identical model can't clear the margin
    champion = service.current_champion()
    assert champion is not None
    assert champion["model_name"] == first.challenger_name  # a worse model never ships
    # Every decision lands in the durable audit log, newest first.
    history = service.promotion_history()
    assert len(history) == 2
    assert history[0]["promoted"] is False
    assert history[1]["promoted"] is True
    assert history[1]["challenger"] == first.challenger_name
