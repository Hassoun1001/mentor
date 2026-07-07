"""Tests for tip scoring math and scorecard aggregation."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.tips.scoring import build_outcome, build_scorecard


def _outcome(ticker, category, action, mention, current, lo, hi):  # type: ignore[no-untyped-def]
    return build_outcome(
        ticker=ticker,
        category=category,
        action=action,
        conviction="high",
        note="",
        days_held=10,
        mention_price=Decimal(mention),
        current_price=Decimal(current),
        min_since=Decimal(lo),
        max_since=Decimal(hi),
    )


def test_return_and_envelope() -> None:
    o = _outcome("AAA", "safe", "buy", "100", "110", "95", "115")
    assert o.return_pct == Decimal("10.00")
    assert o.max_drawup_pct == Decimal("15.00")
    assert o.max_drawdown_pct == Decimal("-5.00")


def test_buy_on_dip_flags_actual_dip() -> None:
    dipped = _outcome("BBB", "safe", "buy_on_dip", "100", "108", "97", "108")
    held = _outcome("CCC", "safe", "buy_on_dip", "100", "108", "101", "108")
    assert dipped.dipped is True
    assert held.dipped is False
    # non-dip actions carry no dip verdict
    assert _outcome("DDD", "safe", "buy", "100", "108", "97", "108").dipped is None


def test_at_or_below_entry_flags_buy_calls_back_at_his_price() -> None:
    # a buy trading below the mentioned price -> back at entry
    assert _outcome("AAA", "safe", "buy", "100", "98", "95", "101").at_or_below_entry is True
    # exactly at entry counts
    at_entry = _outcome("BBB", "safe", "buy_on_dip", "100", "100", "97", "105")
    assert at_entry.at_or_below_entry is True
    # a buy above entry does not
    assert _outcome("CCC", "safe", "buy", "100", "110", "100", "112").at_or_below_entry is False
    # non-buy actions never flag
    assert _outcome("DDD", "safe", "avoid", "100", "90", "88", "100").at_or_below_entry is False


def test_scorecard_aggregates_by_category_and_action() -> None:
    outcomes = [
        _outcome("W", "safe", "buy", "100", "110", "100", "110"),  # +10
        _outcome("L", "safe", "buy", "100", "90", "88", "100"),  # -10
        _outcome("H", "high_risk", "hold", "100", "80", "80", "100"),  # -20
    ]
    card = build_scorecard(tipster="Tester", outcomes=outcomes)
    assert card.total == 3
    assert card.overall.count == 3
    # mean of +10, -10, -20 = -6.67
    assert card.overall.mean_return_pct == Decimal("-6.67")
    # one of three positive
    assert card.overall.win_rate == Decimal("0.33")
    cats = {b.key: b for b in card.by_category}
    assert cats["safe"].count == 2
    assert cats["high_risk"].mean_return_pct == Decimal("-20.00")


def test_empty_scorecard_is_honest() -> None:
    card = build_scorecard(tipster="Nobody", outcomes=[])
    assert card.total == 0
    assert "No priced tips" in card.headline
