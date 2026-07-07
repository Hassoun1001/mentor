"""Training orchestrator.

Loads bars from the price repo, hands them to the trainer, persists the
model + metadata via `ModelStore`. The trainer itself is pure-domain;
this layer just plumbs IO.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from mentor.application.forecasting.news_context import build_news_by_ts, load_news_series
from mentor.application.macro.context import build_macro_by_ts, load_macro_series
from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore, StoredModelMeta
from mentor.infrastructure.forecasting.sklearn_forecaster import (
    SklearnForecaster,
    train_sklearn_forecaster,
)
from mentor.infrastructure.repositories.macro_series import MacroSeriesRepository
from mentor.infrastructure.repositories.news_tone import NewsToneRepository
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


class TrainingService:
    def __init__(
        self,
        repo: PriceBarRepository,
        store_dir: str | Path,
        *,
        news_tone: NewsToneRepository | None = None,
        news_query_key: str = "eurusd",
        macro: MacroSeriesRepository | None = None,
    ) -> None:
        self._repo = repo
        self._store = ModelStore(store_dir)
        self._news_tone = news_tone
        self._news_query_key = news_query_key
        self._macro = macro

    async def train(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        horizon_bars: int,
        model_name: str,
        include_news: bool = False,
        include_macro: bool = False,
    ) -> tuple[SklearnForecaster, StoredModelMeta]:
        rows = await self._repo.range(symbol=symbol, timeframe=timeframe, start=start, end=end)
        if not rows:
            raise ValidationError(
                f"no bars for {symbol} {timeframe.value} in window — backfill first"
            )
        bars = _to_domain(rows)

        news_by_ts = None
        if include_news:
            if self._news_tone is None:
                raise ValidationError("include_news requires a news-tone repository")
            series = await load_news_series(self._news_tone, query_key=self._news_query_key)
            if series.empty:
                raise ValidationError(
                    "no news tone in store — ingest GDELT tone before training with news"
                )
            news_by_ts = build_news_by_ts(series, [b.ts for b in bars])

        macro_by_ts = None
        if include_macro:
            if self._macro is None:
                raise ValidationError("include_macro requires a macro-series repository")
            macro_series = await load_macro_series(self._macro)
            if macro_series.empty:
                raise ValidationError(
                    "no macro series in store — ingest FRED data before training with macro"
                )
            macro_by_ts = build_macro_by_ts(macro_series, [b.ts for b in bars])

        forecaster = train_sklearn_forecaster(
            bars=bars,
            horizon_bars=horizon_bars,
            news_by_ts=news_by_ts,
            macro_by_ts=macro_by_ts,
        )
        meta = self._store.save(
            forecaster,
            name=model_name,
            symbol=symbol.upper(),
            timeframe=timeframe.value,
            train_start=start,
            train_end=end,
        )
        return forecaster, meta

    def list_models(self) -> list[StoredModelMeta]:
        return list(self._store.list())

    def load(self, name: str) -> tuple[SklearnForecaster, StoredModelMeta]:
        return self._store.load(name)
