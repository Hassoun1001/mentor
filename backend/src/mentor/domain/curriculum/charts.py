"""Deterministic chart data for the book.

Charts are described as data and drawn by one generic frontend component, so a
lesson can ask for a labelled candlestick or result chart without hand-written
SVG. Every chart declares what its numbers are:

* ``illustrative`` — made-up prices drawn to show a shape. Never a real market.
* ``calculated`` — exact maths or a simulation from assumptions stated in the
  caption.
* ``published`` — figures reported by a named source, redrawn here.

All randomness is seeded, so the same lesson always shows the same chart.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

Tone = Literal["fg", "muted", "accent", "accentSoft", "warn", "danger"]
DataKind = Literal["illustrative", "calculated", "published"]
Panel = Literal["main", "lower"]
Place = Literal["explain", "example"]
YFormat = Literal["price", "pct", "plain", "r", "usd"]
Num = float | None
OHLC = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class Series:
    name: str
    values: tuple[Num, ...]
    tone: Tone = "accent"
    style: Literal["line", "dashed", "area", "bars"] = "line"
    panel: Panel = "main"


@dataclass(frozen=True, slots=True)
class HLine:
    y: float
    label: str = ""
    tone: Tone = "muted"
    panel: Panel = "main"


@dataclass(frozen=True, slots=True)
class Zone:
    y0: float
    y1: float
    label: str = ""
    tone: Tone = "accent"
    x0: int | None = None
    x1: int | None = None


@dataclass(frozen=True, slots=True)
class Mark:
    x: int
    y: float
    label: str = ""
    tone: Tone = "fg"
    shape: Literal["dot", "up", "down"] = "dot"


@dataclass(frozen=True, slots=True)
class Segment:
    x0: float
    y0: float
    x1: float
    y1: float
    label: str = ""
    tone: Tone = "accent"


@dataclass(frozen=True, slots=True)
class Bar:
    label: str
    value: float
    tone: Tone = "accent"


@dataclass(frozen=True, slots=True, kw_only=True)
class Chart:
    title: str
    caption: str
    data_kind: DataKind
    kind: Literal["candles", "lines", "bars"]
    place: Place = "explain"
    candles: tuple[OHLC, ...] = ()
    series: tuple[Series, ...] = ()
    hlines: tuple[HLine, ...] = ()
    zones: tuple[Zone, ...] = ()
    marks: tuple[Mark, ...] = ()
    segments: tuple[Segment, ...] = ()
    bars: tuple[Bar, ...] = ()
    x_labels: tuple[str, ...] = ()
    x_label: str = ""
    y_label: str = ""
    y_format: YFormat = "price"
    lower_title: str = ""
    source_note: str = ""


# ---------------------------------------------------------------------------
# Synthetic price paths
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Path:
    """Made-up candles plus made-up volume, built to show a particular shape."""

    candles: tuple[OHLC, ...]
    volume: tuple[float, ...]

    @property
    def closes(self) -> tuple[float, ...]:
        return tuple(c[3] for c in self.candles)

    @property
    def highs(self) -> tuple[float, ...]:
        return tuple(c[1] for c in self.candles)

    @property
    def lows(self) -> tuple[float, ...]:
        return tuple(c[2] for c in self.candles)

    def __len__(self) -> int:
        return len(self.candles)


def _rounder(price: float) -> int:
    return max(0, 4 - math.floor(math.log10(abs(price) or 1.0)))


def path(
    knots: Sequence[tuple[int, float]],
    *,
    seed: int = 7,
    noise: float = 0.3,
    candle_range: float | None = None,
) -> Path:
    """Candles whose closes pass exactly through each ``(index, price)`` knot.

    Between knots the close follows a straight line plus seeded noise. Knots
    land exactly, so a lesson can draw a label at the very point it is about.
    """
    if len(knots) < 2 or knots[0][0] != 0:
        raise ValueError("a path needs at least two knots starting at index 0")
    rng = random.Random(seed)
    last = knots[-1][0]
    pivots = dict(knots)
    points = sorted(knots)
    moves = [abs(b[1] - a[1]) / max(b[0] - a[0], 1) for a, b in pairwise(points)]
    step = max(sum(moves) / len(moves), abs(points[0][1]) * 1e-5)
    wick = candle_range if candle_range is not None else step * 1.1
    digits = _rounder(points[0][1])

    closes: list[float] = []
    segment = 0
    for i in range(last + 1):
        while i > points[segment + 1][0]:
            segment += 1
        (x0, y0), (x1, y1) = points[segment], points[segment + 1]
        target = y0 + (y1 - y0) * (i - x0) / (x1 - x0)
        jitter = 0.0 if i in pivots else rng.gauss(0.0, noise * step * 2.2)
        closes.append(target + jitter)

    bars: list[OHLC] = []
    volume: list[float] = []
    prior = closes[0] - (closes[1] - closes[0]) * 0.5
    for close in closes:
        open_ = prior
        top = max(open_, close) + abs(rng.gauss(0.0, wick * 0.5))
        bottom = min(open_, close) - abs(rng.gauss(0.0, wick * 0.5))
        rounded = (
            round(open_, digits),
            round(top, digits),
            round(bottom, digits),
            round(close, digits),
        )
        bars.append(rounded)
        # Bigger candles tend to trade more volume; the noise keeps it uneven.
        size = 1 + abs(close - open_) / (wick * 3 + 1e-12)
        volume.append(round(100 * (0.7 + rng.random() * 0.6) * size, 1))
        prior = close
    return Path(tuple(bars), tuple(volume))


def random_walk(n: int, *, seed: int, start: float = 100.0, vol: float = 0.8) -> Path:
    """A pure coin-flip price path: by construction it has no pattern to find."""
    rng = random.Random(seed)
    bars: list[OHLC] = []
    volume: list[float] = []
    close = start
    for _ in range(n):
        open_ = close
        close = open_ + rng.gauss(0.0, vol)
        top = max(open_, close) + abs(rng.gauss(0.0, vol * 0.5))
        bottom = min(open_, close) - abs(rng.gauss(0.0, vol * 0.5))
        bars.append((round(open_, 3), round(top, 3), round(bottom, 3), round(close, 3)))
        volume.append(round(100 * (0.7 + rng.random() * 0.6), 1))
    return Path(tuple(bars), tuple(volume))


# ---------------------------------------------------------------------------
# Indicators — computed on the chart's own candles, so overlays are genuine
# ---------------------------------------------------------------------------


def sma(values: Sequence[float], n: int) -> tuple[Num, ...]:
    out: list[Num] = []
    for i in range(len(values)):
        out.append(None if i + 1 < n else sum(values[i + 1 - n : i + 1]) / n)
    return tuple(out)


def ema(values: Sequence[float], n: int) -> tuple[Num, ...]:
    alpha = 2 / (n + 1)
    out: list[Num] = []
    current: float | None = None
    for i, value in enumerate(values):
        if i + 1 < n:
            out.append(None)
            continue
        if current is None:
            current = sum(values[i + 1 - n : i + 1]) / n
        else:
            current = alpha * value + (1 - alpha) * current
        out.append(current)
    return tuple(out)


def rsi(values: Sequence[float], n: int = 14) -> tuple[Num, ...]:
    out: list[Num] = [None] * len(values)
    gains = 0.0
    losses = 0.0
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gain, loss = max(change, 0.0), max(-change, 0.0)
        if i <= n:
            gains += gain / n
            losses += loss / n
        else:
            gains = (gains * (n - 1) + gain) / n
            losses = (losses * (n - 1) + loss) / n
        if i >= n:
            out[i] = 100.0 if losses == 0 else 100.0 - 100.0 / (1.0 + gains / losses)
    return tuple(out)


def bollinger(
    values: Sequence[float], n: int = 20, k: float = 2.0
) -> tuple[tuple[Num, ...], tuple[Num, ...], tuple[Num, ...]]:
    mid = sma(values, n)
    upper: list[Num] = []
    lower: list[Num] = []
    for i, centre in enumerate(mid):
        if centre is None:
            upper.append(None)
            lower.append(None)
            continue
        window = values[i + 1 - n : i + 1]
        dev = math.sqrt(sum((v - centre) ** 2 for v in window) / n)
        upper.append(centre + k * dev)
        lower.append(centre - k * dev)
    return tuple(upper), mid, tuple(lower)


def atr(p: Path, n: int = 14) -> tuple[Num, ...]:
    ranges: list[float] = []
    prev_close = p.candles[0][0]
    for _, high, low, close in p.candles:
        ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
        prev_close = close
    return sma(ranges, n)


def macd(
    values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[tuple[Num, ...], tuple[Num, ...], tuple[Num, ...]]:
    fast_line = ema(values, fast)
    slow_line = ema(values, slow)
    line: tuple[Num, ...] = tuple(
        (f - s) if f is not None and s is not None else None
        for f, s in zip(fast_line, slow_line, strict=True)
    )
    start = next(i for i, v in enumerate(line) if v is not None)
    tail = ema([v for v in line[start:] if v is not None], signal)
    signal_line: tuple[Num, ...] = (None,) * start + tail
    hist: tuple[Num, ...] = tuple(
        (m - s) if m is not None and s is not None else None
        for m, s in zip(line, signal_line, strict=True)
    )
    return line, signal_line, hist


def vwap(p: Path) -> tuple[Num, ...]:
    total_value = 0.0
    total_volume = 0.0
    out: list[Num] = []
    for (_, high, low, close), vol in zip(p.candles, p.volume, strict=True):
        total_value += (high + low + close) / 3 * vol
        total_volume += vol
        out.append(total_value / total_volume)
    return tuple(out)


# ---------------------------------------------------------------------------
# Result curves
# ---------------------------------------------------------------------------


def equity_paths(
    *,
    n_paths: int,
    n_trades: int,
    win_rate: float,
    win_r: float,
    risk_pct: float,
    seed: int,
) -> tuple[Series, ...]:
    """Seeded account curves, compounding a fixed % risk per trade (start = 100)."""
    rng = random.Random(seed)
    out: list[Series] = []
    for k in range(n_paths):
        equity = 100.0
        curve: list[Num] = [equity]
        for _ in range(n_trades):
            r = win_r if rng.random() < win_rate else -1.0
            equity *= 1 + risk_pct / 100 * r
            curve.append(round(equity, 3))
        out.append(Series(name=f"Path {k + 1}", values=tuple(curve), tone="muted"))
    return tuple(out)


# ---------------------------------------------------------------------------
# More indicators, computed the same way: on the chart's own candles
# ---------------------------------------------------------------------------


def stochastic(p: Path, n: int = 14, smooth: int = 3) -> tuple[tuple[Num, ...], tuple[Num, ...]]:
    """%K (where the close sits in the recent high-low range) and %D (its average)."""
    k: list[Num] = []
    for i, (_, _, _, close) in enumerate(p.candles):
        if i + 1 < n:
            k.append(None)
            continue
        high = max(p.highs[i + 1 - n : i + 1])
        low = min(p.lows[i + 1 - n : i + 1])
        k.append(50.0 if high == low else 100.0 * (close - low) / (high - low))
    start = n - 1
    known = [v for v in k[start:] if v is not None]
    d: tuple[Num, ...] = (None,) * start + sma(known, smooth)
    return tuple(k), d


def adx(p: Path, n: int = 14) -> tuple[tuple[Num, ...], tuple[Num, ...], tuple[Num, ...]]:
    """Wilder's ADX with its +DI and -DI lines."""
    size = len(p.candles)
    tr = [0.0] * size
    plus_dm = [0.0] * size
    minus_dm = [0.0] * size
    for i in range(1, size):
        high, low = p.highs[i], p.lows[i]
        prev_close = p.closes[i - 1]
        up = high - p.highs[i - 1]
        down = p.lows[i - 1] - low
        tr[i] = max(high - low, abs(high - prev_close), abs(low - prev_close))
        plus_dm[i] = up if up > down and up > 0 else 0.0
        minus_dm[i] = down if down > up and down > 0 else 0.0

    plus: list[Num] = [None] * size
    minus: list[Num] = [None] * size
    dx: list[float] = [0.0] * size
    atr_n = sum(tr[1 : n + 1])
    plus_n = sum(plus_dm[1 : n + 1])
    minus_n = sum(minus_dm[1 : n + 1])
    for i in range(n, size):
        if i > n:
            atr_n += tr[i] - atr_n / n
            plus_n += plus_dm[i] - plus_n / n
            minus_n += minus_dm[i] - minus_n / n
        plus_di = 100.0 * plus_n / atr_n if atr_n else 0.0
        minus_di = 100.0 * minus_n / atr_n if atr_n else 0.0
        plus[i], minus[i] = plus_di, minus_di
        total = plus_di + minus_di
        dx[i] = 100.0 * abs(plus_di - minus_di) / total if total else 0.0

    line: list[Num] = [None] * size
    first = n * 2 - 1
    if first < size:
        current = sum(dx[n : first + 1]) / n
        line[first] = current
        for i in range(first + 1, size):
            current = (current * (n - 1) + dx[i]) / n
            line[i] = current
    return tuple(line), tuple(plus), tuple(minus)


