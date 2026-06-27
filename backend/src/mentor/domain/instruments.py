"""Tradable instrument definitions.

Per the plan the instrument is configuration, not hard-coded. EUR/USD is the
reference build; the same code path serves any forex pair, and the model can
extend to equities later by parameterising mechanics (contract size, pip
size) rather than by branching.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from mentor.domain.errors import ValidationError
from mentor.domain.money import to_decimal


@dataclass(frozen=True, slots=True)
class Instrument:
    """An instrument's static trading mechanics.

    Attributes
    ----------
    symbol:
        Canonical symbol, e.g. "EURUSD".
    base, quote:
        ISO currency codes for the two legs of the pair.
    pip_size:
        Smallest standard price increment. `0.0001` for most FX majors,
        `0.01` for JPY-quoted pairs.
    contract_size:
        Units of base currency per standard lot. Forex convention: 100,000.
    min_lot, lot_step:
        Broker-permitted minimum size and increment. Mainstream retail
        defaults: 0.01 minimum, 0.01 step (one micro lot).
    """

    symbol: str
    base: str
    quote: str
    pip_size: Decimal
    contract_size: Decimal
    min_lot: Decimal
    lot_step: Decimal

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValidationError("symbol required", field="symbol")
        for code, field in ((self.base, "base"), (self.quote, "quote")):
            if not code or len(code) != 3 or not code.isalpha():
                raise ValidationError(f"{field} must be a 3-letter ISO code", field=field)
        for name, value in (
            ("pip_size", self.pip_size),
            ("contract_size", self.contract_size),
            ("min_lot", self.min_lot),
            ("lot_step", self.lot_step),
        ):
            d = to_decimal(value, field=name)
            if d <= 0:
                raise ValidationError(f"{name} must be positive", field=name)
            object.__setattr__(self, name, d)

        object.__setattr__(self, "symbol", self.symbol.upper())
        object.__setattr__(self, "base", self.base.upper())
        object.__setattr__(self, "quote", self.quote.upper())

    def pips_between(self, a: Decimal, b: Decimal) -> Decimal:
        return abs(to_decimal(a, field="a") - to_decimal(b, field="b")) / self.pip_size

    def pip_value_per_lot_in_quote(self, lots: Decimal = Decimal("1")) -> Decimal:
        """Value of one pip in the **quote** currency for the given lot size."""
        return to_decimal(lots, field="lots") * self.contract_size * self.pip_size


_FX_MAJOR: Final = {
    "pip_size": Decimal("0.0001"),
    "contract_size": Decimal("100000"),
    "min_lot": Decimal("0.01"),
    "lot_step": Decimal("0.01"),
}
_FX_JPY: Final = {**_FX_MAJOR, "pip_size": Decimal("0.01")}


def _pair(symbol: str, base: str, quote: str, mechanics: dict[str, Decimal]) -> Instrument:
    return Instrument(symbol=symbol, base=base, quote=quote, **mechanics)


BUILTIN_INSTRUMENTS: Final[dict[str, Instrument]] = {
    "EURUSD": _pair("EURUSD", "EUR", "USD", _FX_MAJOR),
    "GBPUSD": _pair("GBPUSD", "GBP", "USD", _FX_MAJOR),
    "AUDUSD": _pair("AUDUSD", "AUD", "USD", _FX_MAJOR),
    "USDCHF": _pair("USDCHF", "USD", "CHF", _FX_MAJOR),
    "USDCAD": _pair("USDCAD", "USD", "CAD", _FX_MAJOR),
    "USDJPY": _pair("USDJPY", "USD", "JPY", _FX_JPY),
    "EURJPY": _pair("EURJPY", "EUR", "JPY", _FX_JPY),
}


def get_instrument(symbol: str) -> Instrument:
    key = symbol.upper().replace("/", "")
    try:
        return BUILTIN_INSTRUMENTS[key]
    except KeyError as exc:
        raise ValidationError(f"unknown instrument: {symbol!r}", field="symbol") from exc
