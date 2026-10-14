"""Re-grade resolved calls on their own finished horizon bars — plan, apply, revert.

Usage (inside the app container):

    python -m mentor.cli.regrade_predictions plan                 # read-only report
    python -m mentor.cli.regrade_predictions apply --confirm
    python -m mentor.cli.regrade_predictions revert --batch regrade:20261014T060000Z

Only ``realised_close`` and ``realised_outcome`` change; every change is
logged to ``prediction_regrades`` with the values it replaced. See
``mentor/application/forecasting/regrade.py``.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

from mentor.application.forecasting.regrade import PredictionRegradeService
from mentor.config import get_settings
from mentor.infrastructure.db import build_engine, build_session_factory, session_scope
from mentor.infrastructure.repositories.predictions import PredictionRepository
from mentor.infrastructure.repositories.price_bars import PriceBarRepository
from mentor.logging import configure_logging


async def _run(args: argparse.Namespace) -> str:
    settings = get_settings()
    configure_logging(settings)
    engine = build_engine(settings)
    sessions = build_session_factory(engine)
    now = datetime.now(UTC)
    try:
        async with session_scope(sessions) as session:
            service = PredictionRegradeService(
                predictions=PredictionRepository(session),
                prices=PriceBarRepository(session),
            )
            if args.command == "revert":
                restored, skipped = await service.revert(batch_id=args.batch, now=now)
                return f"{args.batch}: restored {restored}; {skipped} skipped (changed since)"
            plan = await service.plan(now=now)
            out = [plan.describe()]
            if args.command == "apply":
                done = await service.apply(plan, now=now)
                out.append(f"APPLIED batch {done.batch_id}: {done.changed} call(s) re-graded")
            return "\n".join(out)
    finally:
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="Re-grade resolved calls on their own finished bars.")
    p.add_argument("command", choices=["plan", "apply", "revert"])
    p.add_argument("--confirm", action="store_true", help="required for apply")
    p.add_argument("--batch", help="batch id to revert")
    args = p.parse_args()
    if args.command == "apply" and not args.confirm:
        p.error("apply changes the graded track record; run plan first, then pass --confirm")
    if args.command == "revert" and not args.batch:
        p.error("revert needs --batch")
    print(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
