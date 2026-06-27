"""Manual price-bar backfill.

Usage:

    python -m mentor.cli.ingest --symbol EURUSD --timeframe 1h --days 30

The scheduler in Phase 5 will call the same `IngestionService.ingest`
under the hood; this CLI is intentionally tiny so backfills don't require
a running web server.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, datetime, timedelta

from mentor.application.market import IngestionService
from mentor.config import get_settings
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.adapters import TwelveDataAdapter
from mentor.infrastructure.db import build_engine, build_session_factory, session_scope
from mentor.infrastructure.repositories import PriceBarRepository
from mentor.logging import configure_logging, get_logger


async def _run(args: argparse.Namespace) -> None:
    settings = get_settings()
    configure_logging(settings)
    log = get_logger("mentor.cli.ingest")

    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    if not api_key:
        raise SystemExit("TWELVE_DATA_API_KEY must be set in the environment.")

    end = datetime.now(UTC)
    start = end - timedelta(days=args.days)
    timeframe = Timeframe(args.timeframe)

    engine = build_engine(settings)
    sessions = build_session_factory(engine)
    adapter = TwelveDataAdapter(api_key=api_key)

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
        await adapter.aclose()
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="Backfill OHLCV bars from Twelve Data.")
    p.add_argument("--symbol", required=True, help="e.g. EURUSD")
    p.add_argument(
        "--timeframe",
        default="1h",
        choices=[t.value for t in Timeframe],
    )
    p.add_argument("--days", type=int, default=30)
    args = p.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
