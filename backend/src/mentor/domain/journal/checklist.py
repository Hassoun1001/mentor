"""Pre-trade checklist — the discipline gate.

> A short checklist that must be completed before an entry — forcing a
> reason, a stop, and a target every time.   — Mentor product plan, §6.F

The checklist is *advisory* by default — it returns a list of unmet items
rather than raising — so the UI can show the user *what* is missing and
encourage them to fix it rather than just refusing. The API layer can
choose to block entry on `passed == False`; that is a policy decision, not
a domain one.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from mentor.domain.journal.trade import TradePlan
from mentor.domain.risk.guardrails import GuardrailReport


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    key: str
    label: str
    passed: bool
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class ChecklistResult:
    passed: bool
    items: tuple[ChecklistItem, ...]
    failed: tuple[ChecklistItem, ...]


@dataclass(frozen=True, slots=True)
class PreTradeChecklist:
    """The default rules. Adding a new rule is a one-line append below."""

    require_reason: bool = True
    require_stop: bool = True
    require_target: bool = True
    require_minimum_rr: Decimal = Decimal("1.0")
    require_passing_guardrails: bool = True
    require_size_above_zero: bool = True
    reason_min_chars: int = 20
    custom_rules: tuple[ChecklistItem, ...] = field(default_factory=tuple)


def _item(key: str, label: str, passed: bool, detail: str | None = None) -> ChecklistItem:
    return ChecklistItem(key=key, label=label, passed=passed, detail=detail)


def evaluate_pre_trade_checklist(
    plan: TradePlan,
    *,
    rules: PreTradeChecklist | None = None,
    guardrails: GuardrailReport | None = None,
    extra_items: Sequence[ChecklistItem] = (),
) -> ChecklistResult:
    """Evaluate a plan against the checklist.

    Returns a structured report — the API turns this into a "what's
    missing" panel rather than a single boolean.
    """
    rules = rules or PreTradeChecklist()
    items: list[ChecklistItem] = []

    if rules.require_reason:
        reason = (plan.reason or "").strip()
        ok = len(reason) >= rules.reason_min_chars
        items.append(
            _item(
                "reason",
                f"Reason ≥ {rules.reason_min_chars} characters",
                ok,
                None if ok else f"reason is {len(reason)} characters",
            )
        )

    if rules.require_stop:
        # plan construction already enforces stop differs from entry; this
        # is a UI-visible confirmation so the trader checks the box.
        items.append(_item("stop", "Stop loss defined", plan.stop != plan.entry))

    if rules.require_target:
        items.append(
            _item(
                "target",
                "Profit target defined",
                plan.target is not None,
                "leaving target undefined invites moving it to chase price",
            )
        )

    if rules.require_minimum_rr and plan.target is not None:
        risk = abs(plan.entry - plan.stop)
        reward = abs(plan.target - plan.entry)
        rr = reward / risk if risk > 0 else Decimal("0")
        ok = rr >= rules.require_minimum_rr
        items.append(
            _item(
                "rr",
                f"Risk:reward ≥ {rules.require_minimum_rr}",
                ok,
                f"current R:R is 1 : {rr:.2f}",
            )
        )

    if rules.require_size_above_zero:
        items.append(
            _item(
                "size",
                "Position size > 0",
                plan.size_lots > 0,
                None
                if plan.size_lots > 0
                else "calculated size is zero — risk budget can't afford the minimum lot",
            )
        )

    if rules.require_passing_guardrails:
        passed = guardrails is None or guardrails.passed
        detail = None
        if guardrails is not None and not guardrails.passed:
            detail = "; ".join(b.message for b in guardrails.breaches)
        items.append(_item("guardrails", "Account guardrails respected", passed, detail))

    items.extend(extra_items)
    items.extend(rules.custom_rules)

    failed = tuple(i for i in items if not i.passed)
    return ChecklistResult(passed=not failed, items=tuple(items), failed=failed)
