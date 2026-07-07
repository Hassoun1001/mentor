"""Volatility domain tests — realized vol, EWMA recursion, forecast building."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.volatility import (
    EwmaVolForecaster,
    VolForecast,
    VolRegime,
    build_sizing_guidance,
    build_vol_forecast,
    ewma_vol,
    horizon_move_pips,
    log_returns,
    percentile_rank,
    realized_vol,
    regime_from_percentile,
)
from mentor.domain.market.bars import PriceBar, Timeframe


def _bars(prices: list[Decimal]) -> list[PriceBar]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        PriceBar(
            symbol="EURUSD",
            timeframe=Timeframe.D1,
            ts=start + timedelta(days=i),
            open=p,
            high=p + Decimal("0.0010"),
            low=p - Decimal("0.0010"),
            close=p,
            volume=Decimal("100"),
            source="test",
        )
        for i, p in enumerate(prices)
    ]


def test_log_returns_count_and_zero_on_constant() -> None:
    closes = [Decimal("1.10")] * 5
    rets = log_returns(closes)
    assert len(rets) == 4
    assert all(r == 0 for r in rets)


def test_realized_vol_matches_hand_computation() -> None:
    # Alternating +/-1% returns: mean 0, sample variance = sum(r^2)/(n-1).
    rets = [Decimal("0.01"), Decimal("-0.01"), Decimal("0.01"), Decimal("-0.01")]
    rv = realized_vol(rets)
    assert rv is not None
    expected = (Decimal("0.0004") / Decimal("3")).sqrt()
    assert abs(rv - expected) < Decimal("1e-9")


def test_realized_vol_none_when_too_short() -> None:
    assert realized_vol([Decimal("0.01")]) is None


def test_ewma_recursion_by_hand() -> None:
    # seed_window=1 => var0 = 0.02^2 = 0.0004; fold r=0 => 0.94*0.0004.
    rets = [Decimal("0.02"), Decimal("0")]
    got = ewma_vol(rets, seed_window=1)
    assert got is not None
    expected = (Decimal("0.94") * Decimal("0.0004")).sqrt()
    assert abs(got - expected) < Decimal("1e-9")


def test_ewma_rejects_bad_lambda() -> None:
    with pytest.raises(ValidationError):
        ewma_vol([Decimal("0.01"), Decimal("0.02")], lam=Decimal("1.5"))


def test_percentile_and_regime() -> None:
    pop = [Decimal(str(x)) for x in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)]
    assert percentile_rank(Decimal("5"), pop) == Decimal("0.5")
    assert regime_from_percentile(Decimal("0.10")) is VolRegime.CALM
    assert regime_from_percentile(Decimal("0.50")) is VolRegime.NORMAL
    assert regime_from_percentile(Decimal("0.90")) is VolRegime.WIDE
    assert percentile_rank(Decimal("1"), []) == Decimal("0.5")  # empty => neutral


def test_horizon_move_scales_with_sqrt_h() -> None:
    per_bar = Decimal("0.01")
    close = Decimal("1.10")
    pip = Decimal("0.0001")
    one = horizon_move_pips(per_bar_vol=per_bar, close=close, horizon_bars=1, pip_size=pip)
    four = horizon_move_pips(per_bar_vol=per_bar, close=close, horizon_bars=4, pip_size=pip)
    # sqrt(4) = 2x the 1-bar move.
    assert abs(four - one * Decimal("2")) < Decimal("1e-6")


def test_build_vol_forecast_is_a_range_not_a_direction() -> None:
    history = [Decimal("0.005"), Decimal("0.006"), Decimal("0.007"), Decimal("0.02")]
    fc = build_vol_forecast(
        symbol="eurusd",
        timeframe=Timeframe.D1,
        asof=datetime(2026, 1, 1, tzinfo=UTC),
        asof_close=Decimal("1.10"),
        horizon_bars=5,
        per_bar_vol=Decimal("0.006"),
        history=history,
        pip_size=Decimal("0.0001"),
        model_name="ewma_vol",
    )
    assert fc.symbol == "EURUSD"
    assert fc.expected_range_pips > 0
    assert Decimal("0") <= fc.percentile_vs_history <= Decimal("1")
    assert fc.regime in set(VolRegime)
    assert "range" in fc.reasoning.lower()


def test_vol_forecast_rejects_bad_percentile() -> None:
    with pytest.raises(ValidationError):
        VolForecast(
            symbol="EURUSD",
            timeframe=Timeframe.D1,
            asof=datetime(2026, 1, 1, tzinfo=UTC),
            asof_close=Decimal("1.10"),
            horizon_bars=5,
            expected_vol=Decimal("0.01"),
            expected_range_pips=Decimal("50"),
            percentile_vs_history=Decimal("1.5"),
            regime=VolRegime.NORMAL,
            model_name="x",
            reasoning="x",
        )


def test_ewma_forecaster_produces_forecast() -> None:
    # A wiggly rising series so realized vol is non-zero and history builds.
    prices = [Decimal("1.10") + Decimal(str((i % 5) * 0.001)) for i in range(120)]
    bars = _bars(prices)
    fc = EwmaVolForecaster().forecast_vol(
        bars=bars,
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        horizon_bars=5,
        pip_size=Decimal("0.0001"),
    )
    assert fc.expected_vol > 0
    assert fc.expected_range_pips > 0
    assert fc.model_name.startswith("ewma_vol")


def _forecast_at(percentile: str, range_pips: str = "50") -> VolForecast:
    return VolForecast(
        symbol="EURUSD",
        timeframe=Timeframe.D1,
        asof=datetime(2026, 1, 1, tzinfo=UTC),
        asof_close=Decimal("1.10"),
        horizon_bars=5,
        expected_vol=Decimal("0.01"),
        expected_range_pips=Decimal(range_pips),
        percentile_vs_history=Decimal(percentile),
        regime=VolRegime.NORMAL,
        model_name="ewma_vol",
        reasoning="x",
    )


def test_sizing_guidance_stop_scales_with_sigma_multiple() -> None:
    g = build_sizing_guidance(_forecast_at("0.5", "40"), stop_sigma_mult=Decimal("1.5"))
    assert g.suggested_stop_pips == Decimal("60")  # 40 * 1.5
    assert g.event_freeze is False
    assert "risk calculator" in g.rationale


def test_sizing_guidance_freezes_on_high_percentile() -> None:
    g = build_sizing_guidance(_forecast_at("0.90"))
    assert g.event_freeze is True
    assert "freeze" in g.rationale.lower()


def test_ewma_forecaster_needs_enough_bars() -> None:
    with pytest.raises(ValidationError):
        EwmaVolForecaster().forecast_vol(
            bars=_bars([Decimal("1.10")] * 10),
            symbol="EURUSD",
            timeframe=Timeframe.D1,
            horizon_bars=5,
            pip_size=Decimal("0.0001"),
        )
