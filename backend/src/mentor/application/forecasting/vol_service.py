"""Volatility inference orchestrator.

Loads the latest visible bars and produces a ``VolForecast``. The EWMA
baseline is *always* computed and returned; when the caller asks for the
ML model we train it on the loaded history, grade it against EWMA
out-of-sample, and only make it the headline if it actually wins. If it
doesn't, the headline stays EWMA and the report says why — the same
honest-benchmark discipline as the direction champion/challenger.

Vol training is cheap on a single instrument's daily history, so we train
on demand rather than persisting a pickle — the read is always fresh and
there are no stale-model compatibility traps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.application.macro.context import build_macro_by_ts, load_macro_series
from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.volatility import (
    EwmaVolForecaster,
    VolForecast,
)
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.sklearn_vol_forecaster import (
    VolTrainingReport,
    train_sklearn_vol_forecaster,
)
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository


def _to_domain(rows) -> list[PriceBar]:  # type: ignore[no-untyped-def]
    return [
        PriceBar(
            symbol=r.symbol,
            timeframe=Timeframe(r.timeframe),
            ts=r.ts,
            open=Decimal(r.open),
            high=Decimal(r.high),
            low=Decimal(r.low),
            close=Decimal(r.close),
            volume=Decimal(r.volume) if r.volume is not None else None,
            source=r.source,
        )
        for r in rows
    ]


@dataclass(frozen=True, slots=True)
class VolPayload:
    forecast: VolForecast  # the headline read (EWMA, or ML if it wins)
    baseline: VolForecast  # always the transparent EWMA read
    eval: VolTrainingReport | None  # present only when the ML model was trained


class VolService:
    def __init__(
        self, *, prices: PriceBarRepository, macro: MacroSeriesRepository | None = None
    ) -> None:
        self._prices = prices
        self._macro = macro

    async def predict_vol(
        self,
        *,
        symbol: str,
        timeframe: Timeframe = Timeframe.D1,
        horizon_bars: int = 5,
        history_bars: int = 2600,
        model: str = "ewma",
    ) -> VolPayload:
        end = datetime.now(UTC)
        start = end - timedelta(seconds=history_bars * timeframe.seconds * 2)
        rows = await self._prices.range(symbol=symbol, timeframe=timeframe, start=start, end=end)
        if not rows:
            raise ValidationError(f"no bars for {symbol} {timeframe.value} — backfill first")
        bars = _to_domain(rows)
        pip_size = get_instrument(symbol).pip_size

        baseline = EwmaVolForecaster().forecast_vol(
            bars=bars,
            symbol=symbol,
            timeframe=timeframe,
            horizon_bars=horizon_bars,
            pip_size=pip_size,
        )
        if model != "ml":
            return VolPayload(forecast=baseline, baseline=baseline, eval=None)

        # Wire in FX-driver features (VIX/rates) when available — measured to
        # improve realized-vol prediction at horizons >= ~10 bars. The honest
        # gate still decides per-horizon whether ML (with or without macro)
        # beats EWMA.
        macro_by_ts = None
        macro_now = None
        if self._macro is not None:
            series = await load_macro_series(self._macro)
            if not series.empty:
                macro_by_ts = build_macro_by_ts(series, [b.ts for b in bars])
                macro_now = series.features_asof(bars[-1].ts)

        forecaster = train_sklearn_vol_forecaster(
            bars=bars, horizon_bars=horizon_bars, macro_by_ts=macro_by_ts
        )
        ml = forecaster.forecast_vol(
            bars=bars,
            symbol=symbol,
            timeframe=timeframe,
            horizon_bars=horizon_bars,
            pip_size=pip_size,
            macro=macro_now,
        )
        report = forecaster.report
        headline = ml if report.beats_ewma else baseline
        return VolPayload(forecast=headline, baseline=baseline, eval=report)
