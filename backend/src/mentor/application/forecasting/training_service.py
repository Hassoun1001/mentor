"""Training orchestrator.

Loads bars from the price repo, hands them to the trainer, persists the
model + metadata via `ModelStore`. The trainer itself is pure-domain;
this layer just plumbs IO.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.infrastructure.forecasting.model_store import ModelStore, StoredModelMeta
from mentor.infrastructure.forecasting.sklearn_forecaster import (
    SklearnForecaster,
    train_sklearn_forecaster,
)
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
    def __init__(self, repo: PriceBarRepository, store_dir: str | Path) -> None:
        self._repo = repo
        self._store = ModelStore(store_dir)

    async def train(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        horizon_bars: int,
        model_name: str,
    ) -> tuple[SklearnForecaster, StoredModelMeta]:
        rows = await self._repo.range(symbol=symbol, timeframe=timeframe, start=start, end=end)
        if not rows:
            raise ValidationError(
                f"no bars for {symbol} {timeframe.value} in window — backfill first"
            )
        bars = _to_domain(rows)
        forecaster = train_sklearn_forecaster(bars=bars, horizon_bars=horizon_bars)
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
