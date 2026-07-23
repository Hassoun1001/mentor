"""Higher-timeframe (HTF) context features — point-in-time, lookahead-safe.

The hourly model currently reads only hourly bars, so it is structurally
blind to the thing every trading book puts first: *what is the bigger
picture doing?* An hourly dip inside a daily uptrend and the same dip
inside a daily downtrend look identical to it.

These five features give an intraday model a compact read of the daily
chart — trend, momentum, volatility, and where price sits in its recent
daily range:

- ``htf_trend_dist``   distance of price from the daily slow EMA (normalised)
- ``htf_ema_spread``   fast-minus-slow daily EMA (normalised) — trend direction
- ``htf_rsi``          daily RSI (0–1) — bigger-picture momentum
- ``htf_atr_pct``      daily ATR / close — the regime's normal daily range
- ``htf_range_pos``    where price sits in the 20-day high/low band (0=low, 1=high)

**The lookahead rule is the whole ballgame.** A daily bar stamped
2026-07-18 is only *finished* at the end of that day, so an hourly bar at
2026-07-18 09:00 must not see it. ``features_asof`` therefore uses only
daily bars whose close time is strictly at or before the as-of timestamp
— i.e. bars stamped *before* the as-of day. Using the same-day bar would
leak the day's outcome into every hour of it and quietly inflate every
score, which is exactly the class of bug the embargo work was about.

Missing history yields neutral zeros, same convention as news and macro.
"""

from __future__ import annotations

import bisect
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Final

from mentor.domain.indicators import atr, ema, rsi
from mentor.domain.market.bars import PriceBar

HTF_FEATURE_NAMES: Final[tuple[str, ...]] = (
    "htf_trend_dist",
    "htf_ema_spread",
    "htf_rsi",
    "htf_atr_pct",
    "htf_range_pos",
)

_FAST = 10
_SLOW = 50
_RSI = 14
_ATR = 14
_RANGE = 20
# Enough closed daily bars for the slowest indicator plus a little slack.
_MIN_BARS: Final[int] = _SLOW + 5

_NEUTRAL: Final[dict[str, float]] = dict.fromkeys(HTF_FEATURE_NAMES, 0.0)


def _clip(value: float, bound: float) -> float:
    return max(-bound, min(bound, value))


class HtfSeries:
    """Daily-bar history with point-in-time feature lookup.

    Bars are sorted once and a parallel list of close-times supports a
    binary search for the as-of cutoff, so per-timestamp lookup is
    O(log n) plus the indicator window — not a rescan of all history.
    """

    def __init__(self, bars: Sequence[PriceBar]) -> None:
        ordered = sorted(bars, key=lambda b: b.ts)
        self._bars: list[PriceBar] = ordered
        # A bar stamped at `ts` is only complete once its period elapses.
        self._close_times: list[datetime] = [
            b.ts + timedelta(seconds=b.timeframe.seconds) for b in ordered
        ]

    @property
    def empty(self) -> bool:
        return not self._bars

    def _visible(self, ts: datetime) -> list[PriceBar]:
        """Bars whose period had *finished* at or before ``ts``."""
        n = bisect.bisect_right(self._close_times, ts)
        return self._bars[:n]

    def features_asof(self, ts: datetime) -> dict[str, float]:
        visible = self._visible(ts)
        if len(visible) < _MIN_BARS:
            return dict(_NEUTRAL)

        closes = [b.close for b in visible]
        last = closes[-1]
        if last <= 0:
            return dict(_NEUTRAL)

        fast = ema(closes, _FAST)
        slow = ema(closes, _SLOW)
        rsi_v = rsi(closes, _RSI)
        atr_v = atr(list(visible), _ATR)
        if fast is None or slow is None or rsi_v is None or atr_v is None:
            return dict(_NEUTRAL)

        window = visible[-_RANGE:]
        high = max(b.high for b in window)
        low = min(b.low for b in window)
        span = high - low

        out = dict(_NEUTRAL)
        out["htf_trend_dist"] = _clip(float((last - slow) / last), 1.0)
        out["htf_ema_spread"] = _clip(float((fast - slow) / last), 1.0)
        out["htf_rsi"] = float(rsi_v) / 100.0
        out["htf_atr_pct"] = _clip(float(atr_v / last), 1.0)
        out["htf_range_pos"] = (
            _clip(float((last - low) / span), 1.0) if span > 0 else 0.5
        )
        return out


def build_htf_by_ts(
    series: HtfSeries, timestamps: Sequence[datetime]
) -> dict[datetime, dict[str, float]]:
    """Per-bar HTF features keyed by the lower-timeframe bar timestamp."""
    return {ts: series.features_asof(ts) for ts in timestamps}


def neutral_htf_features() -> dict[str, float]:
    return dict(_NEUTRAL)


def htf_series_from_bars(bars: Sequence[PriceBar]) -> HtfSeries:
    return HtfSeries(bars)


__all__ = [
    "HTF_FEATURE_NAMES",
    "HtfSeries",
    "build_htf_by_ts",
    "htf_series_from_bars",
    "neutral_htf_features",
]
