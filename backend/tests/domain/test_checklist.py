"""Pre-trade checklist tests."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.journal import evaluate_pre_trade_checklist
from mentor.domain.journal.checklist import PreTradeChecklist
from mentor.domain.journal.trade import TradePlan
from mentor.domain.money import Money, Percent
from mentor.domain.risk import GuardrailLimits, check_guardrails
from mentor.domain.risk.position_sizing import Direction


def _plan(**overrides):
    base = {
        "symbol": "EURUSD",
        "direction": Direction.LONG,
        "size_lots": Decimal("0.33"),
        "entry": Decimal("1.08500"),
        "stop": Decimal("1.08200"),
        "target": Decimal("1.09100"),
        "initial_risk": Money.of("99", "USD"),
        "reason": "Pullback to 200-EMA in an uptrend, calm calendar today.",
    }
    base.update(overrides)
    return TradePlan(**base)


def test_clean_plan_passes() -> None:
    result = evaluate_pre_trade_checklist(_plan())
    assert result.passed
    assert result.failed == ()


def test_short_reason_fails() -> None:
    result = evaluate_pre_trade_checklist(_plan(reason="momentum"))
    assert not result.passed
    assert any(i.key == "reason" and not i.passed for i in result.items)


def test_missing_target_fails() -> None:
    result = evaluate_pre_trade_checklist(_plan(target=None))
    assert not result.passed
    assert any(i.key == "target" and not i.passed for i in result.items)


def test_low_rr_fails_default_rule() -> None:
    # entry 1.08500, stop 1.08200 (30 pips), target 1.08600 (10 pips) → 0.33 R:R
    result = evaluate_pre_trade_checklist(_plan(target=Decimal("1.08600")))
    assert any(i.key == "rr" and not i.passed for i in result.items)


def test_guardrail_breach_surfaces() -> None:
    guardrails = check_guardrails(
        account_balance=Money.of("1000", "USD"),
        limits=GuardrailLimits(
            max_risk_per_trade=Percent.from_percent(2),
            max_open_risk=Percent.from_percent(6),
            daily_loss_limit=Percent.from_percent(4),
        ),
        prospective_trade_risk=Money.of("99", "USD"),  # 9.9% > 2%
    )
    assert not guardrails.passed
    result = evaluate_pre_trade_checklist(_plan(), guardrails=guardrails)
    assert not result.passed
    item = next(i for i in result.items if i.key == "guardrails")
    assert not item.passed
    assert item.detail and "cap" in item.detail


def test_zero_size_fails() -> None:
    result = evaluate_pre_trade_checklist(_plan(size_lots=Decimal("0")))
    assert not result.passed
    assert any(i.key == "size" and not i.passed for i in result.items)


def test_relaxed_rules() -> None:
    rules = PreTradeChecklist(require_target=False, reason_min_chars=5)
    result = evaluate_pre_trade_checklist(_plan(target=None, reason="ok rule"), rules=rules)
    assert result.passed
