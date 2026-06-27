"""Guardrail tests — these checks are aggregate, not per-trade."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.money import Money, Percent
from mentor.domain.risk import GuardrailLimits, OpenPosition, check_guardrails
from mentor.domain.risk.guardrails import BreachKind

LIMITS = GuardrailLimits(
    max_risk_per_trade=Percent.from_percent(2),
    max_open_risk=Percent.from_percent(6),
    daily_loss_limit=Percent.from_percent(4),
)
ACCOUNT = Money.of("10000", "USD")


def test_clean_trade_passes() -> None:
    report = check_guardrails(
        account_balance=ACCOUNT,
        limits=LIMITS,
        prospective_trade_risk=Money.of("100", "USD"),
    )
    assert report.passed
    assert report.breaches == ()


def test_per_trade_breach() -> None:
    report = check_guardrails(
        account_balance=ACCOUNT,
        limits=LIMITS,
        prospective_trade_risk=Money.of("300", "USD"),  # 3% > 2%
    )
    assert not report.passed
    assert any(b.kind is BreachKind.PER_TRADE for b in report.breaches)


def test_open_risk_breach() -> None:
    report = check_guardrails(
        account_balance=ACCOUNT,
        limits=LIMITS,
        prospective_trade_risk=Money.of("200", "USD"),
        open_positions=[
            OpenPosition(Money.of("200", "USD")),
            OpenPosition(Money.of("200", "USD")),
            OpenPosition(Money.of("200", "USD")),
        ],  # 800 / 10000 = 8% > 6%
    )
    assert not report.passed
    assert any(b.kind is BreachKind.OPEN_RISK for b in report.breaches)


def test_daily_loss_limit_blocks_new_trade() -> None:
    report = check_guardrails(
        account_balance=ACCOUNT,
        limits=LIMITS,
        prospective_trade_risk=Money.of("100", "USD"),
        realised_pnl_today=Money(Decimal("-450"), "USD"),  # -4.5% > 4%
    )
    assert not report.passed
    assert any(b.kind is BreachKind.DAILY_LOSS for b in report.breaches)
    breach = next(b for b in report.breaches if b.kind is BreachKind.DAILY_LOSS)
    assert "Step away" in breach.message


def test_approaching_open_risk_emits_warning_note() -> None:
    report = check_guardrails(
        account_balance=ACCOUNT,
        limits=LIMITS,
        prospective_trade_risk=Money.of("100", "USD"),
        open_positions=[OpenPosition(Money.of("400", "USD"))],  # 5%, limit 6%
    )
    assert report.passed
    assert any("approaching" in note for note in report.notes)


def test_positive_pnl_today_does_not_trigger_daily_loss() -> None:
    report = check_guardrails(
        account_balance=ACCOUNT,
        limits=LIMITS,
        prospective_trade_risk=Money.of("100", "USD"),
        realised_pnl_today=Money(Decimal("500"), "USD"),
    )
    assert report.passed
