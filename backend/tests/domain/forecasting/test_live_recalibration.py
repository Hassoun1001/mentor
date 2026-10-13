"""Live recalibration: the champion's live mistakes may correct its stated
confidence — but only when the correction survives calls it never saw.

Every fixture is a fixed, hand-built sequence: no RNG, so each verdict
below is exactly reproducible.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.forecast import Direction, Forecast
from mentor.domain.forecasting.live_recalibration import (
    apply_to_forecast,
    fit_live_recalibration,
    recalibrate,
)
from mentor.domain.market.bars import Timeframe
from mentor.domain.stats.significance import MIN_SAMPLE_FOR_VERDICT


def _overconfident(n: int) -> list[tuple[float, int]]:
    """Leans 70/30 every call, but each lean lands exactly half the time."""
    calls: list[tuple[float, int]] = []
    for i in range(n):
        p = 0.7 if i % 2 == 0 else 0.3
        calls.append((p, 1 if i % 4 in (0, 1) else 0))
    return calls


def _calibrated(n_blocks: int) -> list[tuple[float, int]]:
    """70% calls that land exactly 7 in 10, 30% calls that land 3 in 10."""
    calls: list[tuple[float, int]] = []
    for _ in range(n_blocks):
        calls += [(0.7, 1)] * 7 + [(0.7, 0)] * 3
        calls += [(0.3, 1)] * 3 + [(0.3, 0)] * 7
    return calls


def _underconfident(n_blocks: int) -> list[tuple[float, int]]:
    """60% calls that land 9 in 10 — the model undersells itself."""
    calls: list[tuple[float, int]] = []
    for _ in range(n_blocks):
        calls += [(0.6, 1)] * 9 + [(0.6, 0)]
        calls += [(0.4, 0)] * 9 + [(0.4, 1)]
    return calls


# ---- the transform ---------------------------------------------------------


def test_the_slope_holds_fifty_percent_in_place_and_never_flips_a_lean() -> None:
    for slope in (0.0, 0.4, 1.0, 1.5):
        assert recalibrate(0.5, slope) == pytest.approx(0.5)
        assert recalibrate(0.62, slope) >= 0.5
        assert recalibrate(0.38, slope) <= 0.5


def test_a_slope_below_one_pulls_toward_fifty_and_above_one_pushes_out() -> None:
    assert recalibrate(0.7, 0.5) < 0.7
    assert recalibrate(0.7, 1.5) > 0.7
    assert recalibrate(0.7, 1.0) == 0.7  # identity is exact, not approximate
    assert recalibrate(0.7, 0.0) == pytest.approx(0.5)


def test_the_slope_is_finite_at_the_edges() -> None:
    assert 0.0 < recalibrate(0.0, 0.5) < 0.5
    assert 0.5 < recalibrate(1.0, 0.5) < 1.0


def test_a_negative_slope_is_refused() -> None:
    with pytest.raises(ValidationError):
        recalibrate(0.6, -0.1)


# ---- the fit ---------------------------------------------------------------


def test_below_the_sample_floor_nothing_is_fitted() -> None:
    """Regression guard: the floor is the same 30 the significance verdicts
    use — five lucky days must not rewrite the model's confidence."""
    result = fit_live_recalibration(_overconfident(MIN_SAMPLE_FOR_VERDICT - 1))
    assert result.applied is False
    assert result.active_slope == 1.0
    assert result.n_independent == MIN_SAMPLE_FOR_VERDICT - 1
    assert result.required == MIN_SAMPLE_FOR_VERDICT
    assert result.brier_before is None and result.gain is None
    assert "need 30" in result.reason


def test_an_overconfident_champion_is_pulled_toward_fifty() -> None:
    result = fit_live_recalibration(_overconfident(40))
    assert result.applied is True
    assert result.slope < 1.0
    assert result.active_slope == result.slope
    # Older half selects, newer half grades.
    assert (result.n_fit, result.n_holdout) == (20, 20)
    assert result.brier_before == pytest.approx(0.29)  # 0.7 calls landing 50%
    assert result.brier_after is not None and result.brier_after < result.brier_before
    assert result.gain is not None and result.gain >= 0.002


