"""The candidate library: every trading idea the lab has been asked to test.

A ``CandidateDefinition`` is one idea — one rule family on one timeframe,
with its reason for existing and a small grid of parameter sets. The lab
treats the definition, not any single parameter set, as the thing under
test: walk-forward chooses the parameters from earlier data, the later
data grades the choice, and every parameter set in the grid is recorded
as a trial whether it is ever chosen or not.

**Adding a candidate** (what the maintenance agent does at most once a
week): write the rule family in ``rules/`` if it is new, append one
definition below with a new ``key``, and push. The lab evaluates it once,
on its own, and its verdict is final. Rules for keys:

- Keys are permanent. Never edit a definition that has been evaluated —
  the lab notices (the fingerprint changes), refuses to re-test it, and
  reports ``strategies.definition_changed``. A revised idea is a new key
  (``…_v2``), and its trials count against the bar like everyone else's.
- Keep grids small. Every parameter set is a trial, and every trial raises
  the bar for every candidate that comes after it.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import product
from typing import Final

from mentor.domain.errors import ValidationError
from mentor.domain.market.bars import Timeframe
from mentor.domain.strategy_lab.rules import (
    DonchianBreakout,
    MaCrossTrend,
    NarrowRangeBreakout,
    RangeReversion,
    SessionBreakout,
    SqueezeBreakout,
    TimeSeriesMomentum,
    TrendPullback,
)
from mentor.domain.strategy_lab.spec import EntryRule, ExitRules, ParamValue, StrategySpec

# Bounds the CPU of one evaluation and, more importantly, the temptation to
# search: a bigger grid is a bigger search, and the bar rises with it.
MAX_GRID_SIZE: Final = 24
SUPPORTED_TIMEFRAMES: Final = (Timeframe.H1, Timeframe.D1)

_KEY = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


def params_fingerprint(params: dict[str, ParamValue]) -> str:
    blob = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


@dataclass(frozen=True, slots=True)
class CandidateDefinition:
    key: str
    title: str
    timeframe: Timeframe
    hypothesis: str
    grid: tuple[tuple[EntryRule, ExitRules], ...]
    added: date
    added_by: str = "starter library"
    risk_fraction: Decimal = Decimal("0.01")

    def __post_init__(self) -> None:
        if not _KEY.match(self.key):
            raise ValidationError(f"bad candidate key {self.key!r}", field="key")
        if self.timeframe not in SUPPORTED_TIMEFRAMES:
            raise ValidationError(f"unsupported timeframe {self.timeframe}", field="timeframe")
        if not 1 <= len(self.grid) <= MAX_GRID_SIZE:
            raise ValidationError(f"grid must hold 1..{MAX_GRID_SIZE} sets", field="grid")
        families = {rule.family for rule, _ in self.grid}
        if len(families) != 1:
            raise ValidationError("a candidate tests one rule family", field="grid")
        prints = [params_fingerprint(spec.params()) for spec in self.specs()]
        if len(set(prints)) != len(prints):
            raise ValidationError("grid has duplicate parameter sets", field="grid")

    @property
    def family(self) -> str:
        return self.grid[0][0].family

    def specs(self) -> list[StrategySpec]:
        return [
            StrategySpec(
                rule=rule,
                exits=exits,
                timeframe=self.timeframe,
                hypothesis=self.hypothesis,
                risk_fraction=self.risk_fraction,
            )
            for rule, exits in self.grid
        ]

    def config_key(self, spec: StrategySpec) -> str:
        """Ledger identity of one parameter set of this candidate."""
        return f"{self.key}|{params_fingerprint(spec.params())}"

    def fingerprint(self) -> str:
        """Changes whenever anything that affects results changes."""
        blob = json.dumps(
            {
                "key": self.key,
                "family": self.family,
                "timeframe": self.timeframe.value,
                "risk_fraction": str(self.risk_fraction),
                "grid": [spec.params() for spec in self.specs()],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _grid(
    rules: Sequence[EntryRule], exits: Sequence[ExitRules]
) -> tuple[tuple[EntryRule, ExitRules], ...]:
    return tuple(product(rules, exits))


_STARTED = date(2026, 10, 13)

CANDIDATES: Final[tuple[CandidateDefinition, ...]] = (
    CandidateDefinition(
        key="donchian_breakout_d1",
        title="Channel breakout (turtle style)",
        timeframe=Timeframe.D1,
        hypothesis=(
            "Currencies are moved by slow forces — interest-rate gaps and central-bank "
            "cycles. When price finally escapes a range it has held for months, traders "
            "who bet against the move are forced to give up, which can carry it further."
        ),
        grid=_grid(
            [DonchianBreakout(channel=c) for c in (20, 55, 100)],
            [
                ExitRules(stop_atr=s, target_r=t, max_bars=60)
                for s, t in product((2.0, 3.0), (None, 3.0))
            ],
        ),
        added=_STARTED,
    ),
    CandidateDefinition(
        key="time_series_momentum_d1",
        title="Time-series momentum",
        timeframe=Timeframe.D1,
        hypothesis=(
            "Across many markets, what has risen over the last few months has tended to "
            "keep rising for a while (Moskowitz, Ooi & Pedersen, 2012). News sinks in "
            "slowly and policy cycles last, so a currency's recent direction may persist."
        ),
        grid=_grid(
            [TimeSeriesMomentum(period=p) for p in (63, 126, 252)],
            [
                ExitRules(stop_atr=s, target_r=None, max_bars=m)
                for s, m in product((3.0, 5.0), (21, 63))
            ],
        ),
        added=_STARTED,
    ),
    CandidateDefinition(
        key="trend_pullback_d1",
        title="Buy the dip in a trend",
        timeframe=Timeframe.D1,
        hypothesis=(
            "Inside an established trend, a sharp few-day move against it is often just "
            "profit-taking. Entering on that dip gets a better price than chasing, and the "
            "trend is the reason to expect a recovery."
        ),
        grid=_grid(
            [
                TrendPullback(trend=t, rsi_period=p, rsi_entry=e)
                for t, (p, e) in product((100, 200), ((2, 10.0), (5, 25.0)))
            ],
            [ExitRules(stop_atr=2.0, target_r=t, max_bars=10) for t in (1.0, 2.0)],
        ),
        added=_STARTED,
    ),
    CandidateDefinition(
        key="squeeze_breakout_d1",
        title="Volatility squeeze breakout",
        timeframe=Timeframe.D1,
        hypothesis=(
            "Quiet markets do not stay quiet: volatility comes in clusters and returns to "
            "its average. The first decisive break out of an unusually calm spell may be "
            "the start of the next active one."
        ),
        grid=_grid(
            [SqueezeBreakout(band=20, width=2.0, quiet=q) for q in (60, 120)],
            [
                ExitRules(stop_atr=s, target_r=t, max_bars=30)
                for s, t in product((1.5, 2.5), (2.0, None))
            ],
        ),
        added=_STARTED,
    ),
    CandidateDefinition(
        key="narrow_range_breakout_d1",
        title="Narrow-range breakout (NR4 / NR7)",
        timeframe=Timeframe.D1,
        hypothesis=(
            "The quietest day of the last week marks a market coiled between buyers and "
            "sellers (Crabel's narrow-range days). Whichever side wins the next day may "
            "keep winning for a few days."
        ),
        grid=_grid(
            [NarrowRangeBreakout(narrow=n) for n in (4, 7)],
            [
                ExitRules(stop_atr=2.0, target_r=t, max_bars=m)
                for t, m in product((1.0, 2.0, None), (5, 10))
            ],
        ),
        added=_STARTED,
    ),
    CandidateDefinition(
        key="ma_cross_trend_d1",
        title="Moving-average crossover with a trend filter",
        timeframe=Timeframe.D1,
        hypothesis=(
            "The textbook trend signal loses money in choppy months by flipping back and "
            "forth. Acting only when the market is travelling in a fairly straight line "
            "might keep the trends and skip the whipsaws."
        ),
        grid=_grid(
            [
                MaCrossTrend(fast=f, slow=s, er_period=20, er_min=e)
                for (f, s), e in product(((10, 50), (20, 100), (50, 200)), (0.0, 0.3))
            ],
            [ExitRules(stop_atr=3.0, target_r=None, max_bars=60)],
        ),
        added=_STARTED,
    ),
    CandidateDefinition(
        key="range_reversion_h1",
        title="Range fade (hourly)",
        timeframe=Timeframe.H1,
        hypothesis=(
            "When EUR/USD is going nowhere, banks and range traders lean against the edges "
            "of the range, so stretches far from the average tend to snap back. A trend "
            "filter keeps it from fading a genuine breakout."
        ),
        grid=_grid(
            [
                RangeReversion(band=b, width=w, er_period=24, er_max=e)
                for b, w, e in product((24, 48), (2.0, 2.5), (0.2, 0.3))
            ],
            [ExitRules(stop_atr=2.0, target_r=None, max_bars=24)],
        ),
        added=_STARTED,
    ),
    CandidateDefinition(
        key="session_breakout_h1",
        title="London-open breakout (hourly)",
        timeframe=Timeframe.H1,
        hypothesis=(
            "EUR/USD is quiet overnight in Asia; London's open brings the day's first real "
            "order flow. A break of the overnight range in London's first hours may set "
            "the direction for the rest of the morning."
        ),
        grid=_grid(
            [
                SessionBreakout(range_end_hour=r, session_end_hour=e)
                for r, e in product((6, 7), (10, 12))
            ],
            [ExitRules(stop_atr=1.0, target_r=t, max_bars=8) for t in (1.0, 2.0)],
        ),
        added=_STARTED,
    ),
)


def validate_library(candidates: Sequence[CandidateDefinition]) -> None:
    keys = [c.key for c in candidates]
    if len(set(keys)) != len(keys):
        raise ValidationError("candidate keys must be unique", field="key")


validate_library(CANDIDATES)


def find_candidate(key: str) -> CandidateDefinition | None:
    return next((c for c in CANDIDATES if c.key == key), None)
