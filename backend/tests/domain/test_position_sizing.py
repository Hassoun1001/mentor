"""Position sizing tests — including the property that realised risk never
exceeds the user's stated risk budget for *any* valid input.

This is the most important invariant in Phase 0: the calculator is a
ceiling, not a target. A bug that lets it exceed the budget would
quietly bankrupt a trader.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import get_instrument
from mentor.domain.money import Money, Percent
from mentor.domain.risk import Direction, RiskInputs, calculate_position

EURUSD = get_instrument("EURUSD")
USDJPY = get_instrument("USDJPY")


def _inputs(
    *,
    balance: str = "10000",
    risk_pct: str = "1",
    entry: str = "1.08500",
    stop: str = "1.08200",
    target: str | None = "1.09100",
    direction: Direction = Direction.LONG,
    instrument=EURUSD,
    quote_to_account: str = "1",
) -> RiskInputs:
    return RiskInputs(
        account_balance=Money.of(balance, "USD"),
        risk=Percent.from_percent(risk_pct),
        entry=Decimal(entry),
        stop=Decimal(stop),
        target=Decimal(target) if target else None,
        direction=direction,
        instrument=instrument,
        quote_to_account_rate=Decimal(quote_to_account),
    )


class TestCalculatePosition:
    def test_canonical_eurusd_long(self) -> None:
        """A $10,000 account risking 1% with a 30-pip stop on EUR/USD.

        Risk budget = $100. Pip value per standard lot in USD = $10.
        Expected raw lots = 100 / (30 * 10) = 0.333…, rounded down to 0.33.
        """
        result = calculate_position(_inputs())
        assert result.lots == Decimal("0.33")
        assert result.pip_distance == Decimal("30")
        assert result.money_at_risk.amount == Decimal("99.00")
        assert result.money_at_risk.currency == "USD"
        assert result.risk_reward_ratio == Decimal("2")

    def test_usdjpy_uses_jpy_pip_size(self) -> None:
        """JPY pip = 0.01, so 50 pips = 0.50 price."""
        inputs = _inputs(
            entry="155.000",
            stop="154.500",
            target=None,
            instrument=USDJPY,
            # JPY-account-quote means 1 pip per lot = ¥1000 → assume 1 USD = 150 JPY
            quote_to_account="0.00667",
        )
        result = calculate_position(inputs)
        assert result.pip_distance == Decimal("50")
        # We just assert it's a positive, non-zero lot count.
        assert result.lots > 0

    def test_rejects_entry_equals_stop(self) -> None:
        with pytest.raises(ValidationError):
            _inputs(entry="1.08", stop="1.08")

    def test_long_rejects_stop_above_entry(self) -> None:
        with pytest.raises(ValidationError):
            _inputs(entry="1.08", stop="1.09", target=None, direction=Direction.LONG)

    def test_short_rejects_stop_below_entry(self) -> None:
        with pytest.raises(ValidationError):
            _inputs(entry="1.08", stop="1.07", target=None, direction=Direction.SHORT)

    def test_short_target_below_entry(self) -> None:
        result = calculate_position(
            _inputs(
                direction=Direction.SHORT,
                entry="1.08500",
                stop="1.08800",
                target="1.07900",
            )
        )
        assert result.risk_reward_ratio == Decimal("2")

    def test_rejects_risk_over_10_percent(self) -> None:
        with pytest.raises(ValidationError):
            _inputs(risk_pct="11")

    def test_rejects_negative_account(self) -> None:
        with pytest.raises(ValidationError):
            RiskInputs(
                account_balance=Money(Decimal("-1"), "USD"),
                risk=Percent.from_percent(1),
                entry=Decimal("1.08"),
                stop=Decimal("1.07"),
                direction=Direction.LONG,
                instrument=EURUSD,
            )

    def test_tiny_account_rounds_to_zero(self) -> None:
        """A $5 account risking 1% can't afford the micro-lot minimum."""
        result = calculate_position(_inputs(balance="5", target=None))
        assert result.lots == Decimal("0")
        assert any("rounds to zero" in n for n in result.notes)

    def test_aggressive_sizing_flagged(self) -> None:
        result = calculate_position(_inputs(risk_pct="5", target=None))
        assert result.is_aggressive
        assert any("Aggressive" in n for n in result.notes)

    def test_sub_one_rr_flagged(self) -> None:
        result = calculate_position(_inputs(entry="1.08500", stop="1.08200", target="1.08600"))
        assert result.risk_reward_ratio is not None
        assert result.risk_reward_ratio < Decimal("1")
        assert any("R:R" in n for n in result.notes)


# ---------------------------------------------------------------------------
# Property: realised risk must never exceed the stated budget.
# ---------------------------------------------------------------------------

balances = st.decimals(
    min_value=Decimal("100"),
    max_value=Decimal("1000000"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)
risks = st.decimals(min_value=Decimal("0.1"), max_value=Decimal("10"), places=2)
entries = st.decimals(min_value=Decimal("0.5"), max_value=Decimal("2"), places=5)
stop_offsets = st.decimals(min_value=Decimal("0.0005"), max_value=Decimal("0.05"), places=5)


@given(balance=balances, risk_pct=risks, entry=entries, stop_offset=stop_offsets)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=200, deadline=None)
def test_realised_risk_never_exceeds_budget(
    balance: Decimal, risk_pct: Decimal, entry: Decimal, stop_offset: Decimal
) -> None:
    inputs = RiskInputs(
        account_balance=Money(balance, "USD"),
        risk=Percent.from_percent(risk_pct),
        entry=entry,
        stop=entry - stop_offset,
        direction=Direction.LONG,
        instrument=EURUSD,
    )
    result = calculate_position(inputs)
    budget = balance * (risk_pct / Decimal("100"))
    # money_at_risk is quantized to 2dp; allow 1 cent of rounding slack.
    assert result.money_at_risk.amount <= budget + Decimal("0.01"), (
        f"risk {result.money_at_risk.amount} exceeded budget {budget} "
        f"for balance={balance}, risk={risk_pct}, entry={entry}, stop={inputs.stop}"
    )
