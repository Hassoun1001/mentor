"""Strategy lab from the command line — the same jobs the scheduler runs.

Usage (inside the app container):

    python -m mentor.cli.strategy_lab evaluate   # judge any candidate not yet evaluated
    python -m mentor.cli.strategy_lab paper      # advance paper trading over new bars
    python -m mentor.cli.strategy_lab status     # print where every idea stands

``evaluate`` is safe to repeat: a candidate is judged exactly once, so a
second run finds nothing to do. There is deliberately no ``--force``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime

from mentor.application.strategy_lab.evaluation import StrategyLabEvaluator
from mentor.application.strategy_lab.paper import PaperTrader
from mentor.application.strategy_lab.store import sql_bar_loader
from mentor.application.strategy_lab.summary import collect_lab_view
from mentor.config import get_settings
from mentor.infrastructure.db import build_engine, build_session_factory, session_scope
from mentor.infrastructure.repositories.strategy_lab import StrategyLabRepository
from mentor.logging import configure_logging


async def _run(command: str) -> str:
    settings = get_settings()
    configure_logging(settings)
    engine = build_engine(settings)
    sessions = build_session_factory(engine)
    symbol = settings.loop_symbol
    now = datetime.now(UTC)
    try:
        async with session_scope(sessions) as session:
            store = StrategyLabRepository(session)
            bars = sql_bar_loader(session, symbol)
            if command == "evaluate":
                evaluator = StrategyLabEvaluator(store=store, load_bars=bars, symbol=symbol)
                return (await evaluator.evaluate_pending(now=now)).summary
            if command == "paper":
                updates = await PaperTrader(store=store, load_bars=bars, symbol=symbol).advance(
                    now=now
                )
                return "\n".join(
                    f"{u.key}: {u.bars} new bar(s); " + "; ".join(u.log) for u in updates
                ) or "no strategy is paper trading"
            view = await collect_lab_view(store, now=now)
            return json.dumps(view.to_dict(), indent=1, default=str)
    finally:
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="Strategy lab: evaluate, paper-trade, report.")
    p.add_argument("command", choices=["evaluate", "paper", "status"])
    args = p.parse_args()
    print(asyncio.run(_run(args.command)))


if __name__ == "__main__":
    main()