def donchian(p: Path, n: int = 20) -> tuple[tuple[Num, ...], tuple[Num, ...]]:
    """Highest high and lowest low of the ``n`` candles *before* each candle.

    The current candle is left out on purpose: a close above this line is a real
    new high, and the line never moves because of the candle being judged.
    """
    upper: list[Num] = [None] * len(p.candles)
    lower: list[Num] = [None] * len(p.candles)
    for i in range(n, len(p.candles)):
        upper[i] = max(p.highs[i - n : i])
        lower[i] = min(p.lows[i - n : i])
    return tuple(upper), tuple(lower)


def obv(p: Path) -> tuple[Num, ...]:
    """On-balance volume: add the volume on up closes, subtract it on down closes."""
    total = 0.0
    out: list[Num] = [0.0]
    for i in range(1, len(p.candles)):
        change = p.closes[i] - p.closes[i - 1]
        total += p.volume[i] if change > 0 else -p.volume[i] if change < 0 else 0.0
        out.append(total)
    return tuple(out)


def mfi(p: Path, n: int = 14) -> tuple[Num, ...]:
    """Money Flow Index: an RSI-style 0-100 reading that also uses volume."""
    typical = [(h + low + c) / 3 for _, h, low, c in p.candles]
    flows = [t * v for t, v in zip(typical, p.volume, strict=True)]
    out: list[Num] = [None] * len(typical)
    for i in range(n, len(typical)):
        up = sum(flows[j] for j in range(i + 1 - n, i + 1) if typical[j] > typical[j - 1])
        down = sum(flows[j] for j in range(i + 1 - n, i + 1) if typical[j] < typical[j - 1])
        out[i] = 100.0 if down == 0 else 100.0 - 100.0 / (1.0 + up / down)
    return tuple(out)


