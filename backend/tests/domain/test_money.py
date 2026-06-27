"""Tests for the money value objects."""

from __future__ import annotations

from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.money import Money, Percent, round_down_to_step, to_decimal


class TestToDecimal:
    def test_accepts_string(self) -> None:
        assert to_decimal("1.23") == Decimal("1.23")

    def test_float_round_trips_via_string(self) -> None:
        assert to_decimal(0.1) == Decimal("0.1")

    def test_rejects_nan(self) -> None:
        with pytest.raises(ValidationError):
            to_decimal(float("nan"))

    def test_rejects_inf(self) -> None:
        with pytest.raises(ValidationError):
            to_decimal(float("inf"))


class TestMoney:
    def test_addition_preserves_currency(self) -> None:
        result = Money.of("100", "USD") + Money.of("50", "USD")
        assert result == Money(Decimal("150"), "USD")

    def test_addition_rejects_currency_mismatch(self) -> None:
        with pytest.raises(ValidationError):
            _ = Money.of("100", "USD") + Money.of("50", "EUR")

    def test_currency_normalised_to_upper(self) -> None:
        assert Money.of("1", "usd").currency == "USD"

    def test_invalid_currency_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Money.of("1", "US")


class TestPercent:
    def test_from_percent(self) -> None:
        assert Percent.from_percent(2).fraction == Decimal("0.02")

    def test_of_money(self) -> None:
        assert Percent.from_percent(1).of(Money.of("10000", "USD")).amount == Decimal("100")

    def test_rejects_over_100(self) -> None:
        with pytest.raises(ValidationError):
            Percent(Decimal("1.5"))


class TestRoundDownToStep:
    def test_rounds_down(self) -> None:
        assert round_down_to_step(Decimal("0.137"), Decimal("0.01"), Decimal("0.01")) == Decimal(
            "0.13"
        )

    def test_below_minimum_returns_zero(self) -> None:
        assert round_down_to_step(Decimal("0.005"), Decimal("0.01"), Decimal("0.01")) == Decimal(
            "0"
        )

    def test_exact_step_preserved(self) -> None:
        assert round_down_to_step(Decimal("1.00"), Decimal("0.01"), Decimal("0.01")) == Decimal(
            "1.00"
        )
