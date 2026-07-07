"""Follow-him backtest — sizing, stop-out, equity curve, expectancy."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.tips.backtest import TipEntry, run_follow_backtest


def _entry(ticker: str, day: int, entry: str, exit_: str, min_since: str) -> TipEntry:
    return TipEntry(
        ticker=ticker,
        mentioned_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=day),
        entry_price=Decimal(entry),
        exit_price=Decimal(exit_),
        min_since=Decimal(min_since),
        days_held=10,
    )


def test_winning_trade_sizes_to_risk_budget() -> None:
    # risk 1% of 10000 = 100; stop 10% => stop_dist 10 on a 100 entry => 10 shares.
    res = run_follow_backtest(
        tipster="mohit",
        entries=[_entry("AAA", 0, "100", "110", "95")],
        starting_equity=Decimal("10000"),
        risk_pct=Decimal("0.01"),
        stop_pct=Decimal("0.10"),
    )
    assert res.n_trades == 1
    t = res.trades[0]
    assert t.shares == Decimal("10")
    assert t.pnl == Decimal("100.00")  # 10 * (110 - 100)
    assert t.r_multiple == Decimal("1.00")
    assert t.won is True
    assert res.ending_equity == Decimal("10100.00")


def test_stop_out_is_capped_at_one_r() -> None:
    # Price dipped below the 10% stop => booked at the stop, ~ -1R.
    res = run_follow_backtest(
        tipster="mohit",
        entries=[_entry("BBB", 0, "100", "80", "85")],  # min 85 < stop 90
        starting_equity=Decimal("10000"),
        risk_pct=Decimal("0.01"),
        stop_pct=Decimal("0.10"),
    )
    t = res.trades[0]
    assert t.stopped_out is True
    assert t.exit_fill == Decimal("90.00")
    assert t.pnl == Decimal("-100.00")  # 10 shares * (90 - 100)
    assert t.r_multiple == Decimal("-1.00")


def test_hold_mode_ignores_stop() -> None:
    res = run_follow_backtest(
        tipster="mohit",
        entries=[_entry("CCC", 0, "100", "80", "85")],
        starting_equity=Decimal("10000"),
        apply_stop=False,
    )
    t = res.trades[0]
    assert t.stopped_out is False
    assert t.exit_fill == Decimal("80")  # marked to latest, not the stop


def test_equity_curve_and_expectancy_and_drawdown() -> None:
    res = run_follow_backtest(
        tipster="mohit",
        entries=[
            _entry("WIN", 0, "100", "110", "100"),  # +1R
            _entry("LOSE", 1, "100", "80", "85"),  # stopped, -1R
        ],
        starting_equity=Decimal("10000"),
        risk_pct=Decimal("0.01"),
        stop_pct=Decimal("0.10"),
    )
    assert res.n_trades == 2
    assert res.win_rate == Decimal("0.50")
    # curve has start + one point per trade
    assert len(res.equity_curve) == 3
    assert res.max_drawdown_pct > 0  # peaked after the win, then gave it back
    assert "Following mohit" in res.headline


def test_no_entries_is_empty() -> None:
    res = run_follow_backtest(tipster="nobody", entries=[])
    assert res.n_trades == 0
    assert res.ending_equity == res.starting_equity


def test_rejects_bad_risk() -> None:
    with pytest.raises(ValueError):
        run_follow_backtest(tipster="x", entries=[], risk_pct=Decimal("0.9"))
