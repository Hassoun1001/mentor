"""Is the best of many tries still better than luck?

Try enough trading rules on the same history and one of them will look
brilliant by chance alone. That is not a risk to manage; it is a
certainty to correct for. The correction here is the **deflated Sharpe
ratio** (Bailey & López de Prado, 2014), applied on the t-statistic scale:

1. Each trial's evidence is its trade t-statistic, ``mean R / sd R × √n``.
   Under "no edge" that is roughly standard normal *whatever n is*, which
   makes trials with different trade counts comparable — the paper's
   Sharpe-ratio form assumes every trial ran for the same length.
2. Across N trials of pure noise, the *largest* t to expect is
   ``E[max] ≈ (1-γ)·Φ⁻¹(1-1/N) + γ·Φ⁻¹(1-1/(N·e))`` — about 2.4 for 70
   trials, 3.0 for 500. When the recorded trials disagree with each other
   more than noise would (variance of their t-statistics above 1), the
   expectation is scaled up by that dispersion, never down.
3. A candidate passes only if its out-of-sample t-statistic beats that
   expected maximum by the app's usual 95% margin (``significance._Z``).

N is every configuration ever recorded in the trial ledger, not just this
candidate's. Forgetting failed trials is the classic way to make a
survivor look special, so the ledger is append-only and the bar only rises.

Non-normal returns get the paper's correction to the t-statistic, with
one deliberate asymmetry: the correction may only *penalise*. Strong
positive skew (common in trend following) would otherwise shrink the
denominator toward zero and manufacture an enormous score from a few
large winners.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist

from mentor.domain.stats.significance import _Z

_EULER_GAMMA = 0.5772156649015329
_NORMAL = NormalDist()

# The non-normality correction's denominator never drops below this, so
# skew and fat tails can raise the bar but never lower it. Pinned.
_MIN_SHARPE_DENOMINATOR = 1.0


@dataclass(frozen=True, slots=True)
class TradeStats:
    n: int
    mean: float
    sd: float
    sharpe: float  # per trade
    skew: float
    kurtosis: float  # not excess: a normal distribution scores 3
    t_stat: float  # mean / sd × √n
    t_adjusted: float  # with the (one-sided) non-normality penalty
    win_rate: float | None
    avg_win: float | None
    avg_loss: float | None  # positive number

    @property
    def breakeven_win_rate(self) -> float | None:
        """The win rate this payoff shape needs to break even, after costs."""
        if self.avg_win is None or self.avg_loss is None:
            return None
        return self.avg_loss / (self.avg_win + self.avg_loss)


def trade_stats(rs: Sequence[float]) -> TradeStats:
    n = len(rs)
    wins = [r for r in rs if r > 0]
    losses = [-r for r in rs if r < 0]
    avg_win = math.fsum(wins) / len(wins) if wins else None
    avg_loss = math.fsum(losses) / len(losses) if losses else None
    win_rate = len(wins) / n if n else None
    if n < 2:
        mean = rs[0] if rs else 0.0
        return TradeStats(n, mean, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, win_rate, avg_win, avg_loss)

    mean = math.fsum(rs) / n
    dev = [r - mean for r in rs]
    m2 = math.fsum(d * d for d in dev) / n
    sd = math.sqrt(m2 * n / (n - 1))
    if sd < 1e-12:
        return TradeStats(n, mean, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, win_rate, avg_win, avg_loss)
    skew = (math.fsum(d**3 for d in dev) / n) / m2**1.5
    kurtosis = (math.fsum(d**4 for d in dev) / n) / (m2 * m2)
    sharpe = mean / sd
    denominator = max(
        _MIN_SHARPE_DENOMINATOR, 1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe * sharpe
    )
    return TradeStats(
        n=n,
        mean=mean,
        sd=sd,
        sharpe=sharpe,
        skew=skew,
        kurtosis=kurtosis,
        t_stat=sharpe * math.sqrt(n),
        t_adjusted=sharpe * math.sqrt(n - 1) / math.sqrt(denominator),
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
    )


def expected_max_z(n_trials: int) -> float:
    """Expected maximum of ``n_trials`` independent standard normals (≈, for n ≥ 2)."""
    if n_trials <= 1:
        return 0.0
    return (1 - _EULER_GAMMA) * _NORMAL.inv_cdf(1 - 1 / n_trials) + _EULER_GAMMA * _NORMAL.inv_cdf(
        1 - 1 / (n_trials * math.e)
    )


def trial_dispersion(t_stats: Sequence[float]) -> float:
    """Variance of the recorded trials' t-statistics, never below pure noise's 1."""
    if len(t_stats) < 2:
        return 1.0
    mean = math.fsum(t_stats) / len(t_stats)
    var = math.fsum((t - mean) ** 2 for t in t_stats) / (len(t_stats) - 1)
    return max(1.0, var)


@dataclass(frozen=True, slots=True)
class DeflatedVerdict:
    t_adjusted: float
    null_max: float  # the best t-statistic luck alone would produce across the trials
    bar: float  # null_max plus the 95% margin: what the candidate must reach
    n_trials: int
    dispersion: float
    probability: float  # chance the edge is real after correcting for the trials
    passed: bool


def null_max_for(n_trials: int, dispersion: float = 1.0) -> float:
    """The best t-statistic luck alone should produce across ``n_trials``."""
    return math.sqrt(max(1.0, dispersion)) * expected_max_z(n_trials)


def deflated_bar(n_trials: int, dispersion: float = 1.0) -> float:
    """The score a candidate must reach: luck's best plus the 95% margin."""
    return null_max_for(n_trials, dispersion) + _Z


def deflate(stats: TradeStats, *, n_trials: int, dispersion: float = 1.0) -> DeflatedVerdict:
    null_max = null_max_for(n_trials, dispersion)
    bar = deflated_bar(n_trials, dispersion)
    return DeflatedVerdict(
        t_adjusted=stats.t_adjusted,
        null_max=null_max,
        bar=bar,
        n_trials=n_trials,
        dispersion=max(1.0, dispersion),
        probability=_NORMAL.cdf(stats.t_adjusted - null_max),
        passed=stats.n >= 2 and stats.mean > 0 and stats.t_adjusted >= bar,
    )
