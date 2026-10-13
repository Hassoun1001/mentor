"""The starter library of entry-rule families.

Each family is one well-known, distinct idea, in one small module. A new
family is a new module here plus a ``CandidateDefinition`` in
``library.py``; nothing else changes, and the gate decides whether it ever
trades.
"""

from mentor.domain.strategy_lab.rules.donchian import DonchianBreakout
from mentor.domain.strategy_lab.rules.ma_cross import MaCrossTrend
from mentor.domain.strategy_lab.rules.momentum import TimeSeriesMomentum
from mentor.domain.strategy_lab.rules.narrow_range import NarrowRangeBreakout
from mentor.domain.strategy_lab.rules.pullback import TrendPullback
from mentor.domain.strategy_lab.rules.range_reversion import RangeReversion
from mentor.domain.strategy_lab.rules.session_breakout import SessionBreakout
from mentor.domain.strategy_lab.rules.squeeze import SqueezeBreakout

__all__ = [
    "DonchianBreakout",
    "MaCrossTrend",
    "NarrowRangeBreakout",
    "RangeReversion",
    "SessionBreakout",
    "SqueezeBreakout",
    "TimeSeriesMomentum",
    "TrendPullback",
]
