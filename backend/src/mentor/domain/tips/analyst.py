"""Analyst coverage — consensus target/rating + per-firm ratings.

What Wall Street thinks about a tracked ticker: the *consensus* price
target (and implied upside), the consensus rating with its buy/hold/sell
split, and each big bank's most-recent rating action.

Honest scope: free data (Yahoo) gives the **aggregate** target (mean /
high / low) and **per-firm ratings** — but not each bank's individual
dollar target, nor the Zacks Rank (both paywalled). ``AnalystProvider`` is
the seam a paid provider slots into later to fill those in; nothing else
changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

# Big houses to surface first, with the aliases the feeds actually use.
WATCHLIST_FIRMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Goldman Sachs", ("goldman",)),
    ("Morgan Stanley", ("morgan stanley",)),
    ("JPMorgan", ("jp morgan", "jpmorgan", "j.p. morgan")),
    ("Bank of America", ("b of a", "bank of america", "bofa", "merrill")),
    ("Citi", ("citigroup", "citi")),
    ("Deutsche Bank", ("deutsche",)),
    ("UBS", ("ubs",)),
    ("Wells Fargo", ("wells fargo",)),
    ("Barclays", ("barclays",)),
    ("Jefferies", ("jefferies",)),
)


def match_firm(raw: str) -> str | None:
    """Canonical watchlist name for a raw firm string, else ``None``."""
    low = raw.lower()
    for canonical, aliases in WATCHLIST_FIRMS:
        if any(alias in low for alias in aliases):
            return canonical
    return None


@dataclass(frozen=True, slots=True)
class AnalystRating:
    firm: str  # canonical firm name
    rating: str  # e.g. "Buy", "Overweight", "Neutral"
    action: str  # up / down / main / init / reit
    date: datetime


@dataclass(frozen=True, slots=True)
class AnalystConsensus:
    target_mean: Decimal | None
    target_high: Decimal | None
    target_low: Decimal | None
    upside_pct: Decimal | None  # target_mean vs current price
    rating_key: str | None  # strong_buy / buy / hold / underperform / sell
    num_analysts: int | None
    strong_buy: int
    buy: int
    hold: int
    sell: int
    strong_sell: int


@dataclass(frozen=True, slots=True)
class AnalystSnapshot:
    ticker: str
    current_price: Decimal | None
    consensus: AnalystConsensus | None
    ratings: tuple[AnalystRating, ...]  # latest per watchlist firm, newest first


def compute_upside(target_mean: Decimal | None, current: Decimal | None) -> Decimal | None:
    if target_mean is None or current is None or current <= 0:
        return None
    return ((target_mean - current) / current * Decimal("100")).quantize(Decimal("0.1"))


def latest_per_firm(ratings: list[AnalystRating]) -> tuple[AnalystRating, ...]:
    """Keep only the most recent rating per firm, newest first."""
    best: dict[str, AnalystRating] = {}
    for r in ratings:
        prev = best.get(r.firm)
        if prev is None or r.date > prev.date:
            best[r.firm] = r
    return tuple(sorted(best.values(), key=lambda r: r.date, reverse=True))


class AnalystProvider(ABC):
    """Contract for a source of analyst coverage. Yahoo (free) implements it
    now; a paid provider (per-bank targets, Zacks) can implement it later."""

    @abstractmethod
    async def fetch(self, ticker: str) -> AnalystSnapshot | None:
        """Return coverage for ``ticker``, or ``None`` if unavailable."""
        ...
