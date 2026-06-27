"""Position sizing — the heart of the risk engine.

> Sizes trades from account risk %, stop distance, and pip value. The
> foundation, already prototyped.   — Mentor product plan, §6.E

The math, in one place so it can be audited:

    risk_amount       = account_balance * risk_fraction
    stop_distance     = |entry - stop|
    pip_distance      = stop_distance / pip_size
    pip_value_account = contract_size * pip_size * quote_to_account_rate
    raw_lots          = risk_amount / (pip_distance * pip_value_account)
    lots              = round_down(raw_lots, lot_step)

Rounding down (never up) is deliberate: a larger lot would push the trade
*over* the user's stated risk budget. The risk budget is a ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.money import Money, Percent, quantize_money, round_down_to_step, to_decimal

_MAX_RISK_PCT: Decimal = Decimal("0.10")  # 10% per trade — hard ceiling
_RECOMMENDED_RISK_PCT: Decimal = Decimal("0.02")  # the "1–2% rule"


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True, slots=True)
class RiskInputs:
    """Everything the position-size calculator needs.

    `quote_to_account_rate` converts a value in the instrument's *quote*
    currency to the user's *account* currency. For EUR/USD with a USD-
    denominated account this is `1`. For EUR/USD with a EUR-denominated
    account it is `1 / current_EURUSD_price`. Default `1` keeps the common
    case ergonomic; callers must supply it explicitly for cross-currency
    accounts.
    """

    account_balance: Money
    risk: Percent
    entry: Decimal
    stop: Decimal
    instrument: Instrument
    direction: Direction
    target: Decimal | None = None
    quote_to_account_rate: Decimal = Decimal("1")

    def __post_init__(self) -> None:  # noqa: PLR0912 — flat validation guards are clearer than extracted helpers
        if not self.account_balance.is_positive:
            raise ValidationError("account_balance must be positive", field="account_balance")
        if self.risk.fraction <= 0:
            raise ValidationError("risk must be > 0", field="risk")
        if self.risk.fraction > _MAX_RISK_PCT:
            raise ValidationError(
                f"risk per trade capped at {_MAX_RISK_PCT * 100}% — refusing dangerous sizing",
                field="risk",
            )
        for name, raw in (
            ("entry", self.entry),
            ("stop", self.stop),
            ("quote_to_account_rate", self.quote_to_account_rate),
        ):
            d = to_decimal(raw, field=name)
            if d <= 0:
                raise ValidationError(f"{name} must be positive", field=name)
            object.__setattr__(self, name, d)
        if self.target is not None:
            t = to_decimal(self.target, field="target")
            if t <= 0:
                raise ValidationError("target must be positive", field="target")
            object.__setattr__(self, "target", t)

        if self.entry == self.stop:
            raise ValidationError("entry and stop must differ", field="stop")

        if self.direction is Direction.LONG and self.stop >= self.entry:
            raise ValidationError(
                "long stop must be below entry — otherwise the stop is the target",
                field="stop",
            )
        if self.direction is Direction.SHORT and self.stop <= self.entry:
            raise ValidationError(
                "short stop must be above entry — otherwise the stop is the target",
                field="stop",
            )
        if self.target is not None:
            if self.direction is Direction.LONG and self.target <= self.entry:
                raise ValidationError("long target must be above entry", field="target")
            if self.direction is Direction.SHORT and self.target >= self.entry:
                raise ValidationError("short target must be below entry", field="target")


@dataclass(frozen=True, slots=True)
class PositionSizing:
    """The output of the calculator — everything the user needs to act."""

    lots: Decimal
    units: Decimal
    pip_distance: Decimal
    pip_value_in_account: Money
    money_at_risk: Money
    money_at_risk_pct: Percent
    risk_reward_ratio: Decimal | None
    notional_in_quote: Decimal
    raw_lots_before_rounding: Decimal
    is_aggressive: bool
    notes: tuple[str, ...]


def calculate_position(inputs: RiskInputs) -> PositionSizing:
    """Compute the safe maximum position size for a single trade."""
    instr = inputs.instrument
    account_ccy = inputs.account_balance.currency

    risk_money = inputs.risk.of(inputs.account_balance)
    pip_distance = inputs.instrument.pips_between(inputs.entry, inputs.stop)

    # pip value (one standard lot) expressed in the account currency
    pip_value_per_lot_quote = instr.pip_value_per_lot_in_quote(Decimal("1"))
    pip_value_per_lot_account = pip_value_per_lot_quote * inputs.quote_to_account_rate

    denominator = pip_distance * pip_value_per_lot_account
    if denominator <= 0:
        raise ValidationError("stop distance resolves to zero — cannot size", field="stop")

    raw_lots = risk_money.amount / denominator
    lots = round_down_to_step(raw_lots, instr.lot_step, instr.min_lot)
    units = lots * instr.contract_size

    realised_pip_value_account = lots * pip_value_per_lot_account
    realised_risk_amount = realised_pip_value_account * pip_distance
    money_at_risk = Money(realised_risk_amount, account_ccy).quantized()
    money_at_risk_pct = Percent(
        (money_at_risk.amount / inputs.account_balance.amount)
        if inputs.account_balance.amount > 0
        else Decimal("0")
    )

    rr: Decimal | None = None
    if inputs.target is not None:
        reward_pips = inputs.instrument.pips_between(inputs.entry, inputs.target)
        rr = reward_pips / pip_distance if pip_distance > 0 else None

    notional = units * inputs.entry  # in quote currency

    notes: list[str] = []
    if lots == 0:
        notes.append(
            "Calculated size rounds to zero — risk budget cannot afford the broker minimum lot. "
            "Tighten the stop, raise the account balance, or risk a higher percentage."
        )
    if inputs.risk.fraction > _RECOMMENDED_RISK_PCT:
        notes.append(
            f"Risking more than the {_RECOMMENDED_RISK_PCT * 100}% rule-of-thumb. "
            "Aggressive sizing — review the Risk-of-ruin lesson before continuing."
        )
    if rr is not None and rr < Decimal("1"):
        notes.append(
            f"R:R is {rr:.2f}, below 1.0 — the target is closer than the stop. "
            "Win-rate must be very high to be profitable; usually a sign to re-think the trade."
        )

    return PositionSizing(
        lots=lots,
        units=units,
        pip_distance=pip_distance,
        pip_value_in_account=Money(quantize_money(realised_pip_value_account), account_ccy),
        money_at_risk=money_at_risk,
        money_at_risk_pct=money_at_risk_pct,
        risk_reward_ratio=rr,
        notional_in_quote=notional,
        raw_lots_before_rounding=raw_lots,
        is_aggressive=inputs.risk.fraction > _RECOMMENDED_RISK_PCT,
        notes=tuple(notes),
    )
