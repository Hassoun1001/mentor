"""Paper-trade the system's own live predictions.

Brier and ECE say "the probabilities are honest"; a trader asks "would
following the calls have made money?" This simulator answers that,
directly from the resolved-predictions audit table: every directional
call (optionally gated by confidence) becomes one hypothetical trade —
enter at the prediction's close, exit at the realised close, pay the
spread — compounding into an equity curve.

Honest framing (Principle 05): this is a *measurement* of the live
model's economics, not a promise. It ignores slippage beyond the fixed
spread, assumes fills at bar closes, and short histories are dominated
by luck. The point is a scoreboard the user can watch grow — and trust.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from mentor.domain.forecasting.forecast import Direction
from mentor.infrastructure.models import PredictionORM


@dataclass(frozen=True, slots=True)
class PaperPoint:
    ts: datetime
    equity: float


@dataclass(frozen=True, slots=True)
class PaperReport:
    trades: int
    skipped_low_confidence: int
    skipped_neutral: int
    wins: int
    losses: int
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    avg_trade_pct: float
    curve: tuple[PaperPoint, ...]
    note: str


_NOTE = (
    "Hypothetical: entries/exits at bar closes, charged the same round-trip "
    "friction the backtester applies. Short histories are luck; judge over "
    "100+ trades."
)

# Round-trip friction in price units: 0.8 pip spread + two 0.2 pip slippage
# legs, matching `CostModel`. Hardcoded here rather than imported so the
# domain simulator stays free of application wiring — the endpoint passes
# the live figure, and this only applies to direct callers.
_DEFAULT_ROUND_TRIP = 0.00012


def simulate_own_signals(
    rows: Sequence[PredictionORM],
    *,
    min_confidence: float = 0.0,
    spread: float = _DEFAULT_ROUND_TRIP,
) -> PaperReport:
    """Follow every resolved directional prediction as one paper trade.

    `spread` is round-trip friction in price units (0.00012 = 1.2 pips on
    EUR/USD) charged once per trade against the entry price. It must match
    the cost the breakeven hurdle is computed from: an equity curve priced
    at one cost and graded against a hurdle priced at another is two
    different questions wearing the same answer.
    """
    resolved = sorted(
        (r for r in rows if r.realised_close is not None),
        key=lambda r: r.asof,
    )

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    wins = 0
    losses = 0
    skipped_conf = 0
    skipped_neutral = 0
    returns: list[float] = []
    curve: list[PaperPoint] = []

    for r in resolved:
        if r.direction == Direction.NEUTRAL.value:
            skipped_neutral += 1
            continue
        if float(r.confidence) < min_confidence:
            skipped_conf += 1
            continue
        entry = float(r.asof_close)
        exit_ = float(r.realised_close)  # type: ignore[arg-type]
        if entry <= 0:
            continue
        sign = 1.0 if r.direction == Direction.LONG.value else -1.0
        ret = sign * (exit_ - entry) / entry - spread / entry
        returns.append(ret)
        if ret > 0:
            wins += 1
        else:
            losses += 1
        equity *= 1.0 + ret
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
        curve.append(PaperPoint(ts=r.horizon_at, equity=round(equity, 6)))

    trades = wins + losses
    return PaperReport(
        trades=trades,
        skipped_low_confidence=skipped_conf,
        skipped_neutral=skipped_neutral,
        wins=wins,
        losses=losses,
        win_rate=wins / trades if trades else 0.0,
        total_return_pct=(equity - 1.0) * 100,
        max_drawdown_pct=max_dd * 100,
        avg_trade_pct=(sum(returns) / trades * 100) if trades else 0.0,
        curve=tuple(curve),
        note=_NOTE,
    )
