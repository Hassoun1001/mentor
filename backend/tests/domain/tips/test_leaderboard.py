"""Leaderboard ranking — risk-adjusted, honest with thin samples."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.tips.leaderboard import build_leaderboard
from mentor.domain.tips.scoring import TipOutcome


def _outcome(ticker: str, ret: str) -> TipOutcome:
    return TipOutcome(
        ticker=ticker,
        category="other",
        action="buy",
        conviction="medium",
        note="",
        days_held=10,
        mention_price=Decimal("100"),
        current_price=Decimal("100"),
        return_pct=Decimal(ret),
        max_drawup_pct=Decimal("0"),
        max_drawdown_pct=Decimal("0"),
        dipped=None,
    )


def test_steady_tipster_outranks_volatile_one_with_same_mean() -> None:
    steady = [_outcome("A", "5"), _outcome("B", "5"), _outcome("C", "5")]
    volatile = [_outcome("D", "-15"), _outcome("E", "5"), _outcome("F", "25")]  # mean 5, high stdev
    board = build_leaderboard({"steady": steady, "volatile": volatile})
    assert [r.tipster for r in board] == ["steady", "volatile"]
    assert board[0].risk_adjusted > board[1].risk_adjusted


def test_row_stats_are_correct() -> None:
    board = build_leaderboard({"m": [_outcome("A", "10"), _outcome("B", "-10")]})
    row = board[0]
    assert row.tracked_calls == 2
    assert row.mean_return_pct == Decimal("0.00")
    assert row.win_rate == Decimal("0.50")
    assert row.best_ticker == "A"


def test_empty_tipsters_are_dropped() -> None:
    board = build_leaderboard({"m": [_outcome("A", "3")], "empty": []})
    assert [r.tipster for r in board] == ["m"]
