"""Manual price-bar backfill.

Usage:

    python -m mentor.cli.ingest --symbol EURUSD --timeframe 1h --days 30
    python -m mentor.cli.ingest --symbol EURUSD --timeframe 1d --days 3650 --source yahoo

`--source` picks a single provider (`twelve_data`, `yahoo`) or `failover`
(default) which tries each configured source until one returns bars. The
scheduler calls the same `IngestionService.ingest` under the hood; this
CLI is intentionally tiny so backfills don't require a running web server.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime, timedelta

from mentor.application.market import IngestionService
from mentor.config import get_settings
from mentor.domain.market.adapter import MarketDataAdapter
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.adapters import FailoverMarketDataAdapter
from mentor.infrastructure.adapters.factory import build_adapter, build_sources, close_sources
from mentor.infrastructure.db import build_engine, build_session_factory, session_scope
from mentor.infrastructure.repositories import PriceBarRepository
from mentor.logging import configure_logging, get_logger


async def _run(args: argparse.Namespace) -> None:
    settings = get_settings()
    configure_logging(settings)
    log = get_logger("mentor.cli.ingest")

    end = datetime.now(UTC)
    start = end - timedelta(days=args.days)
    timeframe = Timeframe(args.timeframe)

    # Resolve the source(s). For failover we keep the full list so we can
    # close every underlying client afterwards.
    if args.source == "failover":
        sources = build_sources(settings)
        adapter: MarketDataAdapter = FailoverMarketDataAdapter(sources)
        to_close = sources
    else:
        one = build_adapter(args.source, settings)
        if one is None:
            raise SystemExit(
                f"source '{args.source}' is not configured "
                f"(twelve_data needs TWELVE_DATA_API_KEY)."
            )
        adapter = one
        to_close = [one]

    engine = build_engine(settings)
    sessions = build_session_factory(engine)

    try:
        async with session_scope(sessions) as session:
            service = IngestionService(adapter=adapter, repo=PriceBarRepository(session))
            result = await service.ingest(
                symbol=args.symbol.upper(),
                timeframe=timeframe,
                start=start,
                end=end,
            )
        log.info(
            "cli.done",
            symbol=result.symbol,
            timeframe=result.timeframe.value,
            fetched=result.fetched,
            persisted=result.persisted,
        )
    finally:
        await close_sources(to_close)
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="Backfill OHLCV bars from a market-data source.")
    p.add_argument("--symbol", required=True, help="e.g. EURUSD")
    p.add_argument(
        "--timeframe",
        default="1h",
        choices=[t.value for t in Timeframe],
    )
    p.add_argument("--days", type=int, default=30)
    p.add_argument(
        "--source",
        default="failover",
        choices=["failover", "twelve_data", "yahoo"],
        help="which provider to pull from (default: failover)",
    )
    args = p.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
