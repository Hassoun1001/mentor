"""Account-wide risk guardrails.

> Max risk per trade, max simultaneous open risk, and a daily loss limit
> — each explained by the mentor.   — Mentor product plan, §6.E

These checks are *aggregate*: the position-size calculator ensures a single
trade fits the user's per-trade budget; the guardrails make sure that taking
that trade right now, on top of everything else that is open today, still
respects the user's account-level discipline.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.money import Money, Percent, to_decimal


class BreachKind(StrEnum):
    PER_TRADE = "per_trade"
    OPEN_RISK = "open_risk"
    DAILY_LOSS = "daily_loss"


@dataclass(frozen=True, slots=True)
class Breach:
    kind: BreachKind
    message: str
    current: Decimal
    limit: Decimal


@dataclass(frozen=True, slots=True)
class GuardrailLimits:
    """The user-configured ceilings, all expressed as fractions of equity."""

    max_risk_per_trade: Percent
    max_open_risk: Percent
    daily_loss_limit: Percent

    def __post_init__(self) -> None:
        if self.max_risk_per_trade.fraction > self.max_open_risk.fraction:
            raise ValidationError(
                "max_risk_per_trade cannot exceed max_open_risk",
                field="max_risk_per_trade",
            )


@dataclass(frozen=True, slots=True)
class OpenPosition:
    """An already-open position contributing to portfolio risk."""

    money_at_risk: Money


@dataclass(frozen=True, slots=True)
class GuardrailReport:
    passed: bool
    breaches: tuple[Breach, ...]
    open_risk_pct: Percent
    daily_loss_pct: Percent
    prospective_trade_risk_pct: Percent
    notes: tuple[str, ...] = field(default_factory=tuple)


def _sum_money(items: Sequence[Money], currency: str) -> Decimal:
    total = Decimal("0")
    for item in items:
        if item.currency != currency:
            raise ValidationError(
                f"currency mismatch in guardrail check: {item.currency} vs {currency}",
                field="currency",
            )
        total += item.amount
    return total


def check_guardrails(
    *,
    account_balance: Money,
    limits: GuardrailLimits,
    prospective_trade_risk: Money,
    open_positions: Sequence[OpenPosition] = (),
    realised_pnl_today: Money | None = None,
) -> GuardrailReport:
    """Evaluate whether a prospective trade respects the configured guardrails.

    Returns a report rather than raising — the UI shows the user *why* the
    trade is blocked, with the current vs. allowed numbers and a mentor
    note explaining each rule.
    """
    if not account_balance.is_positive:
        raise ValidationError("account_balance must be positive", field="account_balance")

    ccy = account_balance.currency
    if prospective_trade_risk.currency != ccy:
        raise ValidationError(
            f"prospective_trade_risk currency mismatch: {prospective_trade_risk.currency} vs {ccy}",
            field="prospective_trade_risk",
        )

    equity = account_balance.amount

    trade_pct = prospective_trade_risk.amount / equity
    open_total = _sum_money([p.money_at_risk for p in open_positions], ccy)
    open_pct = open_total / equity
    combined_pct = open_pct + trade_pct

    loss_today = Decimal("0")
    if realised_pnl_today is not None:
        if realised_pnl_today.currency != ccy:
            raise ValidationError(
                "realised_pnl_today currency mismatch",
                field="realised_pnl_today",
            )
        if realised_pnl_today.amount < 0:
            loss_today = -realised_pnl_today.amount
    loss_today_pct = loss_today / equity

    breaches: list[Breach] = []

    if trade_pct > limits.max_risk_per_trade.fraction:
        breaches.append(
            Breach(
                kind=BreachKind.PER_TRADE,
                message=(
                    f"This trade risks {trade_pct * 100:.2f}% of equity, above the "
                    f"{limits.max_risk_per_trade.as_percent}% per-trade cap."
                ),
                current=trade_pct,
                limit=limits.max_risk_per_trade.fraction,
            )
        )

    if combined_pct > limits.max_open_risk.fraction:
        breaches.append(
            Breach(
                kind=BreachKind.OPEN_RISK,
                message=(
                    f"Open risk would reach {combined_pct * 100:.2f}% of equity, "
                    f"above the {limits.max_open_risk.as_percent}% portfolio cap."
                ),
                current=combined_pct,
                limit=limits.max_open_risk.fraction,
            )
        )

    if loss_today_pct >= limits.daily_loss_limit.fraction:
        breaches.append(
            Breach(
                kind=BreachKind.DAILY_LOSS,
                message=(
                    f"Today's realised loss is {loss_today_pct * 100:.2f}% of equity, "
                    f"hitting the {limits.daily_loss_limit.as_percent}% daily-loss limit. "
                    "Step away — the next trade is the worst one."
                ),
                current=loss_today_pct,
                limit=limits.daily_loss_limit.fraction,
            )
        )

    notes: list[str] = []
    if not breaches and combined_pct > to_decimal("0.8") * limits.max_open_risk.fraction:
        notes.append(
            "Open risk is approaching the portfolio cap — one more loss away from being blocked."
        )

    return GuardrailReport(
        passed=not breaches,
        breaches=tuple(breaches),
        open_risk_pct=Percent(open_pct),
        daily_loss_pct=Percent(loss_today_pct),
        prospective_trade_risk_pct=Percent(trade_pct),
        notes=tuple(notes),
    )
