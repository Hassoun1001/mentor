"""Volatility forecasting — predict the *range*, not the *arrow*.

Direction is ~random out-of-sample (we measured ~53.5% over ten years),
but volatility **clusters**: big bars follow big bars. That is one of the
most robust empirical facts in finance (ARCH/GARCH). So unlike a direction
model, a volatility model can *honestly* beat naive — this is the feature
where we expect a real out-of-sample win.

Target: future **realized volatility** over the next ``H`` bars —

    future_rv[t] = stdev(log_returns[t+1 .. t+H])

i.e. the typical size of a single bar's log-return in the window that
*follows* bar ``t``. Point-in-time safe, exactly like ``labels.py``: the
label at ``t`` uses only returns strictly after ``t``; features at ``t``
use only bars up to and including ``t``.

The transparent yardstick is the **RiskMetrics EWMA** (lambda = 0.94): an
exponentially-weighted estimate of current per-bar variance, and a strong
one-step vol forecast. Any ML vol model must beat EWMA out-of-sample on a
proper vol loss (MAE / QLIKE) or we keep EWMA and say so — the same
honest-benchmark discipline as ``BaselineForecaster`` on the direction side.

All math is Decimal-clean, mirroring ``features.py``: log-returns via
``Decimal.ln``, standard deviation with a Newton-iteration square root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe

# RiskMetrics decay for daily-ish data. Higher lambda => longer memory.
RISKMETRICS_LAMBDA: Decimal = Decimal("0.94")

# How many trailing returns seed the EWMA variance before the recursion,
# and the trailing window used to build the historical realized-vol
# distribution that classifies calm / normal / wide.
_EWMA_SEED_WINDOW = 20
_RV_WINDOW = 20
_CALM_PCTL = Decimal("0.33")
_WIDE_PCTL = Decimal("0.66")


class VolRegime(StrEnum):
    CALM = "calm"
    NORMAL = "normal"
    WIDE = "wide"


# --------------------------------------------------------------------------
# Pure math helpers
# --------------------------------------------------------------------------


def _dsqrt(value: Decimal) -> Decimal:
    """Square root of a non-negative Decimal via Newton's iteration.

    Mirrors ``features._std`` so the whole vol stack stays Decimal-clean and
    portable (no float round-trips for the statistical core).
    """
    if value <= 0:
        return Decimal("0")
    x = value
    for _ in range(40):
        x = (x + value / x) / Decimal("2")
    return x


def log_returns(closes: Sequence[Decimal]) -> list[Decimal]:
    """Per-bar log returns ``ln(close[i] / close[i-1])``.

    Bars carry strictly-positive closes (enforced by ``PriceBar``), but we
    guard anyway so this helper is safe on any sequence.
    """
    out: list[Decimal] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        cur = closes[i]
        if prev > 0 and cur > 0:
            out.append((cur / prev).ln())
    return out


def realized_vol(returns: Sequence[Decimal], *, window: int | None = None) -> Decimal | None:
    """Sample standard deviation of log returns over the last ``window``.

    This is exactly the ``future_rv`` target's estimator, reused for both
    the label (over future returns) and the historical distribution (over
    trailing returns). Returns ``None`` when there are fewer than two
    observations.
    """
    # Slice *before* copying — ``list(returns)[-window:]`` would copy the whole
    # prefix first, turning trailing-window calls into O(n) and the rolling
    # series into O(n^2). Slicing the Sequence first keeps this O(window).
    data = list(returns if window is None else returns[-window:])
    n = len(data)
    if n < 2:
        return None
    mean = sum(data, Decimal("0")) / Decimal(n)
    variance = sum(((r - mean) * (r - mean) for r in data), Decimal("0")) / Decimal(n - 1)
    return _dsqrt(variance)


def ewma_vol(
    returns: Sequence[Decimal],
    *,
    lam: Decimal = RISKMETRICS_LAMBDA,
    seed_window: int = _EWMA_SEED_WINDOW,
) -> Decimal | None:
    """RiskMetrics EWMA volatility: ``s2_t = lam*s2_{t-1} + (1-lam)*r_{t-1}^2``.

    Zero-mean assumption (standard for RiskMetrics on returns). The variance
    is seeded with the simple mean of squared returns over the first
    ``seed_window`` observations, then the recursion folds in the rest. The
    returned value is the current one-step-ahead vol forecast.
    """
    data = list(returns)
    if len(data) < 2:
        return None
    if not (Decimal("0") < lam < Decimal("1")):
        raise ValidationError("lambda must be in (0, 1)", field="lam")
    seed = data[:seed_window] if len(data) >= seed_window else data
    variance = sum((r * r for r in seed), Decimal("0")) / Decimal(len(seed))
    for r in data[len(seed) :]:
        variance = lam * variance + (Decimal("1") - lam) * (r * r)
    return _dsqrt(variance)


def rolling_realized_vol(closes: Sequence[Decimal], *, window: int = _RV_WINDOW) -> list[Decimal]:
    """Trailing realized-vol at each bar — the historical vol distribution.

    Used to answer "is today calm / normal / wide?" by percentile rank. Each
    entry is the sample stdev of the ``window`` log-returns ending at that
    bar; bars without enough history are skipped.
    """
    rets = log_returns(closes)
    out: list[Decimal] = []
    for i in range(len(rets)):
        rv = realized_vol(rets[: i + 1], window=window)
        if rv is not None and rv > 0:
            out.append(rv)
    return out


def percentile_rank(value: Decimal, population: Sequence[Decimal]) -> Decimal:
    """Fraction of ``population`` at or below ``value``, in [0, 1]."""
    if not population:
        return Decimal("0.5")
    at_or_below = sum(1 for p in population if p <= value)
    return Decimal(at_or_below) / Decimal(len(population))


def regime_from_percentile(pctl: Decimal) -> VolRegime:
    if pctl < _CALM_PCTL:
        return VolRegime.CALM
    if pctl >= _WIDE_PCTL:
        return VolRegime.WIDE
    return VolRegime.NORMAL


# --------------------------------------------------------------------------
# Value object
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VolForecast:
    """A volatility read — a *range*, never a direction or a price target.

    - ``expected_vol``          per-bar stdev of log returns (the model target)
    - ``expected_range_pips``   1-sigma cumulative move over the horizon, in pips
    - ``percentile_vs_history`` where ``expected_vol`` sits vs trailing realized vol
    - ``regime``                calm / normal / wide
    """

    symbol: str
    timeframe: Timeframe
    asof: datetime
    asof_close: Decimal
    horizon_bars: int
    expected_vol: Decimal
    expected_range_pips: Decimal
    percentile_vs_history: Decimal
    regime: VolRegime
    model_name: str
    reasoning: str
    # Split-conformal coverage band on the expected move (ML model only).
    range_low_pips: Decimal | None = None
    range_high_pips: Decimal | None = None
    coverage: Decimal | None = None  # e.g. 0.90

    def __post_init__(self) -> None:
        if self.expected_vol < 0:
            raise ValidationError("expected_vol must be >= 0", field="expected_vol")
        if self.expected_range_pips < 0:
            raise ValidationError("expected_range_pips must be >= 0", field="expected_range_pips")
        if not (Decimal("0") <= self.percentile_vs_history <= Decimal("1")):
            raise ValidationError("percentile must be in [0, 1]", field="percentile_vs_history")
        if self.horizon_bars < 1:
            raise ValidationError("horizon_bars must be >= 1", field="horizon_bars")
        if self.asof.tzinfo is None:
            raise ValidationError("asof must be timezone-aware", field="asof")
        if not self.reasoning.strip():
            raise ValidationError("reasoning required", field="reasoning")


_REGIME_PHRASE: Mapping[VolRegime, str] = {
    VolRegime.CALM: "a calm regime — quieter than usual",
    VolRegime.NORMAL: "a normal regime",
    VolRegime.WIDE: "a wide regime — expect larger swings than usual",
}


def horizon_move_pips(
    *, per_bar_vol: Decimal, close: Decimal, horizon_bars: int, pip_size: Decimal
) -> Decimal:
    """1-sigma cumulative move over ``horizon_bars``, expressed in pips.

    Under a random-walk approximation the log return over ``H`` bars has
    stdev ``per_bar_vol * sqrt(H)``; multiplied by price this is the move in
    price units, divided by ``pip_size`` gives pips. This is a *one standard
    deviation* band — roughly two-in-three of moves land inside it — not a
    prediction of a specific level.
    """
    if pip_size <= 0:
        raise ValidationError("pip_size must be positive", field="pip_size")
    horizon_sigma = per_bar_vol * _dsqrt(Decimal(horizon_bars))
    return (close * horizon_sigma) / pip_size


def build_vol_forecast(
    *,
    symbol: str,
    timeframe: Timeframe,
    asof: datetime,
    asof_close: Decimal,
    horizon_bars: int,
    per_bar_vol: Decimal,
    history: Sequence[Decimal],
    pip_size: Decimal,
    model_name: str,
    conformal_q: Decimal | None = None,
    coverage: Decimal | None = None,
) -> VolForecast:
    """Assemble a ``VolForecast`` from a per-bar vol estimate + history.

    Shared by the EWMA baseline and the ML regressor so the range/percentile/
    regime/reasoning presentation is identical whichever brain produced the
    ``per_bar_vol`` number. When ``conformal_q`` (a split-conformal residual
    quantile in vol units) is supplied, we translate ``per_bar_vol +/- q``
    into a pips coverage band — an honest "X to Y pips with NN% coverage".
    """
    pctl = percentile_rank(per_bar_vol, history)
    regime = regime_from_percentile(pctl)
    range_pips = horizon_move_pips(
        per_bar_vol=per_bar_vol, close=asof_close, horizon_bars=horizon_bars, pip_size=pip_size
    )
    low_pips: Decimal | None = None
    high_pips: Decimal | None = None
    band_note = ""
    if conformal_q is not None:
        low_vol = max(Decimal("0"), per_bar_vol - conformal_q)
        high_vol = per_bar_vol + conformal_q
        low_pips = horizon_move_pips(
            per_bar_vol=low_vol, close=asof_close, horizon_bars=horizon_bars, pip_size=pip_size
        )
        high_pips = horizon_move_pips(
            per_bar_vol=high_vol, close=asof_close, horizon_bars=horizon_bars, pip_size=pip_size
        )
        cov = int((coverage or Decimal("0.9")) * 100)
        band_note = f" Conformal {cov}% band: {low_pips:.0f} to {high_pips:.0f} pips."
    reasoning = (
        f"Expected move over the next {horizon_bars} bars is about "
        f"+/-{range_pips:.0f} pips (1 sigma), {_REGIME_PHRASE[regime]} at the "
        f"{pctl * 100:.0f}th percentile of trailing realized volatility.{band_note} "
        f"This is a range, not a direction: volatility clusters, so it is a "
        f"genuinely forecastable quantity — unlike which way price goes."
    )
    return VolForecast(
        symbol=symbol.upper(),
        timeframe=timeframe,
        asof=asof,
        asof_close=asof_close,
        horizon_bars=horizon_bars,
        expected_vol=per_bar_vol,
        expected_range_pips=range_pips,
        percentile_vs_history=pctl,
        regime=regime,
        model_name=model_name,
        reasoning=reasoning,
        range_low_pips=low_pips,
        range_high_pips=high_pips,
        coverage=coverage if conformal_q is not None else None,
    )


# --------------------------------------------------------------------------
# Position-sizing + event-freeze guidance (the payoff of a vol forecast)
# --------------------------------------------------------------------------

# Above this percentile of trailing realized vol we flag an "event freeze":
# a fixed-pip stop is much likelier to be hit, so sit out or halve size.
_FREEZE_PCTL = Decimal("0.85")


@dataclass(frozen=True, slots=True)
class VolSizingGuidance:
    """How a volatility read should shape a trade — never a direction call.

    - ``suggested_stop_pips`` a stop wide enough to sit *beyond* normal noise
      over the horizon (feed it into the position-size calculator).
    - ``event_freeze``        vol is in a high percentile — reduce or skip.
    """

    suggested_stop_pips: Decimal
    event_freeze: bool
    rationale: str


def build_sizing_guidance(
    forecast: VolForecast,
    *,
    stop_sigma_mult: Decimal = Decimal("1.5"),
    freeze_pctl: Decimal = _FREEZE_PCTL,
) -> VolSizingGuidance:
    """Turn a ``VolForecast`` into an honest stop suggestion + freeze flag.

    The stop is ``stop_sigma_mult`` times the 1-sigma expected move — a stop
    inside one sigma sits right where routine noise can hit it, so we default
    to 1.5 sigma. The freeze flag fires when today's expected vol is in a very
    high percentile of its own recent history.
    """
    stop_pips = forecast.expected_range_pips * stop_sigma_mult
    pctl = int(forecast.percentile_vs_history * 100)
    freeze = forecast.percentile_vs_history >= freeze_pctl
    if freeze:
        rationale = (
            f"Volatility is in the {pctl}th percentile — a wide, event-like regime. "
            f"Consider a freeze: sit out or halve size until it normalizes, because a "
            f"fixed-pip stop is far likelier to be hit here. If you do trade, a stop "
            f"below ~{stop_pips:.0f} pips is inside the noise."
        )
    else:
        rationale = (
            f"A stop of ~{stop_pips:.0f} pips ({stop_sigma_mult} sigma over "
            f"{forecast.horizon_bars} bars) sits beyond routine noise for this regime. "
            f"Size the trade from this stop in the risk calculator so the dollar risk "
            f"is right for today's volatility, not a static guess."
        )
    return VolSizingGuidance(
        suggested_stop_pips=stop_pips, event_freeze=freeze, rationale=rationale
    )


# --------------------------------------------------------------------------
# Forecaster ABC + EWMA baseline
# --------------------------------------------------------------------------

_MIN_BARS_FOR_VOL = _EWMA_SEED_WINDOW + _RV_WINDOW + 2


class VolForecaster(ABC):
    """Contract shared by the EWMA baseline and the ML vol regressor."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def forecast_vol(
        self,
        *,
        bars: Sequence[PriceBar],
        symbol: str,
        timeframe: Timeframe,
        horizon_bars: int,
        pip_size: Decimal,
        macro: Mapping[str, float] | None = None,
    ) -> VolForecast:
        """`macro` carries FX-driver features (rates, DXY, VIX) aligned to the
        as-of bar; models that don't use them ignore it."""
        ...


