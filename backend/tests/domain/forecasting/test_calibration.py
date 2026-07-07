"""Calibration metric tests — ECE + reliability bins."""

from __future__ import annotations

from mentor.domain.forecasting.calibration import (
    expected_calibration_error,
    reliability_bins,
)


def test_perfectly_calibrated_has_zero_ece() -> None:
    # Predicted probability equals the realised rate in each bin -> ECE 0.
    probs = [0.0, 0.0, 1.0, 1.0]
    outcomes = [0, 0, 1, 1]
    assert expected_calibration_error(probs, outcomes, n_bins=10) < 1e-9


def test_overconfident_has_positive_ece() -> None:
    # Predict 0.9 but only half actually happen -> gap of ~0.4 in that bin.
    probs = [0.9, 0.9, 0.9, 0.9]
    outcomes = [1, 0, 1, 0]
    ece = expected_calibration_error(probs, outcomes, n_bins=10)
    assert abs(ece - 0.4) < 1e-9


def test_reliability_bins_report_predicted_and_empirical() -> None:
    probs = [0.15, 0.15, 0.85, 0.85]
    outcomes = [0, 1, 1, 1]
    bins = reliability_bins(probs, outcomes, n_bins=10)
    assert len(bins) == 2
    low, high = bins
    assert abs(low.predicted_mean - 0.15) < 1e-9
    assert abs(low.empirical_rate - 0.5) < 1e-9  # one of two went up
    assert abs(high.empirical_rate - 1.0) < 1e-9
    assert low.count == 2 and high.count == 2


def test_empty_is_zero() -> None:
    assert expected_calibration_error([], []) == 0.0
    assert reliability_bins([], []) == []


def test_probability_of_one_lands_in_last_bin() -> None:
    bins = reliability_bins([1.0], [1], n_bins=10)
    assert len(bins) == 1
    assert bins[0].count == 1
