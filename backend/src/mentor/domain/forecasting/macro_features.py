"""Macro / FX-driver features — point-in-time, lookahead-safe.

EUR/USD is driven far more by the **US–German rate differential** and the
**dollar index** than by headlines — which is exactly *why* news tone came
out at 0% importance. These are the most fundamentally-defensible exogenous
features. They're still largely priced in, so we measure honestly and let
the promotion gate decide; but if anything exogenous is going to help the
direction model, it's this.

Sources (all from FRED, no key):

- ``DGS2``     US 2-year Treasury yield  -> ``us2y_chg_5`` (5-day change)
- ``T10Y2Y``   US 2s10s spread           -> ``us_2s10s`` (level; curve regime)
- ``DTWEXBGS`` Broad USD index           -> ``dxy_ret_5`` (5-day return; $ momentum)
- ``VIXCLS``   VIX                        -> ``vix_level`` (/100) + ``vix_chg_5``

Point-in-time: at a daily bar closing end-of-day D we use only macro
observations dated on or before D (``day <= asof``). Because FRED series
publish with varying lags, "on or before" naturally falls back to the most
recent value actually available — never a future one. When a series has no
data on/before the as-of date its features are neutral zeros, same as news.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Final

# The FRED series ids we ingest and consume.
FRED_SERIES_IDS: Final[tuple[str, ...]] = ("DGS2", "DGS10", "T10Y2Y", "VIXCLS", "DTWEXBGS")

MACRO_FEATURE_NAMES: Final[tuple[str, ...]] = (
    "us2y_chg_5",
    "us_2s10s",
    "dxy_ret_5",
    "vix_level",
    "vix_chg_5",
)

_LOOKBACK = 5  # trading-day lookback for change/return features
_NEUTRAL: Final[dict[str, float]] = dict.fromkeys(MACRO_FEATURE_NAMES, 0.0)


@dataclass(frozen=True, slots=True)
class MacroPoint:
    series_id: str
    day: datetime  # midnight UTC of the observation day
    value: float


class MacroSeries:
    """Multi-series macro history with point-in-time feature lookup.

    Points are grouped by series id and sorted by day; a parallel list of
    dates lets us binary-search the as-of cutoff so ``features_asof`` is
    O(log n) per series rather than scanning every point (the vol module
    taught us to avoid the accidental O(n^2)).
    """

    def __init__(self, points: Sequence[MacroPoint]) -> None:
        by_series: dict[str, list[MacroPoint]] = defaultdict(list)
        for p in points:
            by_series[p.series_id].append(p)
        self._values: dict[str, list[float]] = {}
        self._days: dict[str, list[date]] = {}
        for sid, pts in by_series.items():
            pts.sort(key=lambda p: p.day)
            self._values[sid] = [p.value for p in pts]
            self._days[sid] = [p.day.date() for p in pts]

    @property
    def empty(self) -> bool:
        return not self._values

    def _visible_count(self, series_id: str, cutoff: date) -> int:
        days = self._days.get(series_id)
        if not days:
            return 0
        return bisect.bisect_right(days, cutoff)

    def _latest_and_lag(self, series_id: str, cutoff: date, lag: int) -> tuple[float, float] | None:
        """(latest, value `lag` observations earlier) visible as of ``cutoff``."""
        n = self._visible_count(series_id, cutoff)
        if n == 0:
            return None
        values = self._values[series_id]
        latest = values[n - 1]
        prior = values[max(0, n - 1 - lag)]
        return latest, prior

    def features_asof(self, ts: datetime) -> dict[str, float]:
        cutoff = ts.date()
        if self.empty:
            return dict(_NEUTRAL)
        out = dict(_NEUTRAL)

        us2y = self._latest_and_lag("DGS2", cutoff, _LOOKBACK)
        if us2y is not None:
            out["us2y_chg_5"] = _clip(us2y[0] - us2y[1], 5.0)

        spread_n = self._visible_count("T10Y2Y", cutoff)
        if spread_n:
            out["us_2s10s"] = _clip(self._values["T10Y2Y"][spread_n - 1], 5.0)

        dxy = self._latest_and_lag("DTWEXBGS", cutoff, _LOOKBACK)
        if dxy is not None and dxy[1] != 0:
            out["dxy_ret_5"] = _clip((dxy[0] - dxy[1]) / dxy[1], 1.0)

        vix = self._latest_and_lag("VIXCLS", cutoff, _LOOKBACK)
        if vix is not None:
            out["vix_level"] = _clip(vix[0] / 100.0, 5.0)
            out["vix_chg_5"] = _clip((vix[0] - vix[1]) / 100.0, 5.0)

        return out


def _clip(value: float, bound: float) -> float:
    return max(-bound, min(bound, value))