def anchored_vwap(p: Path, anchor: int) -> tuple[Num, ...]:
    """VWAP that starts counting at candle ``anchor`` instead of the session open."""
    total_value = 0.0
    total_volume = 0.0
    out: list[Num] = [None] * len(p.candles)
    for i in range(anchor, len(p.candles)):
        _, high, low, close = p.candles[i]
        total_value += (high + low + close) / 3 * p.volume[i]
        total_volume += p.volume[i]
        out[i] = total_value / total_volume
    return tuple(out)


def bar_delta(p: Path) -> tuple[float, ...]:
    """A rough per-candle delta: the share of the range the body covers, times volume.

    Real delta needs every trade labelled buy or sell. Lessons that use this say
    so: it only draws the idea of delta on made-up candles.
    """
    out: list[float] = []
    for (open_, high, low, close), vol in zip(p.candles, p.volume, strict=True):
        span = high - low
        out.append(0.0 if span == 0 else round((close - open_) / span * vol, 1))
    return tuple(out)


def cumulative(values: Sequence[float]) -> tuple[Num, ...]:
    total = 0.0
    out: list[Num] = []
    for value in values:
        total += value
        out.append(round(total, 3))
    return tuple(out)


# ---------------------------------------------------------------------------
# Option maths: the standard Black-Scholes formulas, with no dividends
# ---------------------------------------------------------------------------


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _d1(spot: float, strike: float, vol: float, years: float, rate: float) -> float:
    return (math.log(spot / strike) + (rate + 0.5 * vol * vol) * years) / (vol * math.sqrt(years))


