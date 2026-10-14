"""Retrain a lane now — the scheduler's own retrain path, from the command line.

Usage (inside the app container; about an hour of CPU per lane, so detach):

    python -m mentor.cli.retrain h1
    python -m mentor.cli.retrain d1

Runs exactly what the weekly slot runs (``LoopScheduler._retrain_lane``):
challengers are trained, the champion is re-graded on the same fresh window,
the promotion gates decide, and live recalibration re-decides afterwards.
Nothing is forced. If the scheduler is already retraining that lane, this
stands aside rather than racing it on the model store.
"""

from __future__ import annotations

import argparse
import asyncio

from mentor.application.scheduler.service import LoopScheduler
from mentor.config import get_settings
from mentor.infrastructure.db import build_engine, build_session_factory
from mentor.logging import configure_logging


async def _run(lane: str) -> str:
    settings = get_settings()
    configure_logging(settings)
    engine = build_engine(settings)
    try:
        scheduler = LoopScheduler(settings=settings, session_factory=build_session_factory(engine))
        if lane == "d1":
            return await scheduler.run_retrain_d1_once()
        return await scheduler.run_retrain_once()
    finally:
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="Retrain one lane through the promotion gates.")
    p.add_argument("lane", choices=["h1", "d1"])
    args = p.parse_args()
    print(asyncio.run(_run(args.lane)))


if __name__ == "__main__":
    main()
