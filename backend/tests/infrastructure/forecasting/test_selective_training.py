"""Abstention as it comes out of a real trained model and the promotion gate."""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.sklearn_forecaster import (
    TrainingReport,
    evaluate_policy_on_tail,
    train_sklearn_forecaster,
)

_HORIZON = 24


def _bars(n: int = 600) -> list[PriceBar]:
    rng = random.Random(11)
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


# ---------- report semantics ----------


def test_a_model_that_never_abstains_reports_its_all_hours_brier() -> None:
    r = TrainingReport(
        n_samples=100,
        n_train=60,
        n_test=20,
        train_accuracy=0.6,
        test_accuracy=0.55,
        test_log_loss=0.69,
        test_brier=0.24,
        horizon_bars=_HORIZON,
    )
    assert not r.abstains
    assert r.effective_brier == 0.24


def test_legacy_metadata_defaults_do_not_fake_a_perfect_score() -> None:
    # A model trained before abstention existed carries zeros. If the gate
    # read test_brier_covered directly it would see 0.0 and promote garbage.
    legacy = TrainingReport(
        n_samples=100,
        n_train=60,
        n_test=20,
        train_accuracy=0.6,
        test_accuracy=0.55,
        test_log_loss=0.69,
        test_brier=0.30,
        horizon_bars=_HORIZON,
    )
    assert legacy.test_brier_covered == 0.0
    assert legacy.effective_brier == 0.30  # falls back, does not look perfect


def test_an_abstaining_model_competes_on_its_covered_score() -> None:
    r = TrainingReport(
        n_samples=100,
        n_train=60,
        n_test=20,
        train_accuracy=0.6,
        test_accuracy=0.55,
        test_log_loss=0.69,
        test_brier=0.26,
        horizon_bars=_HORIZON,
        abstain_margin=0.05,
        coverage=0.4,
        n_covered=8,
        test_brier_covered=0.22,
    )
    assert r.abstains
    assert r.effective_brier == 0.22


# ---------- the trainer ----------


def test_training_produces_a_coherent_policy() -> None:
    model = train_sklearn_forecaster(bars=_bars(), horizon_bars=_HORIZON)
    r = model.report

    assert r.abstain_margin >= 0.0
    assert 0.0 <= r.coverage <= 1.0
    assert model.abstain_margin == r.abstain_margin
    if r.abstains:
        # Coverage and the covered count must agree with each other.
        assert r.n_covered > 0
        assert r.n_covered <= r.n_test
        assert 0.0 <= r.test_accuracy_covered <= 1.0
    else:
        assert r.effective_brier == r.test_brier


def test_regrading_honours_the_models_own_margin() -> None:
    bars = _bars()
    model = train_sklearn_forecaster(bars=bars, horizon_bars=_HORIZON)
    policy = evaluate_policy_on_tail(model, bars=bars, horizon_bars=_HORIZON)

    assert policy is not None
    assert policy.margin == model.abstain_margin
    assert policy.n_covered <= policy.n_total


def test_regrade_returns_none_on_a_tail_too_small_to_judge() -> None:
    model = train_sklearn_forecaster(bars=_bars(), horizon_bars=_HORIZON)
    assert evaluate_policy_on_tail(model, bars=_bars(120), horizon_bars=_HORIZON) is None