def call_price(spot: float, strike: float, vol: float, years: float, rate: float = 0.0) -> float:
    d1 = _d1(spot, strike, vol, years, rate)
    d2 = d1 - vol * math.sqrt(years)
    return spot * _norm_cdf(d1) - strike * math.exp(-rate * years) * _norm_cdf(d2)


def put_price(spot: float, strike: float, vol: float, years: float, rate: float = 0.0) -> float:
    call = call_price(spot, strike, vol, years, rate)
    return call - spot + strike * math.exp(-rate * years)


def call_delta(spot: float, strike: float, vol: float, years: float, rate: float = 0.0) -> float:
    return _norm_cdf(_d1(spot, strike, vol, years, rate))


def option_gamma(spot: float, strike: float, vol: float, years: float, rate: float = 0.0) -> float:
    return _norm_pdf(_d1(spot, strike, vol, years, rate)) / (spot * vol * math.sqrt(years))


# ---------------------------------------------------------------------------
# Shape data for the distribution charts
# ---------------------------------------------------------------------------


def histogram(values: Sequence[float], edges: Sequence[float]) -> tuple[int, ...]:
    """Counts of ``values`` in each ``[edges[i], edges[i + 1])`` bucket."""
    counts = [0] * (len(edges) - 1)
    for value in values:
        for i in range(len(counts)):
            if edges[i] <= value < edges[i + 1]:
                counts[i] += 1
                break
    return tuple(counts)


