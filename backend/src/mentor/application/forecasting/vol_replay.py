"""Replay the volatility forecaster over history and grade it.

The forecast is regenerated at each step from *only* the bars available at
that moment, then compared with what price actually did over the following
horizon. Nothing downstream of the forecast timestamp is ever visible to
the forecaster — the same point-in-time discipline the direction model
uses, for the same reason.

**Windows are non-overlapping.** Stepping one bar at a time would give
many more samples, but consecutive windows would share almost all their
bars, so their hits would be correlated and the confidence interval would
come out far too narrow — the sample would look bigger than it is. This is
the same mistake the drift watcher had to be fixed for, and it is worth
paying real sample size to avoid.

Two deliberately dumb benchmarks come along for the ride:

- ``last_window`` — "however far it moved last time, it will move again".
  A random walk on volatility. Hard to beat, and the honest bar any vol
  model has to clear before its machinery is worth anything.
- ``trailing_mean`` — the average move so far. Ignores clustering entirely.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.application.forecasting.vol_service import _to_domain
from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.vol_audit import VolAuditResult, VolSample, audit_vol_forecasts
from mentor.domain.forecasting.volatility import EwmaVolForecaster
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.repositories import PriceBarRepository

# The EWMA needs enough history for its decay to mean anything before the
# first forecast is worth grading.
_WARMUP_BARS = 120

# Each forecast costs time proportional to the history it sees (~80us per
# bar of Decimal arithmetic), so replaying thousands of forecasts over a
# growing window is quadratic and takes minutes. Two bounds fix that
# without weakening the result:
#
# _MAX_VISIBLE — an EWMA's memory decays exponentially, so bars far behind
# the window contribute essentially nothing to the volatility estimate.
# 800 D1 bars is over three years; the quantity under audit
# (expected_range_pips) is unchanged by truncating beyond it.
#
# _MAX_SAMPLES — 400 independent windows already pins a rate near 68% to
# about +/-4.5% at 95% confidence. More samples cost minutes and buy
# decimal places nobody should act on.
_MAX_VISIBLE = 800
_MAX_SAMPLES = 400

# How many prior windows the trailing-mean benchmark averages over.
_TRAILING_WINDOWS = 20


def _move(bars: list[PriceBar], start: int, horizon: int, pip_size: Decimal) -> float:
    """Absolute move in pips over ``horizon`` bars ending at ``start + horizon``."""
    if start < 0 or start + horizon >= len(bars):
        return 0.0
    return float(abs(bars[start + horizon].close - bars[start].close) / pip_size)


class VolReplayService:
    """Walk-forward audit of the volatility forecast."""

    def __init__(self, *, prices: PriceBarRepository) -> None:
        self._prices = prices

    async def audit(
        self,
        *,
        symbol: str,
        timeframe: Timeframe = Timeframe.D1,
        horizon_bars: int = 1,
        history_bars: int = 2600,
        max_samples: int = _MAX_SAMPLES,
    ) -> VolAuditResult:
        if horizon_bars < 1:
            raise ValidationError("horizon_bars must be >= 1", field="horizon_bars")

        end = datetime.now(UTC)
        start = end - timedelta(seconds=history_bars * timeframe.seconds * 3)
        rows = await self._prices.range(
            symbol=symbol, timeframe=timeframe, start=start, end=end
        )
        if not rows:
            raise ValidationError(
                f"no bars for {symbol} {timeframe.value} — backfill first", field="symbol"
            )

        bars = _to_domain(rows)
        if len(bars) < _WARMUP_BARS + horizon_bars * 4:
            raise ValidationError(
                f"only {len(bars)} bars — need at least "
                f"{_WARMUP_BARS + horizon_bars * 4} to audit meaningfully",
                field="symbol",
            )

        pip_size = get_instrument(symbol).pip_size
        forecaster = EwmaVolForecaster()

        samples: list[VolSample] = []
        last_window: list[float] = []
        trailing_mean: list[float] = []

        # Non-overlapping: step a full horizon each time. When that yields
        # more windows than we need, spread the sample evenly across history
        # rather than taking a contiguous block — a bounded subset of
        # non-overlapping windows is still non-overlapping.
        points = list(range(_WARMUP_BARS, len(bars) - horizon_bars, horizon_bars))
        if len(points) > max_samples:
            stride = len(points) / max_samples
            points = [points[int(k * stride)] for k in range(max_samples)]

        for i in points:
            visible = bars[max(0, i + 1 - _MAX_VISIBLE) : i + 1]
            forecast = forecaster.forecast_vol(
                bars=visible,
                symbol=symbol,
                timeframe=timeframe,
                horizon_bars=horizon_bars,
                pip_size=pip_size,
            )
            realised = abs(bars[i + horizon_bars].close - bars[i].close) / pip_size

            # Benchmarks are computed from the bars immediately before the
            # forecast, never from the sampled list. With a stride, the
            # previous *sample* may be weeks back, which would turn
            # "however far it moved last time" into a much easier rival and
            # quietly flatter the model it is supposed to challenge.
            last_window.append(_move(bars, i - horizon_bars, horizon_bars, pip_size))
            prior = [
                _move(bars, i - k * horizon_bars, horizon_bars, pip_size)
                for k in range(1, _TRAILING_WINDOWS + 1)
                if i - k * horizon_bars >= 0
            ]
            trailing_mean.append(sum(prior) / len(prior) if prior else 0.0)

            samples.append(
                VolSample(
                    predicted_sigma_pips=float(forecast.expected_range_pips),
                    realised_move_pips=float(realised),
                    band_low_pips=(
                        float(forecast.range_low_pips)
                        if forecast.range_low_pips is not None
                        else None
                    ),
                    band_high_pips=(
                        float(forecast.range_high_pips)
                        if forecast.range_high_pips is not None
                        else None
                    ),
                )
            )

        if not samples:
            raise ValidationError("not enough history to produce a forecast", field="symbol")

        return audit_vol_forecasts(
            samples,
            benchmarks={"last_window": last_window, "trailing_mean": trailing_mean},
        )
