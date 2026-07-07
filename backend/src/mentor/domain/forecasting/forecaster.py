"""Forecaster ABC.

Every concrete forecaster — baseline rule, ML, ensemble — implements this
single contract. The application layer holds a reference to the chosen
forecaster and the rest of the system never cares which one is live.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from mentor.domain.forecasting.forecast import Forecast
from mentor.domain.market.bars import PriceBar, Timeframe


class Forecaster(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def horizon_bars(self) -> int: ...

    @abstractmethod
    def forecast(
        self,
        *,
        bars: Sequence[PriceBar],
        symbol: str,
        timeframe: Timeframe,
        news: Mapping[str, float] | None = None,
        macro: Mapping[str, float] | None = None,
    ) -> Forecast:
        """Produce a forecast for the latest bar.

        `news` carries exogenous news-sentiment features aligned to the
        as-of bar; `macro` carries FX-driver features (US rates, DXY, VIX)
        the same way. Forecasters that don't use them ignore them; the
        application layer only populates each for models that consume it.
        """
        ...
