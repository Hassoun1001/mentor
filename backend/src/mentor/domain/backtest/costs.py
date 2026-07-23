"""Transaction-cost model.

> Full spread/slippage/commission modelling in every backtest.
> — Mentor product plan, §15 (risk register)

The plan calls out three components separately so each can be tuned
against the user's broker:

- **Spread** — distance between bid and ask. Paid on entry *and* exit
  for a round trip.
- **Commission** — fixed per-lot cost.
- **Slippage** — the gap between expected and actual fill, modelled as
  additional pips on entry and exit.

The model returns:
- the *worsening* of the fill price (in price units) on entry/exit
- the cash commission on a round trip
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.money import to_decimal
from mentor.domain.risk.position_sizing import Direction


@dataclass(frozen=True, slots=True)
class CostModel:
    spread_pips: Decimal = Decimal("0.8")
    slippage_pips: Decimal = Decimal("0.2")
    commission_per_lot_round_trip: Decimal = Decimal("0")  # in account currency

    def __post_init__(self) -> None:
        for name, raw in (
            ("spread_pips", self.spread_pips),
            ("slippage_pips", self.slippage_pips),
            ("commission_per_lot_round_trip", self.commission_per_lot_round_trip),
        ):
            d = to_decimal(raw, field=name)
            if d < 0:
                raise ValidationError(f"{name} must be >= 0", field=name)
            object.__setattr__(self, name, d)

    def entry_fill_price(
        self, *, direction: Direction, raw_price: Decimal, instrument: Instrument
    ) -> Decimal:
        """Adjust raw price to a realistic entry fill.

        Long: pay half spread + slippage *above* the quoted price.
        Short: receive half spread + slippage *below* the quoted price.
        """
        pip = instrument.pip_size
        worsen = (self.spread_pips / Decimal("2") + self.slippage_pips) * pip
        return raw_price + worsen if direction is Direction.LONG else raw_price - worsen

    def exit_fill_price(
        self, *, direction: Direction, raw_price: Decimal, instrument: Instrument
    ) -> Decimal:
        """Adjust raw price to a realistic exit fill.

        Long: sell at half spread + slippage *below* the quoted price.
        Short: buy back at half spread + slippage *above* the quoted price.
        """
        pip = instrument.pip_size
        worsen = (self.spread_pips / Decimal("2") + self.slippage_pips) * pip
        return raw_price - worsen if direction is Direction.LONG else raw_price + worsen

    def commission_for(self, lots: Decimal) -> Decimal:
        return lots * self.commission_per_lot_round_trip

    def friction_for(self, lots: Decimal, instrument: Instrument) -> Decimal:
        """What the spread and slippage cost this round trip, in money.

        Entry and exit fills are each worsened by half the spread plus
        slippage, so a round trip pays ``spread + 2 x slippage`` in pips.
        That charge is real — it is inside the fill prices — but it was
        invisible: ``total_costs_paid`` accumulated commission only, which
        defaults to zero. A backtest reporting "total costs: 0.00" while
        quietly charging a pip and a bit per trade tells the reader the
        opposite of the truth.
        """
        per_trip_pips = self.spread_pips + Decimal("2") * self.slippage_pips
        units = lots * instrument.contract_size
        return per_trip_pips * instrument.pip_size * units
