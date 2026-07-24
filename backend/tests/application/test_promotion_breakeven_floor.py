"""A model can be honestly calibrated and still not worth trading.

Brier measures whether the stated probabilities match reality. It knows
nothing about the spread, so it cannot distinguish "right 51% of the
time" from "profitable" — and on the 24-bar EUR/USD lane those are
opposite verdicts, because a call has to clear 52.36% before it covers
its own friction. The gate used to promote on Brier alone.
"""

from __future__ import annotations

import random

from mentor.application.forecasting.economics import horizon_for, round_trip_cost_price
from mentor.application.forecasting.promotion import clears_floors
from mentor.config import Settings
from mentor.domain.stats.breakeven import BreakevenBasis, estimate_breakeven
from mentor.infrastructure.forecasting.sklearn_forecaster import TrainingReport

# Comfortably inside the Brier floor (0.25 - 0.002), so the Brier gate is
# never what blocks these cases — the point is what the other floors do.
_GOOD_BRIER = 0.240


def _report(*, accuracy: float, coverage: float = 1.0, margin: float = 0.0) -> TrainingReport:
    covered = margin > 0.0
    return TrainingReport(
        n_samples=5_000,
        n_train=4_000,
        n_test=1_000,
        train_accuracy=accuracy,
        test_accuracy=accuracy,
        test_log_loss=0.69,
        test_brier=_GOOD_BRIER,
        horizon_bars=24,
        abstain_margin=margin,
        coverage=coverage,
        n_covered=int(1_000 * coverage) if covered else 0,
        test_brier_covered=_GOOD_BRIER if covered else 0.0,
        test_accuracy_covered=accuracy if covered else 0.0,
    )


def _basis(breakeven: float, *, measured: bool = True) -> BreakevenBasis:
    return BreakevenBasis(
        breakeven=breakeven,
        # The live 1h-lane figures: 0.218% typical 24-bar move against 1.2
        # pips of round-trip friction (0.8 spread + two 0.2 slippage legs).
        mean_abs_move=0.00218,
        cost_per_trade=0.000103,
        n_windows=89,
        measured=measured,
        note="",
    )


# ---------- the defect ----------


def test_beating_a_coin_flip_is_not_enough_to_ship() -> None:
    """51% is significantly better than chance and loses money anyway."""
    passed, detail = clears_floors(
        _report(accuracy=0.51), brier=_GOOD_BRIER, economics=_basis(0.5236)
    )
    assert not passed
    assert "51.0%" in detail
    assert "52.36%" in detail
    assert "lose money" in detail


def test_clearing_the_breakeven_ships() -> None:
    passed, detail = clears_floors(
        _report(accuracy=0.53), brier=_GOOD_BRIER, economics=_basis(0.5236)
    )
    assert passed
    assert detail == ""


def test_the_boundary_is_inclusive() -> None:
    passed, _ = clears_floors(
        _report(accuracy=0.5236), brier=_GOOD_BRIER, economics=_basis(0.5236)
    )
    assert passed


def test_the_easier_lane_admits_what_the_harder_one_rejects() -> None:
    """The same 51% model: dead on the 24-hour lane, alive on the 5-day
    one, because a fixed cost is a smaller share of a bigger move. Grading
    both against 50% made these two indistinguishable."""
    report = _report(accuracy=0.51)
    h1, _ = clears_floors(report, brier=_GOOD_BRIER, economics=_basis(0.5236))
    d1, _ = clears_floors(report, brier=_GOOD_BRIER, economics=_basis(0.5073))
    assert not h1
    assert d1


# ---------- the floors still compose ----------


def test_a_bad_brier_still_blocks_a_profitable_looking_hit_rate() -> None:
    passed, _ = clears_floors(
        _report(accuracy=0.60), brier=0.249, economics=_basis(0.5236)
    )
    assert not passed


def test_abstaining_down_to_a_lucky_sliver_still_blocks() -> None:
    passed, detail = clears_floors(
        _report(accuracy=0.80, coverage=0.04, margin=0.2),
        brier=_GOOD_BRIER,
        economics=_basis(0.5236),
    )
    assert not passed
    assert "abstains" in detail


def test_an_abstaining_model_is_judged_on_the_hours_it_acts() -> None:
    """`effective_accuracy` must follow the covered slice, not all hours —
    the same trap that made abstention inert in production when the
    metadata loader dropped the covered fields."""
    report = _report(accuracy=0.55, coverage=0.30, margin=0.1)
    assert report.effective_accuracy == 0.55
    passed, _ = clears_floors(report, brier=_GOOD_BRIER, economics=_basis(0.5236))
    assert passed


# ---------- the unmeasurable case ----------


def test_an_unmeasurable_hurdle_falls_back_rather_than_freezing_the_loop() -> None:
    """Too few windows to estimate the move distribution: the economic
    floor stands down and the other two still apply. Refusing every
    promotion on a number we cannot compute would stop the system
    learning, which is worse than the status quo it replaces."""
    passed, detail = clears_floors(
        _report(accuracy=0.505),
        brier=_GOOD_BRIER,
        economics=_basis(0.5, measured=False),
    )
    assert passed
    assert detail == ""


# ---------- the real lanes ----------


def test_the_configured_lanes_produce_the_hurdles_the_docs_claim() -> None:
    """Guards the numbers quoted in the module docs and the promotion
    reasons against a config change that silently moves them."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    cost = round_trip_cost_price(settings.loop_symbol)

    # A synthetic series with EUR/USD-like dispersion; the assertion is on
    # the *ordering and shape* of the two hurdles, not on live data.
    rng = random.Random(11)
    closes = [1.08]
    for _ in range(6_000):
        closes.append(closes[-1] + rng.uniform(-0.0004, 0.0004))

    h1 = estimate_breakeven(
        closes,
        horizon_bars=horizon_for("1h", settings),
        cost_per_trade_price=cost,
    )
    d1 = estimate_breakeven(
        closes,
        horizon_bars=horizon_for("1d", settings) * 24,  # a week of hourly bars
        cost_per_trade_price=cost,
    )

    assert h1.measured and d1.measured
    assert h1.breakeven > d1.breakeven > 0.5
    assert h1.hurdle_pp > 0.0