@dataclass(frozen=True, slots=True)
class EwmaVolForecaster(VolForecaster):
    """RiskMetrics EWMA — the transparent benchmark the ML model must beat."""

    lam: Decimal = RISKMETRICS_LAMBDA

    @property
    def name(self) -> str:
        return f"ewma_vol(lambda={self.lam})"

    def forecast_vol(
        self,
        *,
        bars: Sequence[PriceBar],
        symbol: str,
        timeframe: Timeframe,
        horizon_bars: int,
        pip_size: Decimal,
        macro: Mapping[str, float] | None = None,  # EWMA ignores macro
    ) -> VolForecast:
        if len(bars) < _MIN_BARS_FOR_VOL:
            raise ValidationError(
                f"need at least {_MIN_BARS_FOR_VOL} bars for a volatility read", field="bars"
            )
        closes = [b.close for b in bars]
        rets = log_returns(closes)
        per_bar = ewma_vol(rets, lam=self.lam)
        if per_bar is None:
            raise ValidationError("not enough returns to estimate volatility", field="bars")
        history = rolling_realized_vol(closes)
        return build_vol_forecast(
            symbol=symbol,
            timeframe=timeframe,
            asof=bars[-1].ts,
            asof_close=bars[-1].close,
            horizon_bars=horizon_bars,
            per_bar_vol=per_bar,
            history=history,
            pip_size=pip_size,
            model_name=self.name,
        )
