"""Tip ingestion — parse a message and snapshot each entry price.

The entry price is the close on (or just before) the date the tipster
sent the message, not the price when you happen to paste it in. That's
what makes the later return honest: it's measured from when they actually
called it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.tips.parser import TipParser
from mentor.infrastructure.adapters.stock_quotes import (
    DailyClose,
    StockQuoteClient,
    StockQuoteError,
)
from mentor.infrastructure.repositories.stock_tips import StockTipRepository
from mentor.logging import get_logger

log = get_logger("mentor.tips.ingest")


@dataclass(frozen=True, slots=True)
class IngestedTip:
    ticker: str
    category: str
    action: str
    conviction: str
    mention_price: Decimal | None


@dataclass(frozen=True, slots=True)
class IngestResult:
    tipster: str
    parsed: int
    priced: int
    unpriced_tickers: tuple[str, ...]
    tips: tuple[IngestedTip, ...]


def _close_asof(closes: Sequence[DailyClose], ts: datetime) -> Decimal | None:
    """Last close on or before `ts`; fall back to the earliest close."""
    on_or_before = [c for c in closes if c.day <= ts]
    if on_or_before:
        return on_or_before[-1].close
    return closes[0].close if closes else None


class TipIngestService:
    def __init__(
        self, *, parser: TipParser, repo: StockTipRepository, quotes: StockQuoteClient
    ) -> None:
        self._parser = parser
        self._repo = repo
        self._quotes = quotes

    async def ingest(
        self, *, tipster: str, text: str, mentioned_at: datetime | None = None
    ) -> IngestResult:
        when = mentioned_at or datetime.now(UTC)
        parsed = await self._parser.parse(text=text)

        priced = 0
        unpriced: list[str] = []
        ingested: list[IngestedTip] = []
        price_cache: dict[str, Decimal | None] = {}

        for tip in parsed:
            if tip.ticker not in price_cache:
                price_cache[tip.ticker] = await self._mention_price(tip.ticker, when)
            mention_price = price_cache[tip.ticker]
            if mention_price is None:
                unpriced.append(tip.ticker)
            else:
                priced += 1
            await self._repo.add(
                tipster=tipster,
                ticker=tip.ticker,
                category=tip.category.value,
                action=tip.action.value,
                conviction=tip.conviction.value,
                note=tip.note,
                raw_message=text,
                mentioned_at=when,
                mention_price=mention_price,
            )
            ingested.append(
                IngestedTip(
                    ticker=tip.ticker,
                    category=tip.category.value,
                    action=tip.action.value,
                    conviction=tip.conviction.value,
                    mention_price=mention_price,
                )
            )

        log.info("tips.ingested", tipster=tipster, parsed=len(parsed), priced=priced)
        return IngestResult(
            tipster=tipster,
            parsed=len(parsed),
            priced=priced,
            unpriced_tickers=tuple(dict.fromkeys(unpriced)),
            tips=tuple(ingested),
        )

    async def _mention_price(self, ticker: str, when: datetime) -> Decimal | None:
        try:
            closes = await self._quotes.daily_closes(
                ticker=ticker,
                start=when - timedelta(days=8),
                end=when + timedelta(days=2),
            )
        except StockQuoteError:
            return None
        return _close_asof(closes, when)
