"""A safety check must never report a pass it did not perform."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.journal.checklist import evaluate_pre_trade_checklist
from mentor.domain.journal.trade import TradePlan
from mentor.domain.money import Money, Percent
from mentor.domain.risk import GuardrailLimits, check_guardrails
from mentor.domain.risk.position_sizing import Direction


def _plan(risk: str = "50") -> TradePlan:
    return TradePlan(
        symbol="EURUSD",
        direction=Direction.LONG,
        size_lots=Decimal("0.10"),
        entry=Decimal("1.1000"),
        stop=Decimal("1.0950"),
        target=Decimal("1.1100"),
        initial_risk=Money(Decimal(risk), "USD"),
        reason="a reason long enough to satisfy the rule",
    )


def _item(result: object, key: str) -> object:
    return next(i for i in result.items if i.key == key)  # type: ignore[attr-defined]


def test_an_unchecked_guardrail_is_not_reported_as_passing() -> None:
    """Regression: with no limits supplied the rule did `passed = guardrails
    is None or guardrails.passed`, so it rendered a green tick having
    evaluated nothing. The Journal page sent no limits at all, so in
    production this item claimed "Account guardrails respected" on every
    trade ever logged — a risk control that only ever reassured."""
    result = evaluate_pre_trade_checklist(_plan(), guardrails=None)
    item = _item(result, "guardrails")

    assert item.passed is False  # type: ignore[attr-defined]
    assert item.skipped is True  # type: ignore[attr-defined]
    assert "Not checked" in (item.detail or "")  # type: ignore[attr-defined]
    assert not result.fully_checked  # type: ignore[attr-defined]


def test_a_skipped_rule_does_not_block_the_trade() -> None:
    """The user may simply not have configured limits — surface it, do not
    make the journal unusable."""
    result = evaluate_pre_trade_checklist(_plan(), guardrails=None)
    assert result.passed is True  # type: ignore[attr-defined]
    assert [i.key for i in result.skipped] == ["guardrails"]  # type: ignore[attr-defined]


def test_a_real_breach_fails_the_check() -> None:
    """25% of the account on one trade against a 1% limit."""
    report = check_guardrails(
        account_balance=Money(Decimal("10000"), "USD"),
        limits=GuardrailLimits(
            max_risk_per_trade=Percent.from_percent(Decimal("1")),
            max_open_risk=Percent.from_percent(Decimal("25")),
            daily_loss_limit=Percent.from_percent(Decimal("25")),
        ),
        prospective_trade_risk=Money(Decimal("2500"), "USD"),
    )
    result = evaluate_pre_trade_checklist(_plan("2500"), guardrails=report)
    item = _item(result, "guardrails")

    assert item.passed is False  # type: ignore[attr-defined]
    assert item.skipped is False  # type: ignore[attr-defined]
    assert result.passed is False  # type: ignore[attr-defined]


def test_a_compliant_trade_passes_for_real() -> None:
    report = check_guardrails(
        account_balance=Money(Decimal("10000"), "USD"),
        limits=GuardrailLimits(
            max_risk_per_trade=Percent.from_percent(Decimal("1")),
            max_open_risk=Percent.from_percent(Decimal("25")),
            daily_loss_limit=Percent.from_percent(Decimal("25")),
        ),
        prospective_trade_risk=Money(Decimal("50"), "USD"),
    )
    result = evaluate_pre_trade_checklist(_plan(), guardrails=report)

    assert _item(result, "guardrails").passed is True  # type: ignore[attr-defined]
    assert result.fully_checked  # type: ignore[attr-defined]
