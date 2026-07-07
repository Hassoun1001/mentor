"""Volatility feature engineering — point-in-time, lookahead-safe.

A parallel feature builder to ``features.py`` (which serves the *direction*
model), tuned for predicting realized volatility. Every feature at bar ``i``
is computed only from bars ``[0..i]`` — the same structural no-lookahead
guarantee, enforced by slicing in ``build_vol_feature_series``.

The set is deliberately small and vol-specific:

- ``rv_5`` / ``rv_10`` / ``rv_20`` — trailing realized vol (vol clusters, so
  its own recent history is the strongest predictor).
- ``atr_pct``      — ATR(14) as a fraction of price (range-based vol proxy).
- ``abs_ret_1``    — size of the last bar's move (persistence at lag 1).
- ``hl_range_pct`` — last bar's high-low range as a fraction of close.
- ``vol_of_vol``   — how much realized vol has itself been moving.
- ``dow``          — day-of-week; FX session/liquidity effects are real.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Final

from mentor.domain.forecasting.volatility import (
    log_returns,
    realized_vol,
)
from mentor.domain.indicators import atr
from mentor.domain.market.bars import PriceBar

VOL_FEATURE_NAMES: Final[tuple[str, ...]] = (
    "rv_5",
    "rv_10",
    "rv_20",
    "atr_pct",
    "abs_ret_1",
    "hl_range_pct",
    "vol_of_vol",
    "dow",
)

_RV_LONG = 20
_ATR = 14
_VOV_WINDOW = 10
# Need 20 returns (=> 21 closes) for rv_20, plus headroom for ATR and the
# rolling realized-vol series that feeds vol-of-vol.
_MIN_HISTORY: Final[int] = _RV_LONG + _VOV_WINDOW + 5


@dataclass(frozen=True, slots=True)
class VolFeatureRow:
    ts: datetime
    close: Decimal
    future_asof: datetime  # bar ts, restated for clarity at the call site
    features: dict[str, Decimal]


def build_vol_feature_row(bars: Sequence[PriceBar]) -> VolFeatureRow | None:
    """Compute the vol feature row at the latest bar. ``None`` if too short."""
    if len(bars) < _MIN_HISTORY:
        return None
    closes = [b.close for b in bars]
    last = bars[-1]
    if last.close <= 0:
        return None

    rets = log_returns(closes)
    if len(rets) < _RV_LONG:
        return None

    rv5 = realized_vol(rets, window=5)
    rv10 = realized_vol(rets, window=10)
    rv20 = realized_vol(rets, window=_RV_LONG)
    if rv5 is None or rv10 is None or rv20 is None:
        return None

    atr_v = atr(list(bars), _ATR)
    if atr_v is None:
        return None

    # vol-of-vol: dispersion of the recent trailing realized-vol series.
    # Compute only the last _VOV_WINDOW trailing-5 realized vols directly
    # (each over a bounded slice) so this stays O(1) per row rather than
    # rebuilding the whole rolling series.
    rv_tail: list[Decimal] = []
    for end in range(len(rets) - _VOV_WINDOW, len(rets)):
        if end < 1:
            continue
        seg = rets[max(0, end - 4) : end + 1]
        v = realized_vol(seg)
        if v is not None:
            rv_tail.append(v)
    vov = realized_vol(rv_tail) or Decimal("0")

    features = {
        "rv_5": rv5,
        "rv_10": rv10,
        "rv_20": rv20,
        "atr_pct": atr_v / last.close,
        "abs_ret_1": abs(rets[-1]),
        "hl_range_pct": (last.high - last.low) / last.close,
        "vol_of_vol": vov,
        "dow": Decimal(last.ts.weekday()),
    }
    assert set(features) == set(VOL_FEATURE_NAMES), "vol feature names drifted"
    return VolFeatureRow(ts=last.ts, close=last.close, future_asof=last.ts, features=features)


def build_vol_feature_series(bars: Sequence[PriceBar]) -> list[VolFeatureRow]:
    """One vol feature row per bar with enough history (training-time)."""
    out: list[VolFeatureRow] = []
    for i in range(_MIN_HISTORY - 1, len(bars)):
        row = build_vol_feature_row(bars[: i + 1])
        if row is not None:
            out.append(row)
    return out
