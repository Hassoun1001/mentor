"""Multi-tipster leaderboard — rank track records, honestly.

Pure aggregation over already-realised outcomes. Tipsters are ranked by a
**risk-adjusted** return (mean return / dispersion) rather than raw return,
so a tipster who was right big once doesn't outrank a steadier one. With
fewer than two calls dispersion is undefined, so we fall back to the mean
return and flag the thin sample via ``tracked_calls``.

This is measurement, not a recommendation to follow anyone.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from mentor.domain.tips.scoring import TipOutcome


@dataclass(frozen=True, slots=True)
class LeaderboardRow:
    tipster: str
    tracked_calls: int
    mean_return_pct: Decimal
    win_rate: Decimal
    return_stdev: Decimal
    risk_adjusted: Decimal  # mean_return / (stdev + eps); higher = steadier edge
    best_ticker: str | None
    best_return_pct: Decimal
    avg_days_held: Decimal


def _stdev(values: Sequence[Decimal], mean: Decimal) -> Decimal:
    n = len(values)
    if n < 2:
        return Decimal("0")
    var = sum(((v - mean) * (v - mean) for v in values), Decimal("0")) / Decimal(n - 1)
    # Newton sqrt (Decimal-clean, mirrors the forecasting math).
    if var <= 0:
        return Decimal("0")
    x = var
    for _ in range(30):
        x = (x + var / x) / Decimal("2")
    return x


_EPS = Decimal("0.01")


def _row(tipster: str, outcomes: Sequence[TipOutcome]) -> LeaderboardRow:
    returns = [o.return_pct for o in outcomes]
    n = len(returns)
    mean = sum(returns, Decimal("0")) / Decimal(n)
    wins = sum(1 for r in returns if r > 0)
    stdev = _stdev(returns, mean)
    risk_adj = mean / (stdev + _EPS)
    best = max(outcomes, key=lambda o: o.return_pct)
    days = sum((Decimal(o.days_held) for o in outcomes), Decimal("0"))
    return LeaderboardRow(
        tipster=tipster,
        tracked_calls=n,
        mean_return_pct=mean.quantize(Decimal("0.01")),
        win_rate=(Decimal(wins) / Decimal(n)).quantize(Decimal("0.01")),
        return_stdev=stdev.quantize(Decimal("0.01")),
        risk_adjusted=risk_adj.quantize(Decimal("0.001")),
        best_ticker=best.ticker,
        best_return_pct=best.return_pct,
        avg_days_held=(days / Decimal(n)).quantize(Decimal("0.1")),
    )


def build_leaderboard(
    outcomes_by_tipster: Mapping[str, Sequence[TipOutcome]],
) -> tuple[LeaderboardRow, ...]:
    rows = [
        _row(tipster, outcomes)
        for tipster, outcomes in outcomes_by_tipster.items()
        if outcomes
    ]
    # Rank by risk-adjusted return, then raw mean as a tie-breaker.
    rows.sort(key=lambda r: (r.risk_adjusted, r.mean_return_pct), reverse=True)
    return tuple(rows)