def test_a_well_calibrated_champion_is_left_alone() -> None:
    result = fit_live_recalibration(_calibrated(2))  # 40 calls, exact 70/30
    assert result.applied is False
    assert result.slope == 1.0
    assert "already fits" in result.reason


def test_an_underconfident_champion_is_sharpened_but_capped() -> None:
    result = fit_live_recalibration(_underconfident(2))
    assert result.applied is True
    assert 1.0 < result.slope <= 1.5


def test_a_correction_that_does_not_hold_up_on_newer_calls_is_not_applied() -> None:
    """The older half looks overconfident; the newer half shows the model was
    right all along. The slope the past suggests would hurt the future, so
    it must be refused — and the audit must still show what was tried."""
    calls = _overconfident(20) + _calibrated(1)
    result = fit_live_recalibration(calls)
    assert result.slope < 1.0  # the older half did argue for shrinking...
    assert result.applied is False  # ...but the newer half refused it
    assert result.active_slope == 1.0
    assert result.brier_after is not None and result.brier_before is not None
    assert result.brier_after > result.brier_before
    assert "not applied" in result.reason


def test_the_fit_respects_time_order() -> None:
    """Same calls, opposite order, different verdict: the split is in time,
    never shuffled, so which half selects and which grades is the point."""
    forward = fit_live_recalibration(_overconfident(20) + _calibrated(1))
    backward = fit_live_recalibration(_calibrated(1) + _overconfident(20))
    assert forward.applied is False
    assert backward.slope == 1.0  # calibrated older half: nothing to correct


def test_bad_inputs_are_refused() -> None:
    with pytest.raises(ValidationError):
        fit_live_recalibration([(1.2, 1)] * 30)
    with pytest.raises(ValidationError):
        fit_live_recalibration([(0.6, 2)] * 30)


def test_the_audit_record_carries_the_decision() -> None:
    record = fit_live_recalibration(_overconfident(40)).to_dict()
    for key in (
        "applied",
        "slope",
        "active_slope",
        "n_independent",
        "required",
        "n_fit",
        "n_holdout",
        "brier_before",
        "brier_after",
        "gain",
        "reason",
    ):
        assert key in record


# ---- applying it to a forecast ---------------------------------------------


def _forecast(p_up: str, confidence: str | None = None) -> Forecast:
    p = Decimal(p_up)
    return Forecast(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        asof=datetime(2026, 10, 13, 12, tzinfo=UTC),
        asof_close=Decimal("1.1000"),
        horizon_bars=24,
        p_up=p,
        confidence=Decimal(confidence) if confidence else abs(p - Decimal("0.5")) * 2,
        direction=Direction.LONG if p > Decimal("0.5") else Direction.SHORT,
        model_name="regime_adjusted(sklearn_hgb(h=24))",
        reasoning="ML lean.",
        features={},
    )


def test_no_correction_returns_the_forecast_untouched() -> None:
    fc = _forecast("0.6200")
    assert apply_to_forecast(fc, 1.0) is fc


def test_a_correction_restates_the_probability_and_records_the_models_own() -> None:
    fc = _forecast("0.7000")
    out = apply_to_forecast(fc, 0.5)
    assert out.p_up_model == Decimal("0.7000")
    assert out.p_up == Decimal(str(round(recalibrate(0.7, 0.5), 4)))
    assert out.p_up < fc.p_up
    assert out.direction is Direction.LONG  # the lean survives
    assert "overconfident" in out.reasoning


def test_a_weak_lean_can_fall_into_the_neutral_band() -> None:
    """A call the live record says is a coin flip should read as one."""
    out = apply_to_forecast(_forecast("0.5600"), 0.3)
    assert out.direction is Direction.NEUTRAL


def test_regime_shrink_on_confidence_is_preserved() -> None:
    """The regime wrapper had already halved this call's confidence; the
    correction scales what is left rather than recomputing it from p_up."""
    fc = _forecast("0.7000", confidence="0.2000")  # 0.4 from p_up, halved by regime
    out = apply_to_forecast(fc, 0.5)
    expected_ratio = (out.p_up - Decimal("0.5")) / Decimal("0.2")
    assert out.confidence == (Decimal("0.2") * expected_ratio).quantize(Decimal("0.0001"))
