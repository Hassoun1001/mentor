"""Failover market-data adapter.

> Multiple sources of data is mandatory.

Wraps an ordered list of adapters and serves bars from the first one that
succeeds. A source "fails" if it raises or yields zero bars (down,
rate-limited, or no coverage for that symbol/timeframe). This buys
redundancy without the rest of the system knowing or caring which
provider answered — it still talks to the one `MarketDataAdapter`
contract.

Bars are buffered (not streamed straight through) so that a source which
starts yielding and then dies mid-stream doesn't leave a half-written
window: we only commit to a source once it has produced at least one bar
cleanly, and we fall through on any exception before that.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from datetime import datetime

from mentor.domain.errors import DomainError
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import PriceBar, Timeframe
from mentor.logging import get_logger

log = get_logger("mentor.adapters.failover")


class AllSourcesFailedError(DomainError):
    """Every configured source failed to return bars."""


class FailoverMarketDataAdapter(MarketDataAdapter):
    name = "failover"

    def __init__(self, adapters: Sequence[MarketDataAdapter]) -> None:
        if not adapters:
            raise ValueError("FailoverMarketDataAdapter needs at least one source")
        self._adapters = list(adapters)

    @property
    def last_source(self) -> str | None:
        return self._last_source

    _last_source: str | None = None

    async def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> AsyncIterator[PriceBar]:
        errors: list[str] = []
        for adapter in self._adapters:
            try:
                buffer = [
                    bar
                    async for bar in adapter.fetch_bars(
                        symbol=symbol, timeframe=timeframe, start=start, end=end
                    )
                ]
            except DomainError as exc:
                errors.append(f"{adapter.name}: {exc}")
                log.warning("failover.source_failed", source=adapter.name, error=str(exc))
                continue
            except Exception as exc:  # network/parse — try the next source
                errors.append(f"{adapter.name}: {exc!r}")
                log.warning("failover.source_error", source=adapter.name, error=repr(exc))
                continue

            if buffer:
                self._last_source = adapter.name
                log.info("failover.using", source=adapter.name, bars=len(buffer))
                for bar in buffer:
                    yield bar
                return
            errors.append(f"{adapter.name}: returned 0 bars")
            log.info("failover.empty", source=adapter.name)

        raise AllSourcesFailedError("all market-data sources failed: " + "; ".join(errors))
