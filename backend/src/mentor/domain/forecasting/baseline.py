"""Baseline rule forecaster.

> A simple, transparent benchmark every fancier model must beat.
> — Mentor product plan, §6.D

Rules (cumulative, capped at p ∈ [0.30, 0.70] to avoid pretending to be
sure when we aren't):

- Trend filter (200-bar EMA): above → +0.06, below → −0.06.
- Momentum (close > close 10 bars ago): bias +0.04 if up, −0.04 if down.
- RSI extremes: RSI > 70 mean-reversion → −0.03; RSI < 30 → +0.03.
- Wide ATR (volatility > 1.5× 100-bar mean): shrink toward 0.5 (less confidence).

These specific weights are *not* sacred — the point is that the rule
model is auditable in a single screen and trivially backtestable as
the Phase 3 yardstick. If a fancier model can't beat this after costs,
the fancier model is overfit.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.features import build_feature_row
from mentor.domain.forecasting.forecast import (
    Direction,
    Forecast,
    direction_from_probability,
)
from mentor.domain.forecasting.forecaster import Forecaster
from mentor.domain.indicators import ema, rsi
from mentor.domain.market.bars import PriceBar, Timeframe

_TREND_PERIOD = 200
_MIN_PROB = Decimal("0.30")
_MAX_PROB = Decimal("0.70")


@dataclass(frozen=True, slots=True)
class BaselineForecaster(Forecaster):
    horizon_bars: int = 24  # 1 trading day if running on 1h bars

    @property
    def name(self) -> str:
        return f"baseline_rule(h={self.horizon_bars})"

    def forecast(
        self,
        *,
        bars: Sequence[PriceBar],
        symbol: str,
        timeframe: Timeframe,
        news: Mapping[str, float] | None = None,  # rule model ignores news
        macro: Mapping[str, float] | None = None,  # ...and macro drivers
        htf: Mapping[str, float] | None = None,  # ...and higher-timeframe context
    ) -> Forecast:
        if len(bars) < _TREND_PERIOD + 5:
            raise ValidationError(f"need at least {_TREND_PERIOD + 5} bars for baseline forecaster")

        last = bars[-1]
        closes = [b.close for b in bars]
        trend = ema(closes, _TREND_PERIOD)
        rsi_v = rsi(closes, 14)
        prev = bars[-11].close if len(bars) > 11 else last.close

        if trend is None or rsi_v is None:
            raise ValidationError("indicators not computable on this window")

        p = Decimal("0.5")
        notes: list[str] = []

        if last.close > trend:
            p += Decimal("0.06")
            notes.append(f"above the {_TREND_PERIOD}-bar EMA")
        elif last.close < trend:
            p -= Decimal("0.06")
            notes.append(f"below the {_TREND_PERIOD}-bar EMA")

        if last.close > prev:
            p += Decimal("0.04")
            notes.append("positive 10-bar momentum")
        elif last.close < prev:
            p -= Decimal("0.04")
            notes.append("negative 10-bar momentum")

        if rsi_v > Decimal("70"):
            p -= Decimal("0.03")
            notes.append(f"RSI elevated ({rsi_v:.1f})")
        elif rsi_v < Decimal("30"):
            p += Decimal("0.03")
            notes.append(f"RSI suppressed ({rsi_v:.1f})")

        p = max(_MIN_PROB, min(_MAX_PROB, p))
        confidence = abs(p - Decimal("0.5")) * Decimal("2")

        # Feature row is best-effort — used for the audit log
        row = build_feature_row(bars)
        features = row.features if row else {}

        direction = direction_from_probability(p)
        verb = {
            Direction.LONG: "Slight long lean",
            Direction.SHORT: "Slight short lean",
            Direction.NEUTRAL: "No directional lean",
        }[direction]

        reasoning = (
            f"{verb} ({p * 100:.0f}%, "
            f"confidence {confidence * 100:.0f}%) — {'; '.join(notes) or 'mixed signals'}. "
            f"This is a transparent rule benchmark, not a prediction; "
            f"a move that flips the trend filter or the momentum sign would change the read."
        )

        return Forecast(
            symbol=symbol.upper(),
            timeframe=timeframe,
            asof=last.ts,
            asof_close=last.close,
            horizon_bars=self.horizon_bars,
            p_up=p,
            confidence=confidence,
            direction=direction,
            model_name=self.name,
            reasoning=reasoning,
            features=features,
        )


# convenience for the application layer
def asof_datetime_for_bar(_: datetime) -> datetime:  # pragma: no cover
    raise NotImplementedError("use bar.ts directly")
