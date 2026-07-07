"""Replay — backfill the audit log with resolved system predictions.

The flywheel the user asked for resolves a live prediction only once its
horizon elapses (hours/days later). To make the loop *demonstrable* and
to seed the post-mortem with real hits and misses immediately, we replay
it over history: at each past bar `i`, the forecaster predicts using only
`bars[:i+1]` (no lookahead — same point-in-time guarantee the backtester
enforces), and we resolve against `bars[i + horizon]`, which has already
printed.

Every replayed prediction is a genuine, out-of-sample, point-in-time
forecast scored against the real outcome — exactly what the live loop
will produce, just compressed from weeks into seconds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from mentor.application.forecasting.news_context import load_news_series
from mentor.application.macro.context import load_macro_series
from mentor.domain.errors import ValidationError
from mentor.domain.forecasting.baseline import BaselineForecaster
from mentor.domain.forecasting.forecaster import Forecaster
from mentor.domain.forecasting.macro_features import MacroSeries
from mentor.domain.forecasting.news_features import NewsToneSeries
from mentor.domain.forecasting.regime import RegimeAdjustedForecaster
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore
from mentor.infrastructure.forecasting.sklearn_forecaster import SklearnForecaster
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.infrastructure.repositories.news_tone import NewsToneRepository
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import get_logger

log = get_logger("mentor.forecasting.replay")

# A baseline forecast needs the 200-bar trend filter plus headroom.
_MIN_WARMUP = 210


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
class ReplayResult:
    symbol: str
    timeframe: str
    model_name: str
    points_evaluated: int
    predictions_written: int
    skipped_existing: int


class ReplayService:
    def __init__(
        self,
        *,
        prices: PriceBarRepository,
        predictions: PredictionRepository,
        model_store_dir: str | Path,
        news_tone: NewsToneRepository | None = None,
        news_query_key: str = "eurusd",
        macro: MacroSeriesRepository | None = None,
    ) -> None:
        self._prices = prices
        self._predictions = predictions
        self._store = ModelStore(model_store_dir)
        self._news_tone = news_tone
        self._news_query_key = news_query_key
        self._macro = macro

    def _resolve_forecaster(
        self, model_name: str, horizon_bars: int, *, regime_aware: bool = True
    ) -> Forecaster:
        if model_name == "baseline":
            return BaselineForecaster(horizon_bars=horizon_bars)
        forecaster, _meta = self._store.load(model_name)
        if (
            regime_aware
            and isinstance(forecaster, SklearnForecaster)
            and forecaster.distribution is not None
        ):
            return RegimeAdjustedForecaster(
                base=forecaster, distribution=forecaster.distribution
            )
        return forecaster

    async def replay(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        model_name: str,
        horizon_bars: int,
        max_points: int = 200,
        stride: int = 1,
    ) -> ReplayResult:
        """Generate and resolve up to `max_points` historical predictions.

        Walks backward from the most recent fully-resolvable bar so the
        newest, most relevant predictions are produced first.
        """
        rows = await self._prices.range(
            symbol=symbol,
            timeframe=timeframe,
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2100, 1, 1, tzinfo=UTC),
        )
        bars = _to_domain(rows)
        if len(bars) < _MIN_WARMUP + horizon_bars + 1:
            raise ValidationError(
                f"need at least {_MIN_WARMUP + horizon_bars + 1} bars to replay "
                f"{symbol} {timeframe.value}; have {len(bars)}"
            )

        forecaster = self._resolve_forecaster(model_name, horizon_bars)

        # Load the exogenous series once if (and only if) this model uses them.
        news_series: NewsToneSeries | None = None
        macro_series: MacroSeries | None = None
        core = getattr(forecaster, "base", forecaster)
        if getattr(core, "uses_news", False) and self._news_tone is not None:
            news_series = await load_news_series(self._news_tone, query_key=self._news_query_key)
        if getattr(core, "uses_macro", False) and self._macro is not None:
            macro_series = await load_macro_series(self._macro)

        # The last index we can resolve is len - 1 - horizon (its outcome exists).
        last_resolvable = len(bars) - 1 - horizon_bars
        first_predictable = _MIN_WARMUP - 1

        indices = list(range(last_resolvable, first_predictable, -stride))[:max_points]

        written = 0
        skipped = 0
        evaluated = 0
        now = datetime.now(UTC)
        for i in indices:
            evaluated += 1
            window = bars[: i + 1]
            news = news_series.features_asof(window[-1].ts) if news_series else None
            macro = macro_series.features_asof(window[-1].ts) if macro_series else None
            try:
                forecast = forecaster.forecast(
                    bars=window, symbol=symbol, timeframe=timeframe, news=news, macro=macro
                )
            except ValidationError:
                continue  # not enough history at this point for this model
            # Idempotency: model_name on the forecast is the resolved name
            # (e.g. "regime_adjusted(...)"), so dedupe on that.
            if await self._predictions.exists_at(
                symbol=symbol,
                timeframe=timeframe.value,
                asof=forecast.asof,
                model_name=forecast.model_name,
            ):
                skipped += 1
                continue
            realised_close = bars[i + horizon_bars].close
            await self._predictions.record_and_resolve(
                forecast, realised_close=realised_close, resolved_at=now
            )
            written += 1

        log.info(
            "replay.done",
            symbol=symbol,
            timeframe=timeframe.value,
            model=model_name,
            evaluated=evaluated,
            written=written,
            skipped=skipped,
        )
        return ReplayResult(
            symbol=symbol.upper(),
            timeframe=timeframe.value,
            model_name=model_name,
            points_evaluated=evaluated,
            predictions_written=written,
            skipped_existing=skipped,
        )
