""""Follow him" backtest — pull prices, size by risk, build the equity curve."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from mentor.domain.tips.backtest import (
    FollowBacktestResult,
    TipEntry,
    run_follow_backtest,
)
from mentor.domain.tips.tip import TipAction
from mentor.infrastructure.adapters.stock_quotes import (
    DailyClose,
    StockQuoteClient,
    StockQuoteError,
)
from mentor.infrastructure.models import StockTipORM
from mentor.infrastructure.repositories.stock_tips import StockTipRepository
from mentor.logging import get_logger

log = get_logger("mentor.tips.backtest")

# Only calls that imply actually taking a long position are "followed".
_ACTIONABLE = {TipAction.BUY.value, TipAction.BUY_ON_DIP.value}


class TipBacktestService:
    def __init__(self, *, repo: StockTipRepository, quotes: StockQuoteClient) -> None:
        self._repo = repo
        self._quotes = quotes

    async def backtest(
        self,
        *,
        tipster: str,
        starting_equity: Decimal = Decimal("10000"),
        risk_pct: Decimal = Decimal("0.01"),
        stop_pct: Decimal = Decimal("0.10"),
        apply_stop: bool = True,
    ) -> FollowBacktestResult:
        tips = await self._repo.list_all(tipster=tipster)
        actionable = [
            t
            for t in tips
            if t.mention_price is not None and t.action in _ACTIONABLE
        ]
        if not actionable:
            return run_follow_backtest(
                tipster=tipster,
                entries=[],
                starting_equity=starting_equity,
                risk_pct=risk_pct,
                stop_pct=stop_pct,
                apply_stop=apply_stop,
            )

        now = datetime.now(UTC)
        earliest = min(t.mentioned_at for t in actionable)
        entries: list[TipEntry] = []
        for ticker in dict.fromkeys(t.ticker for t in actionable):
            try:
                closes = await self._quotes.daily_closes(
                    ticker=ticker, start=earliest - timedelta(days=3), end=now + timedelta(days=1)
                )
            except StockQuoteError:
                continue
            for t in (x for x in actionable if x.ticker == ticker):
                entry = _entry_for(t, closes, now)
                if entry is not None:
                    entries.append(entry)

        result = run_follow_backtest(
            tipster=tipster,
            entries=entries,
            starting_equity=starting_equity,
            risk_pct=risk_pct,
            stop_pct=stop_pct,
            apply_stop=apply_stop,
        )
        log.info("tips.backtest", tipster=tipster, trades=result.n_trades)
        return result


def _entry_for(tip: StockTipORM, closes: list[DailyClose], now: datetime) -> TipEntry | None:
    mention_price = tip.mention_price
    if mention_price is None:
        return None
    since = [c for c in closes if c.day >= tip.mentioned_at]
    window = since or list(closes)
    if not window:
        return None
    prices = [c.close for c in window]
    return TipEntry(
        ticker=tip.ticker,
        mentioned_at=tip.mentioned_at,
        entry_price=Decimal(mention_price),
        exit_price=window[-1].close,
        min_since=min(prices),
        days_held=max(0, (now - tip.mentioned_at).days),
    )
