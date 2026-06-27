"""Risk-of-ruin simulator tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.risk.monte_carlo import simulate_risk_of_ruin


def test_negative_expectancy_pool_has_high_ruin_probability() -> None:
    """A pool dominated by losers and risking 5% per trade for 200
    trades should ruin the account in most paths."""
    pool = [Decimal("-1"), Decimal("-1"), Decimal("-1"), Decimal("0.5")]
    result = simulate_risk_of_ruin(
        r_distribution=pool,
        starting_balance=Decimal("10000"),
        risk_per_trade_fraction=Decimal("0.05"),
        n_trades=200,
        n_runs=400,
        seed=1,
    )
    assert result.probability_of_ruin > Decimal("0.9")


def test_strong_positive_pool_almost_never_ruins_at_one_pct() -> None:
    pool = [Decimal("2"), Decimal("2"), Decimal("-1")]  # +1.0 per trade EV
    result = simulate_risk_of_ruin(
        r_distribution=pool,
        starting_balance=Decimal("10000"),
        risk_per_trade_fraction=Decimal("0.01"),
        n_trades=200,
        n_runs=300,
        seed=1,
    )
    assert result.probability_of_ruin < Decimal("0.05")
    assert result.median_terminal > Decimal("10000")


def test_rejects_empty_distribution() -> None:
    with pytest.raises(ValidationError):
        simulate_risk_of_ruin(
            r_distribution=[],
            starting_balance=Decimal("10000"),
            risk_per_trade_fraction=Decimal("0.01"),
            n_trades=100,
        )


def test_rejects_excessive_risk() -> None:
    with pytest.raises(ValidationError):
        simulate_risk_of_ruin(
            r_distribution=[Decimal("1")],
            starting_balance=Decimal("10000"),
            risk_per_trade_fraction=Decimal("0.5"),  # 50% — refused
            n_trades=100,
        )


def test_reproducible_with_seed() -> None:
    a = simulate_risk_of_ruin(
        r_distribution=[Decimal("1"), Decimal("-1")],
        starting_balance=Decimal("10000"),
        risk_per_trade_fraction=Decimal("0.02"),
        n_trades=100,
        n_runs=200,
        seed=99,
    )
    b = simulate_risk_of_ruin(
        r_distribution=[Decimal("1"), Decimal("-1")],
        starting_balance=Decimal("10000"),
        risk_per_trade_fraction=Decimal("0.02"),
        n_trades=100,
        n_runs=200,
        seed=99,
    )
    assert a.probability_of_ruin == b.probability_of_ruin
    assert a.median_terminal == b.median_terminal
