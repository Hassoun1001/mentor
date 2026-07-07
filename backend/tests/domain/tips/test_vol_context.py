"""Per-ticker volatility context tests."""

from __future__ import annotations

from decimal import Decimal

from mentor.domain.forecasting.volatility import VolRegime
from mentor.domain.tips.vol_context import build_ticker_vol_context


def test_none_when_series_too_short() -> None:
    assert build_ticker_vol_context([Decimal("100")] * 5) is None


def test_flat_series_has_no_move() -> None:
    ctx = build_ticker_vol_context([Decimal("100")] * 40)
    # Zero volatility -> ewma_vol is 0 -> None (nothing to say).
    assert ctx is None


def test_volatile_series_reports_move_and_regime() -> None:
    closes = [Decimal("100") + Decimal(str((i % 5) * 2)) for i in range(60)]
    ctx = build_ticker_vol_context(closes, horizon_days=5)
    assert ctx is not None
    assert ctx.expected_move_pct > 0
    assert ctx.regime in set(VolRegime)
    assert Decimal("0") <= ctx.percentile <= Decimal("1")


def test_move_scales_with_horizon() -> None:
    closes = [Decimal("100") + Decimal(str((i % 7) * 1.5)) for i in range(80)]
    one = build_ticker_vol_context(closes, horizon_days=1)
    four = build_ticker_vol_context(closes, horizon_days=4)
    assert one is not None and four is not None
    # sqrt(4) = 2x the 1-day move.
    assert abs(four.expected_move_pct - one.expected_move_pct * Decimal("2")) < Decimal("1e-6")
