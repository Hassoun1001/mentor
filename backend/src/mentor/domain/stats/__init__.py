"""Statistical honesty helpers — is a measured number distinguishable from luck?

Two questions, deliberately kept apart. `significance` asks whether a rate is
distinguishable from a baseline; `breakeven` supplies the baseline that makes
that question about money rather than about guessing.
"""

from mentor.domain.stats.breakeven import (
    MIN_WINDOWS,
    BreakevenBasis,
    breakeven_win_rate,
    estimate_breakeven,
    mean_abs_move,
)
from mentor.domain.stats.significance import (
    MeanVerdict,
    ProportionVerdict,
    assess_expectancy,
    assess_proportion,
    trades_needed,
    wilson_interval,
)

__all__ = [
    "MIN_WINDOWS",
    "BreakevenBasis",
    "MeanVerdict",
    "ProportionVerdict",
    "assess_expectancy",
    "assess_proportion",
    "breakeven_win_rate",
    "estimate_breakeven",
    "mean_abs_move",
    "trades_needed",
    "wilson_interval",
]
