"""Repair bars stored before their period closed — plan, apply, revert.

Usage (inside the app container):

    python -m mentor.cli.repair_bars plan                     # read-only report
    python -m mentor.cli.repair_bars apply --confirm          # correct + remove misaligned
    python -m mentor.cli.repair_bars apply --confirm --remove-unmatched
    python -m mentor.cli.repair_bars revert --batch repair:1h:20261013T180000Z

``plan`` writes nothing. ``apply`` prints one batch id per timeframe; every
change in it is logged to ``price_bar_revisions`` with the values it
replaced, and ``revert`` with that id restores them. Predictions and graded
outcomes are never touched. See ``mentor/application/market/repair.py``.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from mentor.application.market.repair import BarRepairService
from mentor.config import get_settings
from mentor.domain.instruments import get_instrument
from mentor.domain.market.bars import Timeframe
from mentor.infrastructure.adapters import FailoverMarketDataAdapter
from mentor.infrastructure.adapters.factory import build_sources, close_sources
from mentor.infrastructure.db import build_engine, build_session_factory, session_scope
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import configure_logging

_TIMEFRAMES = (Timeframe.H1, Timeframe.D1)


async def _run(args: argparse.Namespace) -> str:
    settings = get_settings()
    configure_logging(settings)
    symbol = settings.loop_symbol
    pip = get_instrument(symbol).pip_size
    engine = build_engine(settings)
    sessions = build_session_factory(engine)
    sources = build_sources(settings)
    adapter = FailoverMarketDataAdapter(sources)
    now = datetime.now(UTC)
    out: list[str] = []
    try:
        if args.command == "revert":
            async with session_scope(sessions) as session:
                service = BarRepairService(
                    adapter=adapter, repo=PriceBarRepository(session), pip=pip
                )
                restored, skipped = await service.revert(batch_id=args.batch, now=now)
            return f"{args.batch}: restored {restored} row(s); {skipped} skipped (changed since)"

        for tf in _TIMEFRAMES:
            # One transaction per timeframe: a failure leaves the other intact.
            async with session_scope(sessions) as session:
                service = BarRepairService(
                    adapter=adapter, repo=PriceBarRepository(session), pip=pip
                )
                plan = await service.plan(symbol=symbol, timeframe=tf, now=now)
                out.append(plan.describe())
                if args.command == "apply":
                    done = await service.apply(
                        plan, now=now, remove_unmatched=args.remove_unmatched
                    )
                    out.append(
                        f"  APPLIED batch {done.batch_id}: corrected {done.corrected}, "
                        f"removed {done.removed_misaligned} misaligned and "
                        f"{done.removed_unmatched} unmatched"
                    )
        return "\n".join(out)
    finally:
        await close_sources(sources)
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="Repair bars stored before their period closed.")
    p.add_argument("command", choices=["plan", "apply", "revert"])
    p.add_argument("--confirm", action="store_true", help="required for apply")
    p.add_argument(
        "--remove-unmatched",
        action="store_true",
        help="also remove provisional rows no settled bar matches",
    )
    p.add_argument("--batch", help="batch id to revert")
    args = p.parse_args()
    if args.command == "apply" and not args.confirm:
        p.error("apply changes stored prices; run plan first, then pass --confirm")
    if args.command == "revert" and not args.batch:
        p.error("revert needs --batch")
    print(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
