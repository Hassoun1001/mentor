"""Forecaster ABC.

Every concrete forecaster — baseline rule, ML, ensemble — implements this
single contract. The application layer holds a reference to the chosen
forecaster and the rest of the system never cares which one is live.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

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
        self, *, bars: Sequence[PriceBar], symbol: str, timeframe: Timeframe
    ) -> Forecast: ...
