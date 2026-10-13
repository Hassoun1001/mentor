"""The honesty gates, pinned.

These numbers decide whether the system is allowed to believe itself: how
much better a model must be to ship, the cost hurdle it must clear, how many
independent results a verdict needs, how long a positioning report must wait
before the model may see it. Loosening any of them makes every metric look
better and the system worse — the one "improvement" an automated maintainer
must never make.

They change only by hand. The server's deploy script refuses a commit that
edits their definitions or this file; this test catches the same change
before it is ever pushed.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.application.forecasting import promotion
from mentor.application.scheduler import drift
from mentor.domain.backtest.costs import CostModel
from mentor.domain.forecasting import live_recalibration, selective
from mentor.domain.risk import position_sizing
from mentor.domain.stats import breakeven, significance
from mentor.domain.strategy_lab import deflation, gate, live
from mentor.infrastructure.adapters.macro import cftc_cot


def test_promotion_gate() -> None:
    assert promotion._PROMOTION_MARGIN == 0.002
    assert promotion._COIN_FLIP_BRIER == 0.25
    assert promotion._BASELINE_FLOOR == 0.25 - 0.002
    assert promotion._MIN_COVERAGE == 0.15
    assert promotion._DEMOTION_AFTER == 3
    assert promotion._SELECTION_FOLDS == (0.64, 0.80)


def test_evidence_floors() -> None:
    assert significance.MIN_SAMPLE_FOR_VERDICT == 30
    assert significance._Z == 1.959963984540054  # 95% two-sided
    assert breakeven.MIN_WINDOWS == 30
    assert breakeven._MAX_BREAKEVEN == 0.95
    assert breakeven._COIN_FLIP == 0.5
    assert drift._COIN_FLIP_BRIER == 0.25


def test_noise_guards() -> None:
    assert selective.MIN_COVERAGE == 0.15
    assert selective._MIN_GAIN == 0.002
    assert live_recalibration._MIN_GAIN == 0.002


def test_trading_costs_are_not_wished_away() -> None:
    model = CostModel()
    assert model.spread_pips == Decimal("0.8")
    assert model.slippage_pips == Decimal("0.2")


def test_point_in_time_lag() -> None:
    assert timedelta(days=4) == cftc_cot._PUBLICATION_LAG


def test_risk_guards() -> None:
    assert Decimal("3") == position_sizing._MIN_SENSIBLE_STOP_PIPS
    assert Decimal("100") == position_sizing._EXTREME_LEVERAGE


def test_strategy_lab_gate() -> None:
    assert gate._WALK_FORWARD_FOLDS == 4
    assert gate._MIN_SELECTION_TRADES == 10
    assert gate._HOLDOUT_MIN_TRADES == 10
    assert datetime(2024, 1, 1, tzinfo=UTC) == gate._HOLDOUT_START_D1
    assert datetime(2026, 4, 1, tzinfo=UTC) == gate._HOLDOUT_START_H1
    assert deflation._MIN_SHARPE_DENOMINATOR == 1.0
    assert deflation._Z is significance._Z
    assert live._LIVE_CHECKPOINT == significance.MIN_SAMPLE_FOR_VERDICT == 30
