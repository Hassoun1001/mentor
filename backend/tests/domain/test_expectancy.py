"""Expectancy and R-multiple tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.money import Money, Percent
from mentor.domain.risk import expectancy, r_multiple


class TestExpectancy:
    def test_classic_40_percent_win_2to1(self) -> None:
        """A 40%-win system at 2R wins / 1R losses is positive expectancy.

        E[R] = 0.4 * 2 - 0.6 * 1 = 0.2
        """
        result = expectancy(
            win_rate=Percent.from_percent(40),
            avg_win_r="2",
            avg_loss_r="1",
        )
        assert result.expected_value_r == Decimal("0.2")
        assert result.is_positive
        assert result.profit_factor == Decimal("0.8") / Decimal("0.6")

    def test_break_even(self) -> None:
        result = expectancy(
            win_rate=Percent.from_percent(50),
            avg_win_r="1",
            avg_loss_r="1",
        )
        assert result.expected_value_r == Decimal("0")
        assert not result.is_positive

    def test_negative_expectancy(self) -> None:
        result = expectancy(
            win_rate=Percent.from_percent(50),
            avg_win_r="1",
            avg_loss_r="2",
        )
        assert result.expected_value_r == Decimal("-0.5")

    def test_no_losses_profit_factor_none(self) -> None:
        result = expectancy(
            win_rate=Percent.from_percent(100),
            avg_win_r="1",
            avg_loss_r="0",
        )
        assert result.profit_factor is None

    def test_rejects_negative_avg_win(self) -> None:
        with pytest.raises(ValidationError):
            expectancy(
                win_rate=Percent.from_percent(50),
                avg_win_r="-1",
                avg_loss_r="1",
            )


class TestRMultiple:
    def test_two_R_win(self) -> None:
        r = r_multiple(
            entry=Money.of("100", "USD"),
            exit_=Money.of("200", "USD"),
            initial_risk=Money.of("50", "USD"),
        )
        assert r == Decimal("2")

    def test_full_R_loss(self) -> None:
        r = r_multiple(
            entry=Money.of("100", "USD"),
            exit_=Money.of("50", "USD"),
            initial_risk=Money.of("50", "USD"),
        )
        assert r == Decimal("-1")

    def test_currency_mismatch_rejected(self) -> None:
        with pytest.raises(ValidationError):
            r_multiple(
                entry=Money.of("100", "USD"),
                exit_=Money.of("100", "EUR"),
                initial_risk=Money.of("50", "USD"),
            )
