"""Drift-watch verdict tests (pure function — no DB, no scheduler)."""

from __future__ import annotations

from mentor.application.scheduler.drift import assess_drift


def _outcomes(*, p: float, y: int, n: int) -> list[tuple[float, int]]:
    return [(p, y)] * n


def test_too_few_samples_gives_no_verdict() -> None:
    verdict = assess_drift(
        _outcomes(p=0.9, y=0, n=10),  # terrible, but the window is tiny
        champion_brier=0.24,
        min_samples=25,
        margin=0.02,
    )
    assert verdict.retrain is False
    assert verdict.live_brier is None
    assert verdict.samples == 10


def test_healthy_live_brier_does_not_retrain() -> None:
    # Confidently right: p=0.8 on outcome 1 → Brier 0.04, well under threshold.
    verdict = assess_drift(
        _outcomes(p=0.8, y=1, n=40),
        champion_brier=0.24,
        min_samples=25,
        margin=0.02,
    )
    assert verdict.retrain is False
    assert verdict.live_brier is not None
    assert verdict.live_brier < 0.05


def test_degraded_live_brier_triggers_retrain() -> None:
    # Confidently wrong: p=0.8 on outcome 0 → Brier 0.64 >> 0.24 + 0.02.
    verdict = assess_drift(
        _outcomes(p=0.8, y=0, n=40),
        champion_brier=0.24,
        min_samples=25,
        margin=0.02,
    )
    assert verdict.retrain is True
    assert verdict.live_brier is not None
    assert verdict.live_brier > verdict.threshold  # type: ignore[operator]
    assert "drift" in verdict.reason


def test_no_champion_falls_back_to_coin_flip_threshold() -> None:
    # Without a champion figure the bar is 0.25 + margin. p=0.5 → 0.25 exactly:
    # not worse than a coin flip, so no retrain.
    steady = assess_drift(
        _outcomes(p=0.5, y=1, n=30),
        champion_brier=None,
        min_samples=25,
        margin=0.02,
    )
    assert steady.retrain is False
    # Confidently wrong crosses it.
    degraded = assess_drift(
        _outcomes(p=0.9, y=0, n=30),
        champion_brier=None,
        min_samples=25,
        margin=0.02,
    )
    assert degraded.retrain is True


def test_boundary_exactly_at_threshold_does_not_retrain() -> None:
    # live == threshold must NOT fire (strict inequality) — avoids flapping.
    # p=0.7 wrong every time → Brier 0.49; threshold set to exactly 0.49.
    verdict = assess_drift(
        _outcomes(p=0.7, y=0, n=30),
        champion_brier=0.47,
        min_samples=25,
        margin=0.02,
    )
    assert verdict.threshold is not None
    assert abs(verdict.live_brier - verdict.threshold) < 1e-12  # type: ignore[operator]
    assert verdict.retrain is False
