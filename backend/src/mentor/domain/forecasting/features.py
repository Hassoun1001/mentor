"""Feature engineering.

Every feature is computed **point-in-time**: at bar `i`, only bars `[0..i]`
contribute. This is the same lookahead-safety guarantee the backtester
enforces structurally; here it's enforced by the function signatures —
each transformer takes a `closes` / `bars` sequence and returns one row.

The feature set is intentionally small and transparent. The plan calls
out exactly these families (§6.D): indicators, lagged returns, distance
from key levels, news features (deferred — those come from the news
service and are merged in by the inference service).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Final

from mentor.domain.indicators import atr, ema, rsi
from mentor.domain.market.bars import PriceBar


@dataclass(frozen=True, slots=True)
class FeatureRow:
    ts: datetime
    close: Decimal
    features: dict[str, Decimal]


FEATURE_NAMES: Final[tuple[str, ...]] = (
    "ret_1",
    "ret_5",
    "ret_10",
    "ema_fast_dist",
    "ema_slow_dist",
    "ema_fast_minus_slow",
    "rsi_14",
    "macd_line",
    "atr_pct",
    "high_20_dist",
    "low_20_dist",
    "vol_20",
)

_FAST = 12
_SLOW = 26
_RSI = 14
_ATR = 14
_RANGE = 20
_VOL = 20
_MIN_HISTORY: Final[int] = max(_SLOW + 5, _ATR + 5, _RSI + 5, _RANGE + 5, _VOL + 5)


def _ret(values: Sequence[Decimal], lag: int) -> Decimal | None:
    if len(values) <= lag or values[-lag - 1] == 0:
        return None
    return (values[-1] - values[-lag - 1]) / values[-lag - 1]


def _std(values: Sequence[Decimal]) -> Decimal:
    if len(values) < 2:
        return Decimal("0")
    mean = sum(values, Decimal("0")) / Decimal(len(values))
    variance = sum(((v - mean) * (v - mean) for v in values), Decimal("0")) / Decimal(
        len(values) - 1
    )
    # Decimal sqrt: use Newton's iteration for portability.
    if variance == 0:
        return Decimal("0")
    x = variance
    for _ in range(30):
        x = (x + variance / x) / Decimal("2")
    return x


def build_feature_row(bars: Sequence[PriceBar]) -> FeatureRow | None:
    """Compute the feature row at the *latest* bar in `bars`.

    Returns `None` if there isn't enough history.
    """
    if len(bars) < _MIN_HISTORY:
        return None

    closes = [b.close for b in bars]
    current = bars[-1]
    last_close = current.close

    fast = ema(closes, _FAST)
    slow = ema(closes, _SLOW)
    if fast is None or slow is None or last_close == 0:
        return None

    rsi_v = rsi(closes, _RSI)
    if rsi_v is None:
        return None

    atr_v = atr(list(bars), _ATR)
    if atr_v is None:
        return None

    # 20-bar high/low
    window = bars[-_RANGE:]
    high20 = max(b.high for b in window)
    low20 = min(b.low for b in window)

    # Returns over the last `_VOL` bars
    recent_rets: list[Decimal] = []
    for i in range(max(0, len(closes) - _VOL), len(closes) - 1):
        prev = closes[i]
        nxt = closes[i + 1]
        if prev > 0:
            recent_rets.append((nxt - prev) / prev)
    vol20 = _std(recent_rets)

    ret1 = _ret(closes, 1) or Decimal("0")
    ret5 = _ret(closes, 5) or Decimal("0")
    ret10 = _ret(closes, 10) or Decimal("0")

    features = {
        "ret_1": ret1,
        "ret_5": ret5,
        "ret_10": ret10,
        "ema_fast_dist": (last_close - fast) / last_close,
        "ema_slow_dist": (last_close - slow) / last_close,
        "ema_fast_minus_slow": (fast - slow) / last_close,
        "rsi_14": rsi_v / Decimal("100"),
        "macd_line": (fast - slow) / last_close,
        "atr_pct": atr_v / last_close,
        "high_20_dist": (high20 - last_close) / last_close,
        "low_20_dist": (last_close - low20) / last_close,
        "vol_20": vol20,
    }

    assert set(features) == set(FEATURE_NAMES), "feature names drifted from FEATURE_NAMES"
    return FeatureRow(ts=current.ts, close=last_close, features=features)


def build_feature_series(bars: Sequence[PriceBar]) -> list[FeatureRow]:
    """Produce one feature row per bar that has enough history.

    Used at training time. At each step we slice `bars[:i+1]` so the row
    at index `i` can only see bars up to and including `i` — preventing
    lookahead in feature construction.
    """
    out: list[FeatureRow] = []
    for i in range(_MIN_HISTORY - 1, len(bars)):
        row = build_feature_row(bars[: i + 1])
        if row is not None:
            out.append(row)
    return out
