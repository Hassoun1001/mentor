"""Market-data domain — bars, timeframes, and the adapter contract.

Every external source — Twelve Data, Alpha Vantage, Polygon, OANDA — is a
concrete implementation of `MarketDataAdapter`. The rest of the app sees a
single uniform interface, which is what makes "swap a data source without
touching the rest of the app" a one-day change instead of a project.
"""

from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import PriceBar, Timeframe

__all__ = ["MarketDataAdapter", "PriceBar", "Timeframe"]
