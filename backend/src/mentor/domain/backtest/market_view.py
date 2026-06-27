"""Point-in-time market view.

The single most important invariant in the backtester: a strategy
evaluated at bar *i* must not see bars *i+1*, *i+2*, … under any
circumstance. We make that **structural**, not a convention.

The full bar series is stored in a private tuple; the public API exposes
only the slice up to the current index. There is no `next()` method,
no `forward(n)` helper, no "future" attribute. A typo can't reach a
future bar — there is no path to the data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar


@dataclass(frozen=True, slots=True)
class MarketView:
    _bars: tuple[PriceBar, ...]
    _current_index: int

    def __post_init__(self) -> None:
        if not self._bars:
            raise ValidationError("MarketView requires at least one bar")
        if not (0 <= self._current_index < len(self._bars)):
            raise ValidationError(
                f"current_index out of range: {self._current_index} not in [0, {len(self._bars)})"
            )

    # --- size --------------------------------------------------------------

    @property
    def visible_count(self) -> int:
        """Number of bars visible to the strategy (current + history)."""
        return self._current_index + 1

    # --- accessors --------------------------------------------------------

    @property
    def current(self) -> PriceBar:
        return self._bars[self._current_index]

    @property
    def now(self) -> datetime:
        return self.current.ts

    @property
    def current_close(self) -> Decimal:
        return self.current.close

    def previous(self, n: int = 1) -> PriceBar | None:
        """Return the bar `n` steps before the current bar, or `None`."""
        if n < 1:
            raise ValidationError("n must be >= 1", field="n")
        idx = self._current_index - n
        return self._bars[idx] if idx >= 0 else None

    def history(self, lookback: int) -> tuple[PriceBar, ...]:
        """Return up to `lookback` bars *ending at and including* the current bar."""
        if lookback < 1:
            raise ValidationError("lookback must be >= 1", field="lookback")
        start = max(0, self._current_index - lookback + 1)
        return self._bars[start : self._current_index + 1]

    def closes(self, lookback: int) -> tuple[Decimal, ...]:
        return tuple(b.close for b in self.history(lookback))

    def highs(self, lookback: int) -> tuple[Decimal, ...]:
        return tuple(b.high for b in self.history(lookback))

    def lows(self, lookback: int) -> tuple[Decimal, ...]:
        return tuple(b.low for b in self.history(lookback))
