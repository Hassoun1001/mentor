"""The volatility audit must catch under-forecasting, which is the costly failure."""

from __future__ import annotations

import pytest

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.vol_audit import (
    MEAN_ABS_OVER_SIGMA,
    MEDIAN_ABS_OVER_SIGMA,
    NORMAL_ONE_SIGMA,
    VolSample,
    audit_vol_forecasts,
    normal_quantile_hit_rate,
)


def _samples(sigma: float, moves: list[float]) -> list[VolSample]:
    return [VolSample(predicted_sigma_pips=sigma, realised_move_pips=m) for m in moves]


def _well_calibrated(n: int = 400, sigma: float = 20.0) -> list[VolSample]:
    """68% of moves inside 1 sigma, as the docstring promises."""
    inside = int(n * NORMAL_ONE_SIGMA)
    moves = [sigma * 0.5] * inside + [sigma * 1.6] * (n - inside)
    return _samples(sigma, moves)


# ---------- the 1-sigma claim ----------


def test_a_well_calibrated_forecast_is_not_flagged() -> None:
    r = audit_vol_forecasts(_well_calibrated())
    assert not r.one_sigma.significant
    assert not r.one_sigma.understates_risk
    assert "holding up" in r.verdict


def test_systematic_under_forecasting_is_caught_and_named() -> None:
    # Only 40% of moves stay inside 1 sigma — stops are far too tight.
    moves = [10.0] * 160 + [55.0] * 240
    r = audit_vol_forecasts(_samples(20.0, moves))
    assert r.one_sigma.significant
    assert r.one_sigma.understates_risk
    assert "too tight" in r.verdict


def test_over_forecasting_is_reported_but_not_as_danger() -> None:
    # 95% inside — safe, just wasteful.
    moves = [5.0] * 380 + [40.0] * 20
    r = audit_vol_forecasts(_samples(20.0, moves))
    assert r.one_sigma.significant
    assert not r.one_sigma.understates_risk
    assert "conservative" in r.verdict


def test_a_small_sample_is_not_treated_as_proof() -> None:
    # 50% inside, but only 12 forecasts — the interval is far too wide to call.
    r = audit_vol_forecasts(_samples(20.0, [10.0] * 6 + [40.0] * 6))
    assert not r.one_sigma.significant
    assert "interval" in r.one_sigma.verdict


# ---------- the band claim ----------


def test_band_coverage_is_measured_separately_from_one_sigma() -> None:
    samples = [
        VolSample(
            predicted_sigma_pips=20.0,
            realised_move_pips=m,
            band_low_pips=5.0,
            band_high_pips=45.0,
        )
        for m in ([10.0] * 360 + [80.0] * 40)  # 90% inside the band
    ]
    r = audit_vol_forecasts(samples, band_coverage=0.90)
    assert r.band is not None
    assert not r.band.significant  # the 90% claim holds
    assert r.band.label.startswith("conformal 90%")


def test_a_band_narrower_than_advertised_is_caught() -> None:
    samples = [
        VolSample(
            predicted_sigma_pips=20.0,
            realised_move_pips=m,
            band_low_pips=15.0,
            band_high_pips=25.0,
        )
        for m in ([20.0] * 240 + [80.0] * 160)  # only 60% inside
    ]
    r = audit_vol_forecasts(samples, band_coverage=0.90)
    assert r.band is not None
    assert r.band.understates_risk
    assert "too narrow" in r.verdict


def test_no_band_means_no_band_check() -> None:
    assert audit_vol_forecasts(_well_calibrated()).band is None


# ---------- bias and benchmarks ----------


def test_a_calibrated_forecast_scores_a_ratio_of_one() -> None:
    """The property that matters: a sigma is not an average move.

    For a normal variable the median absolute value is ~0.674 sigma, so a
    perfectly calibrated forecast must score 1.0 — not 0.674. Measuring the
    raw realised/sigma ratio would brand every correct forecast as
    over-predicting by 33%, which is exactly the mistake this guards.
    """
    sigma = 20.0
    calibrated_median = sigma * MEDIAN_ABS_OVER_SIGMA
    r = audit_vol_forecasts(_samples(sigma, [calibrated_median] * 200))
    assert r.median_ratio == pytest.approx(1.0)
    assert "systematically" not in r.verdict


def test_a_systematic_scale_error_shows_in_the_median_ratio() -> None:
    # Moves are twice what a calibrated forecast of this size predicts.
    sigma = 20.0
    r = audit_vol_forecasts(_samples(sigma, [sigma * MEDIAN_ABS_OVER_SIGMA * 2] * 200))
    assert r.median_ratio == pytest.approx(2.0)
    assert "2.00x" in r.verdict


def test_accuracy_is_scored_on_the_implied_mean_move_not_the_sigma() -> None:
    """A benchmark predicting the typical move must not get a free 25%.

    The rival here predicts the realised move exactly. The model's sigma
    implies exactly that same mean absolute move, so the two must tie —
    scoring sigma directly would hand the rival an unearned win.
    """
    sigma = 25.0
    implied = sigma * MEAN_ABS_OVER_SIGMA
    r = audit_vol_forecasts(
        _samples(sigma, [implied] * 100), benchmarks={"typical_move": [implied] * 100}
    )
    assert r.mae_pips == pytest.approx(0.0, abs=1e-9)
    assert r.beats_benchmarks


def test_losing_to_a_naive_benchmark_is_stated_plainly() -> None:
    # The rival nails every move; the model's implied mean move is far off.
    samples = _samples(20.0, [60.0] * 100)
    r = audit_vol_forecasts(samples, benchmarks={"yesterday": [60.0] * 100})
    assert not r.beats_benchmarks
    assert "not earning its keep" in r.verdict


def test_beating_the_benchmarks_is_stated_too() -> None:
    sigma = 30.0
    samples = _samples(sigma, [sigma * MEAN_ABS_OVER_SIGMA] * 100)  # MAE 0
    r = audit_vol_forecasts(samples, benchmarks={"yesterday": [5.0] * 100})
    assert r.beats_benchmarks
    assert "beats every naive benchmark" in r.verdict


def test_a_mismatched_benchmark_length_is_rejected() -> None:
    with pytest.raises(ValidationError):
        audit_vol_forecasts(_samples(20.0, [10.0] * 50), benchmarks={"x": [1.0] * 10})


# ---------- guards ----------


def test_no_samples_is_rejected() -> None:
    with pytest.raises(ValidationError):
        audit_vol_forecasts([])


def test_all_zero_forecasts_is_rejected_rather_than_dividing_by_zero() -> None:
    with pytest.raises(ValidationError):
        audit_vol_forecasts(_samples(0.0, [10.0] * 50))


def test_the_normal_reference_matches_the_textbook() -> None:
    assert normal_quantile_hit_rate(1.0) == pytest.approx(0.6827, abs=1e-4)
    assert normal_quantile_hit_rate(2.0) == pytest.approx(0.9545, abs=1e-4)
