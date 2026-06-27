"""Walk-forward validation.

> True held-out testing and rolling re-validation to expose overfitting.
> — Mentor product plan, §6.G

We slide a (train, test) window through history. The training slice is
where a tuner *would* tune; the test slice is the held-out reality. For
the baseline strategies in this engine, there's no parameter search, so
the train slice is informational — but the structure is built in for
when Phase 4 wires in a real ML model.

The key honesty test: does the test-slice expectancy stay positive when
the train slice does? If train looks great and test collapses, that's
the overfitting signature the plan warns about.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.backtest.engine import BacktestResult, run_backtest
from mentor.domain.backtest.metrics import BacktestMetrics, compute_metrics
from mentor.domain.backtest.strategy import Strategy
from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument
from mentor.domain.market.bars import PriceBar
from mentor.domain.money import Money


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    index: int
    train_metrics: BacktestMetrics
    test_metrics: BacktestMetrics
    train_bars: int
    test_bars: int


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    windows: tuple[WalkForwardWindow, ...]
    in_sample_avg_expectancy_r: Decimal
    out_of_sample_avg_expectancy_r: Decimal
    degradation_pct: Decimal | None
    final_test_metrics: BacktestMetrics | None

    @property
    def is_overfit_signal(self) -> bool:
        """A heuristic, not a verdict.

        Train expectancy clearly positive, test expectancy clearly worse
        (≥ 50% drop) → flag for review. The plan explicitly warns against
        deferring this judgement to a single number.
        """
        if self.degradation_pct is None:
            return False
        return self.in_sample_avg_expectancy_r > Decimal(
            "0.05"
        ) and self.degradation_pct >= Decimal("50")


def walk_forward(
    *,
    bars: Sequence[PriceBar],
    instrument: Instrument,
    strategy_factory: Callable[[], Strategy],
    starting_balance: Money,
    n_windows: int = 4,
    train_test_split: Decimal = Decimal("0.7"),
) -> WalkForwardResult:
    """Run a walk-forward pass.

    The series is divided into `n_windows` contiguous slices. Within
    each slice, the first `train_test_split` fraction is the train
    segment and the remainder is the test segment. The strategy factory
    is called fresh for each segment so state never leaks between them.
    """
    if n_windows < 1:
        raise ValidationError("n_windows must be >= 1", field="n_windows")
    if not (Decimal("0.1") <= train_test_split <= Decimal("0.95")):
        raise ValidationError("train_test_split must be in [0.1, 0.95]", field="train_test_split")
    if len(bars) < n_windows * 20:
        raise ValidationError(
            f"need at least {n_windows * 20} bars for {n_windows} windows; got {len(bars)}"
        )

    total = len(bars)
    slice_size = total // n_windows
    windows: list[WalkForwardWindow] = []

    in_sample: list[Decimal] = []
    out_of_sample: list[Decimal] = []

    for i in range(n_windows):
        start = i * slice_size
        end = total if i == n_windows - 1 else (i + 1) * slice_size
        slice_bars = list(bars[start:end])
        split_at = max(2, int(len(slice_bars) * float(train_test_split)))
        train_bars = slice_bars[:split_at]
        test_bars = slice_bars[split_at:]
        if not train_bars or not test_bars:
            continue

        train_result: BacktestResult = run_backtest(
            bars=train_bars,
            strategy=strategy_factory(),
            instrument=instrument,
            starting_balance=starting_balance,
        )
        test_result: BacktestResult = run_backtest(
            bars=test_bars,
            strategy=strategy_factory(),
            instrument=instrument,
            starting_balance=starting_balance,
        )
        train_m = compute_metrics(train_result)
        test_m = compute_metrics(test_result)
        windows.append(
            WalkForwardWindow(
                index=i,
                train_metrics=train_m,
                test_metrics=test_m,
                train_bars=len(train_bars),
                test_bars=len(test_bars),
            )
        )
        in_sample.append(train_m.expectancy_r)
        out_of_sample.append(test_m.expectancy_r)

    if not windows:
        raise ValidationError("no walk-forward windows produced results")

    avg_in = sum(in_sample, Decimal("0")) / Decimal(len(in_sample))
    avg_out = sum(out_of_sample, Decimal("0")) / Decimal(len(out_of_sample))
    degradation: Decimal | None = None
    if avg_in > 0:
        degradation = ((avg_in - avg_out) / avg_in) * Decimal("100")

    return WalkForwardResult(
        windows=tuple(windows),
        in_sample_avg_expectancy_r=avg_in,
        out_of_sample_avg_expectancy_r=avg_out,
        degradation_pct=degradation,
        final_test_metrics=windows[-1].test_metrics if windows else None,
    )
