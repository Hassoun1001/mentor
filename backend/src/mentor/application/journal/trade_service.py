"""Trade use cases — plan, open, close, cancel.

Use cases orchestrate the domain and the repository; they never contain
business logic themselves. If you find yourself adding math here, it
belongs in `domain/journal/trade.py` instead.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from mentor.domain.errors import ValidationError
from mentor.domain.instruments import Instrument, get_instrument
from mentor.domain.journal import compute_analytics
from mentor.domain.journal.analytics import JournalAnalytics
from mentor.domain.journal.trade import (
    Trade,
    TradePlan,
    cancel_trade,
    close_trade,
    open_trade,
    plan_trade,
)
from mentor.infrastructure.repositories.trades import TradeRepository


class TradeService:
    def __init__(self, repo: TradeRepository) -> None:
        self._repo = repo

    async def plan(self, plan: TradePlan) -> Trade:
        trade = plan_trade(plan)
        return await self._repo.add(trade)

    async def open(
        self,
        trade_id: uuid.UUID,
        *,
        fill_price: Decimal,
        at: datetime | None = None,
    ) -> Trade:
        current = await self._repo.get(trade_id)
        if current is None:
            raise ValidationError(f"trade {trade_id} not found", field="trade_id")
        return await self._repo.save(open_trade(current, fill_price=fill_price, at=at))

    async def cancel(self, trade_id: uuid.UUID) -> Trade:
        current = await self._repo.get(trade_id)
        if current is None:
            raise ValidationError(f"trade {trade_id} not found", field="trade_id")
        return await self._repo.save(cancel_trade(current))

    async def close(
        self,
        trade_id: uuid.UUID,
        *,
        exit_price: Decimal,
        instrument: Instrument | None = None,
        at: datetime | None = None,
        quote_to_account_rate: Decimal = Decimal("1"),
        mistake_tags: tuple[str, ...] = (),
        emotion: str | None = None,
        notes: str | None = None,
    ) -> Trade:
        current = await self._repo.get(trade_id)
        if current is None:
            raise ValidationError(f"trade {trade_id} not found", field="trade_id")
        instr = instrument or get_instrument(current.symbol)
        closed = close_trade(
            current,
            exit_price=exit_price,
            instrument=instr,
            at=at,
            quote_to_account_rate=quote_to_account_rate,
            mistake_tags=mistake_tags,
            emotion=emotion,
            notes=notes,
        )
        return await self._repo.save(closed)

    async def list_recent(self, *, symbol: str | None = None, limit: int = 100) -> list[Trade]:
        return list(await self._repo.list_recent(symbol=symbol, limit=limit))

    async def analytics(self, *, symbol: str | None = None) -> JournalAnalytics:
        trades = await self._repo.list_closed(symbol=symbol)
        return compute_analytics(trades)
