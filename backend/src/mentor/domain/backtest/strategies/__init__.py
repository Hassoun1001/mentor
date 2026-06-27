"""Bundled strategies — the baseline and a couple of teaching examples."""

from mentor.domain.backtest.strategies.buy_and_hold import BuyAndHold
from mentor.domain.backtest.strategies.ma_crossover import MaCrossover
from mentor.domain.backtest.strategies.registry import (
    STRATEGY_REGISTRY,
    build_strategy,
)

__all__ = ["STRATEGY_REGISTRY", "BuyAndHold", "MaCrossover", "build_strategy"]
