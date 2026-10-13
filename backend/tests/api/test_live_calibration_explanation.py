"""The Loop page's live-calibration sentence must say what actually happened."""

from __future__ import annotations

from mentor.api.v1.forecasting import LiveCalibrationResponse, _explain_live_calibration


def test_a_waiting_champion_reports_progress_toward_the_floor() -> None:
    text = _explain_live_calibration(
        LiveCalibrationResponse(model_name="auto_a", independent_outcomes=6)
    )
    assert "6 of the 30" in text
    assert "keeps the calibration it learned in training" in text


def test_an_active_correction_is_explained_with_its_evidence() -> None:
    text = _explain_live_calibration(
        LiveCalibrationResponse(
            model_name="auto_a",
            independent_outcomes=40,
            decided_on=40,
            active=True,
            slope=0.5,
            n_fit=20,
            n_holdout=20,
            brier_before=0.29,
            brier_after=0.26,
            example_to=0.5503,
        )
    )
    assert "overconfident" in text
    assert "60% is shown as 55%" in text
    assert "0.2900 → 0.2600" in text
    assert "never which way it leans" in text


def test_a_refused_correction_says_so() -> None:
    text = _explain_live_calibration(
        LiveCalibrationResponse(
            model_name="auto_a",
            independent_outcomes=41,
            decided_on=40,
            reason="Slope 0.40 ... — not applied.",
        )
    )
    assert "left unchanged" in text and "not applied" in text


def test_the_baseline_has_nothing_to_correct() -> None:
    text = _explain_live_calibration(LiveCalibrationResponse(model_name="baseline"))
    assert "baseline rule" in text
