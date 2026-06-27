"""Decimal-backed value objects for money and quantities.

Everything that touches money uses `Decimal` and an explicit currency. Floats
are forbidden in this layer — silent precision loss has wrecked production
trading systems before and the cost is a few keystrokes here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Final, Self

from mentor.domain.errors import ValidationError

_TWO_PLACES: Final[Decimal] = Decimal("0.01")


def to_decimal(value: Decimal | int | str | float, *, field: str | None = None) -> Decimal:
    """Coerce to Decimal, rejecting non-finite values.

    Floats are accepted *only* via string round-trip so the binary
    representation noise (`0.1 + 0.2`) cannot leak into pricing logic.
    """
    try:
        if isinstance(value, Decimal):
            result = value
        elif isinstance(value, float):
            result = Decimal(str(value))
        else:
            result = Decimal(value)
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise ValidationError(f"not a valid decimal: {value!r}", field=field) from exc

    if not result.is_finite():
        raise ValidationError(f"value must be finite, got {value!r}", field=field)
    return result


def quantize_money(amount: Decimal) -> Decimal:
    """Round to two decimal places using banker-safe HALF_UP."""
    return amount.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """An amount of money in a specific currency."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        # Reject NaN/Inf on direct construction (Money.of already coerces
        # via to_decimal; this guards Money(Decimal(...), ...) call sites).
        if not self.amount.is_finite():
            raise ValidationError("amount must be finite", field="amount")
        if not self.currency or len(self.currency) != 3 or not self.currency.isalpha():
            raise ValidationError("currency must be a 3-letter ISO code", field="currency")
        object.__setattr__(self, "currency", self.currency.upper())

    @classmethod
    def of(cls, amount: Decimal | int | str | float, currency: str) -> Self:
        return cls(to_decimal(amount, field="amount"), currency)

    def _check_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValidationError(
                f"currency mismatch: {self.currency} vs {other.currency}",
                field="currency",
            )

    def __add__(self, other: Money) -> Money:
        self._check_same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check_same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal | int) -> Money:
        return Money(self.amount * to_decimal(factor, field="factor"), self.currency)

    __rmul__ = __mul__

    def quantized(self) -> Money:
        return Money(quantize_money(self.amount), self.currency)

    @property
    def is_positive(self) -> bool:
        return self.amount > 0

    @property
    def is_negative(self) -> bool:
        return self.amount < 0


@dataclass(frozen=True, slots=True)
class Percent:
    """A percentage expressed as a Decimal (0.01 == 1%)."""

    fraction: Decimal

    def __post_init__(self) -> None:
        f = to_decimal(self.fraction, field="fraction")
        if f < 0 or f > Decimal("1"):
            raise ValidationError(
                f"percent must be in [0, 1], got {f}",
                field="fraction",
            )
        object.__setattr__(self, "fraction", f)

    @classmethod
    def from_percent(cls, value: Decimal | int | str | float) -> Percent:
        return cls(to_decimal(value, field="percent") / Decimal("100"))

    def of(self, amount: Money) -> Money:
        return Money(amount.amount * self.fraction, amount.currency)

    @property
    def as_percent(self) -> Decimal:
        return self.fraction * Decimal("100")


def round_down_to_step(value: Decimal, step: Decimal, minimum: Decimal) -> Decimal:
    """Round `value` *down* to the nearest `step`, clamped at `minimum`.

    Used to round raw lot sizes to the broker's permitted increment. We round
    down (never up) because the position-size calculation is a *maximum*: a
    larger lot would exceed the user's risk budget.
    """
    if step <= 0:
        raise ValidationError("step must be positive", field="step")
    if value < minimum:
        return Decimal("0")
    steps = (value / step).quantize(Decimal("1"), rounding=ROUND_DOWN)
    rounded = steps * step
    if rounded < minimum:
        return Decimal("0")
    return rounded