def beta_paths(n: int, *, seed: int, betas: Sequence[float]) -> tuple[tuple[Num, ...], ...]:
    """One seeded daily market move, applied to each path scaled by its beta (start = 100)."""
    rng = random.Random(seed)
    moves = [rng.gauss(0.05, 1.0) for _ in range(n)]
    out: list[tuple[Num, ...]] = []
    for beta in betas:
        value = 100.0
        path_values: list[Num] = [value]
        for move in moves:
            value *= 1 + beta * move / 100
            path_values.append(round(value, 2))
        out.append(tuple(path_values))
    return tuple(out)


def fat_tailed_returns(n: int, *, seed: int, scale: float = 1.0) -> tuple[float, ...]:
    """Seeded daily returns: mostly calm days, with a few rare and much larger moves."""
    rng = random.Random(seed)
    out: list[float] = []
    for _ in range(n):
        vol = scale * (3.5 if rng.random() < 0.04 else 1.0)
        out.append(rng.gauss(0.03, vol))
    return tuple(out)


def pivots(values: Sequence[float], *, width: int = 3) -> tuple[list[int], list[int]]:
    """Indexes of swing highs and swing lows (local extremes over +/- ``width``)."""
    highs: list[int] = []
    lows: list[int] = []
    for i in range(width, len(values) - width):
        window = values[i - width : i + width + 1]
        if values[i] == max(window):
            highs.append(i)
        elif values[i] == min(window):
            lows.append(i)
    return highs, lows
